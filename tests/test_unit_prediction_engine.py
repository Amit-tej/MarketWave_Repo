"""
UNIT TESTING: Prediction Engine Module
Tests prediction functions in isolation with small subsets of data.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from prediction_engine import fallback_stats_predict, predict_with_simple_ensemble


class TestFallbackStatsPredict:
    """Unit tests for fallback_stats_predict."""

    def test_returns_correct_shape(self, sample_price_df):
        df = sample_price_df.set_index("date")
        result = fallback_stats_predict(df, horizon=10)
        assert "yhat" in result
        assert len(result["yhat"]) == 10
        assert "intervals" in result
        assert "base_preds" in result

    def test_predictions_deterministic(self, sample_price_df):
        df = sample_price_df.set_index("date")
        r1 = fallback_stats_predict(df, horizon=10)
        r2 = fallback_stats_predict(df, horizon=10)
        assert np.allclose(r1["yhat"], r2["yhat"])

    def test_empty_data_returns_nan(self, empty_df):
        result = fallback_stats_predict(empty_df, horizon=5)
        assert len(result["yhat"]) == 5
        assert all(np.isnan(v) for v in result["yhat"])

    def test_no_p_modal_returns_nan(self):
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        result = fallback_stats_predict(df, horizon=5)
        assert all(np.isnan(v) for v in result["yhat"])

    def test_intervals_present(self, sample_price_df):
        df = sample_price_df.set_index("date")
        result = fallback_stats_predict(df, horizon=7)
        for key in ["80", "90", "95"]:
            assert key in result["intervals"]
            assert len(result["intervals"][key]) == 7


class TestPredictWithSimpleEnsemble:
    """Unit tests for predict_with_simple_ensemble."""

    def test_predicts_correct_shape(self, mock_ensemble_path, sample_price_df):
        df = sample_price_df.set_index("date")
        df["feat_a"] = np.random.randn(len(df))
        df["feat_b"] = np.random.randn(len(df))
        result = predict_with_simple_ensemble(mock_ensemble_path, df, horizon=10)
        assert len(result["yhat"]) == 10
        assert "intervals" in result
        assert "base_preds" in result

    def test_predictions_are_numeric(self, mock_ensemble_path, sample_price_df):
        df = sample_price_df.set_index("date")
        df["feat_a"] = np.random.randn(len(df))
        df["feat_b"] = np.random.randn(len(df))
        result = predict_with_simple_ensemble(mock_ensemble_path, df, horizon=5)
        assert all(isinstance(v, (int, float, np.floating)) for v in result["yhat"])
