from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import joblib
import glob
import os
import pandas as pd
import json
from prediction_engine import predict_with_ensemble, predict_with_simple_ensemble
from utils import get_logger
from web_scraper import get_current_commodity_price, get_price_scraper
from mistral_client import mistral_predictor
import re

app = FastAPI(
    title="MarketWave API Adapter",
    description="Lightweight HTTP adapter exposing prediction and explainability endpoints for the MarketWave CLI library.",
    version="0.1",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = os.path.dirname(__file__)
MODELS_DIR = os.path.join(ROOT, "models")
DATASET_DIR = os.path.join(ROOT, "dataset")

logger = get_logger("api_server")


class PredictRequest(BaseModel):
    market: str
    commodity: str
    horizon: int = 30
    force_simple: Optional[bool] = False


class PredictResponse(BaseModel):
    prediction_id: str
    yhat: List[Optional[float]]
    intervals: Dict[str, List[List[Optional[float]]]]
    base_preds: Dict[str, List[Optional[float]]]
    current_market_price: Optional[float] = None
    scraped_price_data: Optional[Dict[str, Any]] = None


@app.get("/welcome")
def welcome(request: Request):
    logger.info(f"Request received: {request.method} {request.url.path}")
    return {"message": "Welcome to the MarketWave API Service!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/markets")
def list_markets():
    # infer markets from models subdirectories
    try:
        markets = []
        if os.path.isdir(MODELS_DIR):
            for name in os.listdir(MODELS_DIR):
                p = os.path.join(MODELS_DIR, name)
                if os.path.isdir(p):
                    markets.append(name)
        return {"markets": markets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/markets/{market}/commodities")
def list_commodities(market: str):
    try:
        market_dir = os.path.join(MODELS_DIR, market)
        if not os.path.isdir(market_dir):
            raise HTTPException(status_code=404, detail="Market not found")
        # find ensemble files
        files = glob.glob(os.path.join(market_dir, "ensemble_*"))
        comms = []
        for f in files:
            base = os.path.basename(f)
            # expected pattern: ensemble_{Commodity}_{Market}.joblib
            parts = base.replace(".joblib", "").split("_")
            if len(parts) >= 2:
                comm = parts[1]
                comms.append(comm)
        comms = sorted(list(set(comms)))
        return {"commodities": comms}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _find_ensemble_path(market: str, commodity: str):
    market_dir = os.path.join(MODELS_DIR, market)
    if not os.path.isdir(market_dir):
        return None
    patt1 = os.path.join(market_dir, f"ensemble_{commodity}_*.joblib")
    patt2 = os.path.join(market_dir, f"ensemble_{commodity}.joblib")
    matches = glob.glob(patt1) + glob.glob(patt2)
    if not matches:
        # try case-insensitive search
        for f in os.listdir(market_dir):
            if f.lower().startswith("ensemble_") and commodity.lower() in f.lower():
                matches.append(os.path.join(market_dir, f))
    return matches[0] if matches else None


def _load_latest_sdf(market: str, commodity: str, seq_len: int = 90):
    """Attempt to load the latest dataframe (sdf) required by prediction_engine functions.
    Heuristics: search dataset/ for files containing commodity name and price, return last seq_len rows with a 'p_modal' column when possible."""
    try:
        # candidate files
        files = glob.glob(
            os.path.join(DATASET_DIR, f"*{commodity}*price*.csv"), recursive=False
        )
        files += glob.glob(
            os.path.join(DATASET_DIR, f"*{commodity}*.csv"), recursive=False
        )
        if not files:
            # fallback: any dataset file
            files = glob.glob(os.path.join(DATASET_DIR, "*.csv"))
        if not files:
            return None
        # pick most recent file (by modified time)
        files = sorted(files, key=os.path.getmtime, reverse=True)
        for f in files:
            try:
                df = pd.read_csv(f, parse_dates=True)
            except Exception:
                continue
            # try to detect price column
            cols = [c.lower() for c in df.columns]
            price_col = None
            for c in df.columns:
                if (
                    "price" in c.lower()
                    or "modal" in c.lower()
                    or "p_modal" in c.lower()
                ):
                    price_col = c
                    break
            if price_col is None:
                # try numeric columns
                numerics = df.select_dtypes(include=["number"]).columns
                if len(numerics) > 0:
                    price_col = numerics[0]
                else:
                    continue
            # rename to p_modal
            df = df.rename(columns={price_col: "p_modal"})
            # try to filter by market if market column exists
            market_cols = [c for c in df.columns if "market" in c.lower()]
            if market_cols:
                mc = market_cols[0]
                df = df[
                    df[mc].astype(str).str.lower().str.contains(str(market).lower())
                ]
                if df.empty:
                    continue
            # ensure datetime index
            date_cols = [
                c
                for c in df.columns
                if any(k in c.lower() for k in ("date", "ds", "t"))
            ]
            if date_cols:
                dcol = date_cols[0]
                try:
                    df[dcol] = pd.to_datetime(df[dcol], errors="coerce")
                    df = df.set_index(dcol).sort_index()
                except Exception:
                    pass
            # limit to seq_len
            if "p_modal" in df.columns:
                sdf = df[["p_modal"]].tail(seq_len)
                if not sdf.empty:
                    return sdf
        return None
    except Exception:
        return None


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    market = req.market
    commodity = req.commodity
    horizon = req.horizon or 30
    ensemble_path = _find_ensemble_path(market, commodity)
    if not ensemble_path:
        raise HTTPException(
            status_code=404,
            detail="Ensemble model not found for given market/commodity",
        )
    sdf = _load_latest_sdf(market, commodity)
    if sdf is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset found for commodity/market to build input features",
        )
    try:
        if req.force_simple:
            out = predict_with_simple_ensemble(ensemble_path, sdf, horizon=horizon)
        else:
            out = predict_with_ensemble(ensemble_path, sdf, horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # Fetch current market price using web scraper with Google search
    current_price = None
    scraped_data = None
    try:
        logger.info(
            f"Fetching current price for {commodity} in {market} using Google search"
        )
        price_data = get_current_commodity_price(commodity, market)
        current_price = price_data.get("current_price")
        scraped_data = price_data
        logger.info(f"Current price fetched via Google search: {current_price}")
    except Exception as e:
        logger.warning(f"Failed to fetch current price via Google search: {e}")

    # create a simple prediction id using filename and timestamp
    pid = (
        os.path.basename(ensemble_path) + "_" + str(int(pd.Timestamp.now().timestamp()))
    )
    resp = {
        "prediction_id": pid,
        "yhat": out.get("yhat", []),
        "intervals": out.get("intervals", {}),
        "base_preds": out.get("base_preds", {}),
        "current_market_price": current_price,
        "scraped_price_data": scraped_data,
    }
    return resp


@app.get("/predictions/{prediction_id}/explain")
def explain(prediction_id: str):
    """Best-effort explainability: try to find the ensemble from prediction_id and return feature importances.
    If the underlying model is XGBoost we return feature_importances_, otherwise we return model metadata and base_preds."""
    try:
        # extract ensemble filename from prediction_id prefix
        fname = prediction_id.split("_")[0]
        # find file in models dir
        candidates = glob.glob(os.path.join(MODELS_DIR, "**", fname), recursive=True)
        if not candidates:
            raise HTTPException(
                status_code=404, detail="Ensemble artifact not found for explanation"
            )
        ensemble_path = candidates[0]
        ensemble = joblib.load(ensemble_path)
        explain_payload = {"model_metadata": {}, "global_importance": [], "local": []}
        # attempt xgboost
        xgb_path = ensemble.get("xgb_path") or ensemble.get("xgb")
        if xgb_path and os.path.exists(xgb_path):
            try:
                from models.xgboost_wrapper import load_xgboost

                xgb = load_xgboost(xgb_path)
                # try sklearn-like feature importance
                if hasattr(xgb, "feature_importances_"):
                    fi = xgb.feature_importances_.tolist()
                    # create feature names heuristically
                    feature_names = getattr(xgb, "feature_names", None)
                    if not feature_names:
                        feature_names = [f"f{i}" for i in range(len(fi))]
                    explain_payload["global_importance"] = [
                        {"feature": n, "importance": float(v)}
                        for n, v in zip(feature_names, fi)
                    ]
                    explain_payload["model_metadata"] = {
                        "model_name": "xgboost",
                        "path": xgb_path,
                    }
                else:
                    explain_payload["model_metadata"] = {
                        "model_name": "xgboost",
                        "path": xgb_path,
                    }
            except Exception:
                pass
        else:
            # if no xgb, try to use meta models info
            explain_payload["model_metadata"] = {
                "ensemble": os.path.basename(ensemble_path)
            }
        return explain_payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current-prices/{commodity}")
def get_current_price(commodity: str, market: Optional[str] = None):
    """Get current market price for a commodity using Google search"""
    try:
        logger.info(
            f"Fetching current price for {commodity} in {market or 'any market'} using Google search"
        )
        price_data = get_current_commodity_price(commodity, market or "")
        return price_data
    except Exception as e:
        logger.error(f"Failed to fetch current price via Google search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch current price via Google search: {str(e)}",
        )


@app.get("/current-prices")
def get_multiple_current_prices(commodities: Optional[str] = None):
    """Get current market prices for multiple commodities using Google search"""
    try:
        if not commodities:
            # Default commodities
            commodity_list = ["tomato", "potato", "onion", "brinjal", "green_chilli"]
        else:
            commodity_list = [c.strip() for c in commodities.split(",")]

        scraper = get_price_scraper()
        results = scraper.get_multiple_commodities_prices(commodity_list)
        return {"prices": results}
    except Exception as e:
        logger.error(f"Failed to fetch current prices via Google search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch current prices via Google search: {str(e)}",
        )


@app.get("/historical-prices/{commodity}")
def get_historical_prices(commodity: str, market: Optional[str] = None):
    """Get historical price data for a commodity using web search and Gemini AI"""
    try:
        logger.info(
            f"Fetching historical prices for {commodity} in {market or 'any market'} using web search and Gemini AI"
        )
        from web_scraper import get_historical_commodity_prices

        result = get_historical_commodity_prices(commodity, market or "")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch historical prices: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch historical prices: {str(e)}"
        )


@app.get("/forecast-prices/{commodity}")
def get_forecast_prices(commodity: str, market: Optional[str] = None):
    """Get forecast price data for a commodity using web search and Gemini AI"""
    try:
        logger.info(
            f"Fetching forecast prices for {commodity} in {market or 'any market'} using web search and Gemini AI"
        )
        from web_scraper import get_forecast_commodity_prices

        result = get_forecast_commodity_prices(commodity, market or "")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch forecast prices: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch forecast prices: {str(e)}"
        )


@app.post("/predict-mistral", response_model=PredictResponse)
def predict_mistral(req: PredictRequest):
    """Predict commodity prices using Mistral AI agent"""
    try:
        logger.info(
            f"Mistral prediction request: {req.market} - {req.commodity} - horizon {req.horizon}"
        )

        # Use Mistral predictor
        result = mistral_predictor.predict(req.commodity, req.market, req.horizon)

        # Create prediction ID
        pid = f"mistral_{req.commodity}_{req.market}_{int(pd.Timestamp.now().timestamp())}"

        # Format response to match existing structure
        resp = {
            "prediction_id": pid,
            "yhat": result.get("yhat", []),
            "intervals": result.get("intervals", {}),
            "base_preds": result.get("base_preds", {}),
            "current_market_price": None,  # Mistral doesn't provide current price
            "scraped_price_data": None,
        }
        return resp

    except Exception as e:
        logger.error(f"Mistral prediction failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Mistral prediction failed: {str(e)}"
        )


@app.get("/price-comparison/{commodity}")
def get_price_comparison(commodity: str, expected_price: Optional[float] = None):
    """Get price comparison data across multiple markets for a commodity.
    Optional query param expected_price (float) — when provided, the endpoint
    will only include the top recommendation if expected_price < top_recommendation_price.
    """
    try:
        logger.info(
            f"Fetching price comparison for {commodity} (expected_price={expected_price})"
        )
        scraper = get_price_scraper()
        result = scraper.get_price_comparison(commodity)

        # Helper to parse a numeric price from various possible representations
        def _parse_price(val) -> Optional[float]:
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                # Try to extract first numeric token (handles "Bowenpally: ₹18.77/kg" etc.)
                m = re.search(r"([0-9]+(?:\.[0-9]+)?)", val.replace(",", ""))
                if m:
                    try:
                        return float(m.group(1))
                    except Exception:
                        return None
            # if it's a dict, try to look for common keys
            if isinstance(val, dict):
                for k in ("price", "price_per_kg", "value", "p", "cost"):
                    if k in val:
                        return _parse_price(val[k])
            return None

        # If result contains a top recommendation, enforce expected_price rule
        top = None
        if isinstance(result, dict):
            # try common keys
            top = (
                result.get("top_recommendation")
                or result.get("best")
                or result.get("recommendation")
            )
        # If top is a string like "Bowenpally: ₹18.77/kg", parse the number from it
        top_price = _parse_price(top)

        if expected_price is not None and top_price is not None:
            # show top recommendation only when expected_price < top_price
            if not (expected_price < top_price):
                # remove/hide top recommendation
                if isinstance(result, dict) and (
                    "top_recommendation" in result
                    or "best" in result
                    or "recommendation" in result
                ):
                    result.pop("top_recommendation", None)
                    result.pop("best", None)
                    result.pop("recommendation", None)
                    result["top_recommendation_hidden_reason"] = (
                        "Hidden because expected_price >= top_recommendation_price"
                    )

        return result
    except Exception as e:
        logger.error(f"Failed to fetch price comparison: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch price comparison: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
