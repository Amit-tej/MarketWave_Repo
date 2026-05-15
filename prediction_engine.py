import numpy as np
import pandas as pd
import os
import random
from utils import get_logger
import joblib
from models.xgboost_wrapper import load_xgboost, predict_xgboost

logger = get_logger("prediction_engine")

# Set deterministic seeds for reproducible predictions
np.random.seed(42)
random.seed(42)


def predict_with_simple_ensemble(ensemble_path, sdf_last, horizon=30):
    """Predict using simple stacked ensemble (RF + RF + Linear meta)"""
    ensemble = joblib.load(ensemble_path)

    # Check if this is a simple ensemble
    if "m1" in ensemble and "m2" in ensemble and "meta" in ensemble:
        # Prepare features
        feat_data = sdf_last.copy()
        if "p_modal" in feat_data.columns:
            feat_data = feat_data.drop(columns=["p_modal"])

        # Process features same way as training
        for col in feat_data.select_dtypes(include=["object", "category"]).columns:
            feat_data[col] = (
                feat_data[col].astype("category").cat.codes.replace(-1, np.nan)
            )

        feat_data = feat_data.fillna(feat_data.mean())

        for col in feat_data.columns:
            feat_data[col] = pd.to_numeric(feat_data[col], errors="coerce")

        feat_data = feat_data.fillna(0)

        # Get last row for prediction
        X_last = feat_data.tail(1)

        # Make predictions with base models
        pred1 = ensemble["m1"].predict(X_last)[0]
        pred2 = ensemble["m2"].predict(X_last)[0]

        # Meta prediction
        meta_input = np.array([[pred1, pred2]])
        final_pred = ensemble["meta"].predict(meta_input)[0]

        # For simplicity, repeat the prediction for all horizons
        # In practice, you'd want recursive prediction
        yhat = [final_pred] * horizon

        # Simple intervals (±20% of prediction)
        intervals = {
            "80": [(y * 0.8, y * 1.2) for y in yhat],
            "90": [(y * 0.75, y * 1.25) for y in yhat],
            "95": [(y * 0.7, y * 1.3) for y in yhat],
        }

        return {
            "yhat": yhat,
            "intervals": intervals,
            "base_preds": {"rf1": [pred1] * horizon, "rf2": [pred2] * horizon},
        }

    else:
        # Fall back to complex ensemble
        return predict_with_ensemble(ensemble_path, sdf_last, horizon)


def predict_with_ensemble(ensemble_path, sdf_last, horizon=30):
    """Load ensemble and produce multi-horizon forecasts with conformal intervals.
    sdf_last: DataFrame containing the last available rows (with date index), at least seq_len rows for LSTM.
    Returns: dict with 'yhat' list and intervals for 80/90/95
    """
    ensemble = joblib.load(ensemble_path)
    # load base models
    xgb_path = ensemble.get("xgb_path")
    p_path = ensemble.get("prophet_path")
    lstm_path = ensemble.get("lstm_path")
    meta_models = ensemble.get("meta_models") or {}
    conformal = ensemble.get("conformal", {})
    seq_len = ensemble.get("seq_len", 30)

    # XGBoost
    try:
        xgb_model = (
            load_xgboost(xgb_path) if xgb_path and xgb_path.endswith(".model") else None
        )
    except Exception:
        xgb_model = None

    # Prophet
    try:
        from models.prophet_wrapper import load_prophet, predict_prophet

        prophet_model = load_prophet(p_path) if p_path else None
    except Exception:
        prophet_model = None

    # LSTM
    try:
        from models.lstm_wrapper import build_lstm, load_lstm_weights

        lstm_model = None
        if lstm_path:
            # need to reconstruct model architecture
            lstm_model = build_lstm(input_shape=(seq_len, 1))
            load_lstm_weights(lstm_model, lstm_path)
            scaler = joblib.load(lstm_path + ".scaler")
        else:
            scaler = None
    except Exception:
        lstm_model = None
        scaler = None

    # generate base model forecasts
    xgb_preds = []
    prop_preds = []
    lstm_preds = []

    # prepare latest feature row for xgboost; drop target
    feat_row = sdf_last.copy()
    if "p_modal" in feat_row.columns:
        feat_row = feat_row.drop(columns=["p_modal"])
    xrow = feat_row.tail(1)

    last_val = (
        float(sdf_last["p_modal"].iloc[-1]) if "p_modal" in sdf_last.columns else None
    )

    # XGBoost recursive
    if xgb_model is not None:
        last = last_val if last_val is not None else 0
        xrow_local = xrow.copy()
        for k in range(horizon):
            if "p_modal" in xrow_local.columns:
                xrow_local["p_modal"] = last
            try:
                p = predict_xgboost(xgb_model, xrow_local)[0]
            except Exception:
                p = np.nan
            xgb_preds.append(p)
            last = p
    else:
        xgb_preds = [np.nan] * horizon

    # Prophet
    if prophet_model is not None:
        try:
            pfc = prophet_model.predict(
                prophet_model.make_future_dataframe(periods=horizon, freq="D")
            )
            prop_preds = pfc[["ds", "yhat"]].tail(horizon)["yhat"].values.tolist()
        except Exception:
            prop_preds = [np.nan] * horizon
    else:
        prop_preds = [np.nan] * horizon

    # LSTM iterative
    if lstm_model is not None and scaler is not None:
        seq = sdf_last["p_modal"].tail(seq_len).values
        if len(seq) < seq_len:
            seq = np.pad(seq, (seq_len - len(seq), 0), "edge")
        seq_s = scaler.transform(seq.reshape(-1, 1)).reshape(1, seq_len, 1)
        sseq = seq_s.copy()
        for k in range(horizon):
            try:
                p_s = float(lstm_model.predict(sseq)[0, 0])
                p_raw = scaler.inverse_transform([[p_s]])[0, 0]
            except Exception:
                p_raw = np.nan
            lstm_preds.append(p_raw)
            # append to seq
            if not np.isnan(p_s):
                new = np.append(sseq[0, 1:, 0], p_s)
                sseq = new.reshape(1, seq_len, 1)
    else:
        lstm_preds = [np.nan] * horizon

    # Meta predictions per horizon
    yhat = []
    for h in range(horizon):
        meta = meta_models.get(h + 1)
        if meta is None:
            # fallback average of available preds
            vals = [
                v
                for v in (
                    xgb_preds[h] if h < len(xgb_preds) else np.nan,
                    prop_preds[h] if h < len(prop_preds) else np.nan,
                    lstm_preds[h] if h < len(lstm_preds) else np.nan,
                )
                if not np.isnan(v)
            ]
            yhat.append(np.mean(vals) if vals else np.nan)
            continue
        fv = np.array(
            [
                [
                    xgb_preds[h]
                    if h < len(xgb_preds) and not np.isnan(xgb_preds[h])
                    else 0,
                    prop_preds[h]
                    if h < len(prop_preds) and not np.isnan(prop_preds[h])
                    else 0,
                    lstm_preds[h]
                    if h < len(lstm_preds) and not np.isnan(lstm_preds[h])
                    else 0,
                ]
            ]
        )
        yhat.append(float(meta.predict(fv)[0]))

    # intervals using conformal quantiles
    q80 = conformal.get("q80", 0.0)
    q90 = conformal.get("q90", 0.0)
    q95 = conformal.get("q95", 0.0)

    intervals = {
        "80": [(y - q80, y + q80) for y in yhat],
        "90": [(y - q90, y + q90) for y in yhat],
        "95": [(y - q95, y + q95) for y in yhat],
    }

    # If the ensemble produced only NaNs (or no valid predictions), fallback to the stats predictor
    def _all_nan(lst):
        if not lst:
            return True
        return all([v is None or (isinstance(v, float) and np.isnan(v)) for v in lst])

    # Log which base artifacts are present
    try:
        present = []
        if xgb_path and os.path.exists(xgb_path):
            present.append("xgboost")
        if p_path and os.path.exists(p_path):
            present.append("prophet")
        if lstm_path and os.path.exists(lstm_path):
            present.append("lstm")
        if not present:
            logger.warning(
                f"Ensemble loaded from {ensemble_path} but no base artifacts found: xgb={xgb_path}, prophet={p_path}, lstm={lstm_path}"
            )
        else:
            logger.info(f"Ensemble base artifacts available: {','.join(present)}")
    except Exception:
        pass

    if _all_nan(yhat):
        logger.warning(
            "Ensemble produced no valid numeric forecasts (all NaN). Falling back to historical stats predictor"
        )
        try:
            return fallback_stats_predict(sdf_last, horizon=horizon)
        except Exception:
            # final fallback: return NaNs with empty base_preds
            return {
                "yhat": [float("nan")] * horizon,
                "intervals": {"80": [(float("nan"), float("nan"))] * horizon},
                "base_preds": {},
            }

    return {
        "yhat": yhat,
        "intervals": intervals,
        "base_preds": {"xgb": xgb_preds, "prophet": prop_preds, "lstm": lstm_preds},
    }


def predict_with_blended_forecast(ensemble_path, sdf_last, horizon=30):
    """Blend ML ensemble predictions with web-based forecasts for improved accuracy.

    This function combines:
    1. ML model predictions from ensemble (XGBoost, Prophet, LSTM)
    2. Web-scraped forecasts from Google search + Gemini AI (DISABLED for stability)
    3. Statistical fallback when ML models fail

    Returns blended predictions with confidence weighting.
    """
    logger = get_logger("prediction_engine")

    # Get ML predictions
    try:
        ml_result = predict_with_ensemble(ensemble_path, sdf_last, horizon)
        ml_yhat = ml_result.get("yhat", [])
        ml_intervals = ml_result.get("intervals", {})
        ml_base_preds = ml_result.get("base_preds", {})
        ml_confidence = (
            1.0
            if ml_yhat
            and not all(
                np.isnan(v) if isinstance(v, (int, float)) else v is None
                for v in ml_yhat
            )
            else 0.0
        )
    except Exception as e:
        logger.warning(f"ML prediction failed: {e}, falling back to stats")
        ml_result = fallback_stats_predict(sdf_last, horizon)
        ml_yhat = ml_result.get("yhat", [])
        ml_intervals = ml_result.get("intervals", {})
        ml_base_preds = ml_result.get("base_preds", {})
        ml_confidence = 0.5  # Lower confidence for fallback

    # Web forecasts DISABLED for stable predictions
    # External web data introduces variability and non-determinism
    web_forecasts = [None] * horizon
    web_confidence = 0.0

    logger.info("Web forecasts disabled for stable predictions")

    # Blend predictions (only ML predictions used)
    blended_yhat = ml_yhat.copy()
    blended_intervals = ml_intervals.copy()
    blended_base_preds = ml_base_preds.copy()

    # Add web predictions to base_preds (all None)
    blended_base_preds["web_forecast"] = web_forecasts

    # Calculate overall confidence
    overall_confidence = ml_confidence

    logger.info(
        f"Blended forecast completed: ML confidence {ml_confidence:.2f}, Web confidence {web_confidence:.2f}, Overall {overall_confidence:.2f}"
    )

    return {
        "yhat": blended_yhat,
        "intervals": blended_intervals,
        "base_preds": blended_base_preds,
        "ml_confidence": ml_confidence,
        "web_confidence": web_confidence,
        "overall_confidence": overall_confidence,
    }


def fallback_stats_predict(sdf, horizon=30):
    """Improved fallback predictor:
    - Try statsmodels' ExponentialSmoothing when available (handles trend+seasonality).
    - Otherwise build simple time features + lags and train a Ridge model.
    - If a matching quantity dataset exists in dataset/, merge it as an exogenous feature.
    Returns the same dict shape as predict_with_ensemble.
    """
    import os
    import glob
    from sklearn.linear_model import Ridge

    # basic checks
    if "p_modal" not in sdf.columns or len(sdf.dropna(subset=["p_modal"])) == 0:
        return {
            "yhat": [float("nan")] * horizon,
            "intervals": {"80": [(None, None)] * horizon},
            "base_preds": {},
        }

    # ensure datetime index
    if not isinstance(sdf.index, pd.DatetimeIndex):
        try:
            sdf = sdf.copy()
            sdf.index = pd.to_datetime(sdf.index)
        except Exception:
            # fallback to mean
            vals = sdf["p_modal"].dropna()
            base = float(vals.mean()) if not vals.empty else 0.0
            return {
                "yhat": [base] * horizon,
                "intervals": {"80": [(None, None)] * horizon},
                "base_preds": {"historical_mean": [base] * horizon},
            }

    series = sdf["p_modal"].astype(float).dropna()
    if series.empty:
        return {
            "yhat": [float("nan")] * horizon,
            "intervals": {"80": [(None, None)] * horizon},
            "base_preds": {},
        }

    # Try ExponentialSmoothing if available
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        # Ensure the series has a proper datetime index with frequency
        train = series.copy()
        if not isinstance(train.index, pd.DatetimeIndex):
            train.index = pd.date_range(
                start="2024-01-01", periods=len(train), freq="D"
            )
        else:
            train.index = pd.date_range(
                start=train.index[0], end=train.index[-1], freq="D"
            )

        # Try SARIMAX first for better dynamic forecasts
        try:
            model_sarima = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
            fit_sarima = model_sarima.fit(disp=False)
            forecast_index = pd.date_range(
                start=train.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D"
            )
            yhat = fit_sarima.forecast(horizon, index=forecast_index).tolist()
            residuals = fit_sarima.resid.dropna()
            std = float(residuals.std()) if len(residuals) > 1 else float(train.std())

        except:
            # Fallback to ExponentialSmoothing if SARIMAX fails
            seasonal = 7 if len(train) >= 14 else None
            model = ExponentialSmoothing(
                train,
                seasonal_periods=seasonal,
                trend="add" if len(train) > 30 else None,
                seasonal="add" if seasonal else None,
                damped_trend=True,
            )  # Add damped trend for more realistic forecasts
            fit = model.fit(optimized=True)
            yhat = fit.forecast(horizon).tolist()
            residuals = (fit.fittedvalues - train).dropna()
            std = float(residuals.std()) if len(residuals) > 1 else float(train.std())

        # Remove random variation for stable predictions
        # Predictions should be deterministic for same input

        q80 = 1.28 * std
        q90 = 1.64 * std
        q95 = 1.96 * std
        intervals = {
            "80": [(y - q80, y + q80) for y in yhat],
            "90": [(y - q90, y + q90) for y in yhat],
            "95": [(y - q95, y + q95) for y in yhat],
        }
        return {"yhat": yhat, "intervals": intervals, "base_preds": {"hw_es": yhat}}
    except Exception:
        # statsmodels not available or failed -> fall back to feature-based regression
        pass

    # Build features for regression
    df_feat = pd.DataFrame({"y": series})
    df_feat["t"] = np.arange(len(df_feat))
    df_feat["dayofyear_s"] = np.sin(2 * np.pi * df_feat.index.dayofyear / 365.25)
    df_feat["dayofyear_c"] = np.cos(2 * np.pi * df_feat.index.dayofyear / 365.25)
    # lags and rolling
    for lag in (1, 7, 30):
        df_feat[f"lag_{lag}"] = df_feat["y"].shift(lag)
    df_feat["roll_7"] = df_feat["y"].rolling(7, min_periods=1).mean()
    df_feat["roll_30"] = df_feat["y"].rolling(30, min_periods=1).mean()

    # optional: try to load quantity data as exogenous
    try:
        ds_dir = os.path.join(os.path.dirname(__file__), "dataset")
        # dataset folder might be up one level; try workspace dataset/
        if not os.path.isdir(ds_dir):
            ds_dir = os.path.join(os.getcwd(), "dataset")
        qfiles = glob.glob(os.path.join(ds_dir, f"*{os.path.basename(ds_dir)}*"))
    except Exception:
        ds_dir = os.path.join(os.getcwd(), "dataset")

    # attempt to find a quantity file matching commodity name from sdf if present
    quantity_series = None
    try:
        # find commodity name from sdf if present
        commodity = None
        if "cmdty" in sdf.columns:
            commodity = str(sdf["cmdty"].dropna().iloc[0]).lower()
        # search dataset dir for file names containing commodity and 'quantity'
        if commodity:
            q_candidates = glob.glob(
                os.path.join(ds_dir, f"*{commodity}*quantity*.csv")
            ) + glob.glob(os.path.join(ds_dir, f"*{commodity}*quantity*.CSV"))
            if q_candidates:
                qf = q_candidates[0]
                qdf = pd.read_csv(qf, parse_dates=True)
                # try to find date column
                for c in ("date", "t", "ds"):
                    if c in qdf.columns:
                        qdf[c] = pd.to_datetime(qdf[c], errors="coerce")
                        qdf = qdf.set_index(c)
                        break
                # try to pick same market rows
                if "market_name" in qdf.columns and "market_name" in sdf.columns:
                    m = sdf["market_name"].dropna().iloc[-1]
                    qdf = qdf[
                        qdf["market_name"].str.lower().str.strip()
                        == str(m).lower().strip()
                    ]
                # pick quantity column heuristically
                qty_col = None
                for col in qdf.columns:
                    if (
                        "qty" in col.lower()
                        or "quantity" in col.lower()
                        or "q" == col.lower()
                    ):
                        qty_col = col
                        break
                if qty_col is None and len(qdf.columns) > 0:
                    qty_col = qdf.columns[0]
                if qty_col is not None:
                    quantity_series = qdf[qty_col].astype(float).rename("qty")
                    # align to main series
                    quantity_series = quantity_series.reindex(series.index)
                    quantity_series = quantity_series.ffill().bfill()
    except Exception:
        quantity_series = None

    if quantity_series is not None:
        df_feat["qty"] = quantity_series.values[: len(df_feat)]

    df_feat = df_feat.dropna()
    if len(df_feat) < 10:
        # not enough data for regression; fallback to mean
        base = (
            float(series.tail(30).mean()) if len(series) >= 1 else float(series.mean())
        )
        return {
            "yhat": [base] * horizon,
            "intervals": {"80": [(None, None)] * horizon},
            "base_preds": {"historical_mean": [base] * horizon},
        }

    X = df_feat.drop(columns=["y"])
    y = df_feat["y"]

    model = Ridge(alpha=1.0)
    try:
        model.fit(X, y)
    except Exception:
        # if fit fails, fallback to mean
        base = float(y.mean())
        return {
            "yhat": [base] * horizon,
            "intervals": {"80": [(None, None)] * horizon},
            "base_preds": {"historical_mean": [base] * horizon},
        }

    # recursive forecasting
    last_row = df_feat.iloc[-1:].copy()
    preds = []
    for step in range(horizon):
        # build next feature row
        next_t = last_row["t"].values[0] + 1
        next_index = last_row.index[0] + pd.Timedelta(days=1)
        next_row = {}
        next_row["t"] = next_t
        next_row["dayofyear_s"] = np.sin(2 * np.pi * next_index.dayofyear / 365.25)
        next_row["dayofyear_c"] = np.cos(2 * np.pi * next_index.dayofyear / 365.25)
        # lags: use previous predictions where needed
        for lag in (1, 7, 30):
            if lag == 1:
                val = last_row["y"].values[0]
            else:
                # approximate by recent roll
                val = (
                    last_row.get(f"lag_{lag}", last_row["y"]).values[0]
                    if f"lag_{lag}" in last_row.columns
                    else last_row["y"].values[0]
                )
            next_row[f"lag_{lag}"] = val
        next_row["roll_7"] = (
            last_row["y"].rolling(7, min_periods=1).mean().values[0]
            if "y" in last_row
            else last_row["roll_7"].values[0]
        )
        next_row["roll_30"] = (
            last_row["y"].rolling(30, min_periods=1).mean().values[0]
            if "y" in last_row
            else last_row["roll_30"].values[0]
        )
        if "qty" in last_row.columns:
            # keep qty same as last known (or NaN)
            next_row["qty"] = last_row["qty"].values[0]

        Xnext = pd.DataFrame([next_row], index=[next_index])
        # ensure column order
        Xnext = Xnext[X.columns]
        p = float(model.predict(Xnext)[0])
        preds.append(p)
        # append to last_row for next iteration
        new = pd.DataFrame([{"y": p, **next_row}], index=[next_index])
        last_row = pd.concat([last_row, new])
        last_row = last_row.iloc[-1:]

    # compute residuals on training set to derive quantile intervals
    train_pred = model.predict(X)
    resid = y.values - train_pred
    q80 = float(np.quantile(np.abs(resid), 0.8))
    q90 = float(np.quantile(np.abs(resid), 0.9))
    q95 = float(np.quantile(np.abs(resid), 0.95))
    intervals = {
        "80": [(v - q80, v + q80) for v in preds],
        "90": [(v - q90, v + q90) for v in preds],
        "95": [(v - q95, v + q95) for v in preds],
    }

    return {
        "yhat": preds,
        "intervals": intervals,
        "base_preds": {"ridge_recursive": preds},
    }
