"""
BLACK BOX TESTING: MarketWave API
Tests the FastAPI backend from an external user's perspective
without inspecting internal implementation details.
"""

import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)


class TestHealthEndpoint:
    """Black box test: System health check"""

    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"


class TestMarketsEndpoint:
    """Black box test: Listing available markets"""

    def test_markets_returns_list(self):
        response = client.get("/markets")
        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        assert isinstance(data["markets"], list)
        assert len(data["markets"]) > 0

    def test_markets_contains_known_market(self):
        response = client.get("/markets")
        data = response.json()
        markets = [m.lower() for m in data["markets"]]
        assert "bowenpally" in markets


class TestCommoditiesEndpoint:
    """Black box test: Listing commodities for a market"""

    def test_commodities_for_valid_market(self):
        response = client.get("/markets/Bowenpally/commodities")
        assert response.status_code == 200
        data = response.json()
        assert "commodities" in data
        assert isinstance(data["commodities"], list)
        assert "Tomato" in data["commodities"]

    def test_commodities_for_invalid_market_404(self):
        response = client.get("/markets/InvalidMarket/commodities")
        assert response.status_code == 404


class TestPredictEndpoint:
    """Black box test: Forecast predictions from user perspective"""

    def test_predict_valid_market_commodity(self):
        payload = {
            "market": "Bowenpally",
            "commodity": "Tomato",
            "horizon": 7,
            "force_simple": True,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "yhat" in data
        assert "intervals" in data
        assert "base_preds" in data
        assert len(data["yhat"]) == 7
        # Verify intervals contain expected confidence levels
        for key in ("80", "90", "95"):
            assert key in data["intervals"]

    def test_predict_invalid_market_404(self):
        payload = {"market": "NonExistent", "commodity": "Tomato", "horizon": 7}
        response = client.post("/predict", json=payload)
        assert response.status_code == 404

    def test_predict_invalid_commodity_404(self):
        payload = {"market": "Bowenpally", "commodity": "Gold", "horizon": 7}
        response = client.post("/predict", json=payload)
        assert response.status_code == 404

    def test_predict_default_horizon(self):
        payload = {"market": "Bowenpally", "commodity": "Tomato"}
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Default horizon is 30
        assert len(data["yhat"]) == 30


class TestExplainEndpoint:
    """Black box test: Explainability endpoint"""

    def test_explain_existing_prediction(self):
        # First get a prediction
        payload = {
            "market": "Bowenpally",
            "commodity": "Tomato",
            "horizon": 7,
            "force_simple": True,
        }
        pred_resp = client.post("/predict", json=payload)
        assert pred_resp.status_code == 200
        pred_id = pred_resp.json()["prediction_id"]

        response = client.get(f"/predictions/{pred_id}/explain")
        assert response.status_code == 200
        data = response.json()
        assert "model_metadata" in data

    def test_explain_invalid_prediction_404(self):
        response = client.get("/predictions/nonexistent_id/explain")
        assert response.status_code == 404


class TestWelcomeEndpoint:
    """Black box test: Welcome message"""

    def test_welcome_message(self):
        response = client.get("/welcome")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "MarketWave" in data["message"]
