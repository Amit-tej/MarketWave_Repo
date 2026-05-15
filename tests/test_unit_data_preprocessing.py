"""
UNIT TESTING: Data Preprocessing Module
Tests each individual function in data_preprocessing.py in isolation.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_preprocessing import (
    load_csv,
    load_dataset,
    filter_telangana_hyderabad,
    preprocess_prices,
)


class TestLoadCsv:
    """Unit tests for load_csv function."""

    def test_detect_date_column(self, tmp_path, sample_price_df):
        path = tmp_path / "price.csv"
        sample_price_df.to_csv(path, index=False)
        df = load_csv(str(path))
        assert "date" in df.columns
        assert isinstance(
            df["date"].dtype, pd.core.dtypes.dtypes.DatetimeTZDtype
        ) or np.issubdtype(df["date"].dtype, np.datetime64)

    def test_no_date_column_warning(self, tmp_path):
        path = tmp_path / "nodate.csv"
        pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_csv(path, index=False)
        df = load_csv(str(path))
        assert "date" not in df.columns

    def test_rename_date_column(self, tmp_path):
        path = tmp_path / "datetime.csv"
        pd.DataFrame(
            {"Date_Time": ["2023-01-01", "2023-01-02"], "value": [1, 2]}
        ).to_csv(path, index=False)
        df = load_csv(str(path))
        assert "date" in df.columns


class TestLoadDataset:
    """Unit tests for load_dataset function."""

    def test_load_existing_file(self, tmp_path, sample_price_df):
        path = tmp_path / "tomato_price_data2021-2024.csv"
        sample_price_df.to_csv(path, index=False)
        df = load_dataset(str(path))
        assert len(df) == len(sample_price_df)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_dataset("nonexistent_file.csv")


class TestFilterTelanganaHyderabad:
    """Unit tests for filter_telangana_hyderabad function."""

    def test_filters_correctly(self, sample_price_df):
        df = filter_telangana_hyderabad(sample_price_df)
        assert len(df) == len(sample_price_df)
        assert all(df["state_name"].str.lower().str.contains("telangana"))
        assert all(df["district_name"].str.lower().str.contains("hyderabad"))

    def test_excludes_other_states(self):
        df = pd.DataFrame(
            {
                "state_name": ["Karnataka", "Telangana", "Andhra Pradesh"],
                "district_name": ["Bangalore", "Hyderabad", "Vijayawada"],
                "p_modal": [1000, 1200, 1100],
            }
        )
        result = filter_telangana_hyderabad(df)
        assert len(result) == 1
        assert result.iloc[0]["state_name"] == "Telangana"


class TestPreprocessPrices:
    """Unit tests for preprocess_prices function."""

    def test_fill_missing_values(self, sample_price_df_with_missing):
        df = sample_price_df_with_missing.copy()
        df = preprocess_prices(df)
        assert df["p_modal"].isna().sum() == 0
        assert df["p_min"].isna().sum() == 0

    def test_outlier_clipping(self, sample_price_df_with_missing):
        df = sample_price_df_with_missing.copy()
        original_max = df["p_modal"].max()
        df = preprocess_prices(df)
        # outlier at 5000 should be clipped
        assert df["p_modal"].max() < original_max

    def test_date_index_set(self, sample_price_df):
        df = sample_price_df.copy()
        df = preprocess_prices(df)
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_forward_fill_interpolation(self):
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {
                "date": dates,
                "p_min": [100, np.nan, np.nan, 110, 120, np.nan, 130, 140, 150, 160],
                "p_max": [200, np.nan, np.nan, 220, 240, np.nan, 260, 280, 300, 320],
                "p_modal": [150, np.nan, np.nan, 165, 180, np.nan, 195, 210, 225, 240],
            }
        )
        df = preprocess_prices(df)
        assert df["p_modal"].isna().sum() == 0
        # values should be monotonically increasing after fill
        assert df["p_modal"].iloc[1] > 140

    def test_all_price_cols_processed(self, sample_price_df):
        df = sample_price_df.copy()
        df = preprocess_prices(df)
        for col in ["p_min", "p_max", "p_modal"]:
            assert col in df.columns
            assert df[col].isna().sum() == 0
