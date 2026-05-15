"""
UNIT TESTING: Feature Engineering Module
Tests each individual feature generation function in isolation.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from feature_engineering import (
    add_temporal_features,
    add_lag_features,
    add_rolling_stats,
    add_momentum_rsi,
    add_fourier_terms,
    prepare_features,
    get_scalers,
)


class TestAddTemporalFeatures:
    def test_creates_expected_columns(self, sample_price_df):
        df = add_temporal_features(sample_price_df.set_index("date"))
        expected = [
            "day",
            "week",
            "month",
            "quarter",
            "year",
            "day_of_week",
            "is_weekend",
            "season",
        ]
        for col in expected:
            assert col in df.columns

    def test_weekend_flag_correct(self):
        dates = pd.date_range("2023-01-01", periods=7, freq="D")
        df = pd.DataFrame({"value": range(7)}, index=dates)
        df = add_temporal_features(df)
        assert df["is_weekend"].isin([0, 1]).all()


class TestAddLagFeatures:
    def test_lag_columns_created(self, sample_price_df):
        df = sample_price_df.set_index("date")
        df = add_lag_features(df, cols=["p_modal"], lags=[1, 7])
        assert "p_modal_lag_1" in df.columns
        assert "p_modal_lag_7" in df.columns

    def test_lag_values_correct(self):
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        df = pd.DataFrame({"p_modal": [10, 20, 30, 40, 50]}, index=dates)
        df = add_lag_features(df, cols=["p_modal"], lags=[1])
        assert df["p_modal_lag_1"].iloc[1] == 10
        assert df["p_modal_lag_1"].iloc[2] == 20
        assert pd.isna(df["p_modal_lag_1"].iloc[0])


class TestAddRollingStats:
    def test_rolling_columns_created(self, sample_price_df):
        df = sample_price_df.set_index("date")
        df = add_rolling_stats(df, cols=["p_modal"], windows=[7, 14])
        assert "p_modal_ma_7" in df.columns
        assert "p_modal_std_7" in df.columns
        assert "p_modal_range_7" in df.columns

    def test_rolling_mean_reasonable(self):
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        df = pd.DataFrame({"p_modal": [100] * 10}, index=dates)
        df = add_rolling_stats(df, cols=["p_modal"], windows=[3])
        assert (df["p_modal_ma_3"] == 100).all()


class TestAddMomentumRsi:
    def test_momentum_and_rsi_created(self, sample_price_df):
        df = sample_price_df.set_index("date")
        df = add_lag_features(df, cols=["p_modal"], lags=[7])
        df = add_momentum_rsi(df, col="p_modal")
        assert "price_momentum_7" in df.columns
        assert "rsi_14" in df.columns

    def test_rsi_within_bounds(self):
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        np.random.seed(1)
        prices = np.cumsum(np.random.randn(30)) + 100
        df = pd.DataFrame({"p_modal": prices}, index=dates)
        df = add_lag_features(df, cols=["p_modal"], lags=[7])
        df = add_momentum_rsi(df, col="p_modal")
        valid_rsi = df["rsi_14"].dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


class TestAddFourierTerms:
    def test_fourier_columns_created(self, sample_price_df):
        df = sample_price_df.set_index("date")
        df = add_fourier_terms(df, period=365, order=3)
        for k in range(1, 4):
            assert f"sin_{k}" in df.columns
            assert f"cos_{k}" in df.columns


class TestPrepareFeatures:
    def test_prepare_features_returns_df(self, sample_price_df):
        df = sample_price_df.set_index("date")
        result = prepare_features(df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(df)

    def test_no_nans_after_prepare(self, sample_price_df):
        df = sample_price_df.set_index("date")
        result = prepare_features(df)
        assert result.isna().sum().sum() == 0

    def test_target_encoding_created(self, sample_price_df):
        df = sample_price_df.set_index("date")
        result = prepare_features(df)
        if "cmdty" in sample_price_df.columns:
            assert "cmdty_te" in result.columns


class TestGetScalers:
    def test_returns_dict(self):
        scalers = get_scalers()
        assert isinstance(scalers, dict)
        assert "lstm" in scalers
        assert "tree" in scalers
