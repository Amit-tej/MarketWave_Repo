"""
Pytest configuration and shared fixtures for MarketWave test suites.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def sample_price_df():
    """Generate a small mock price DataFrame for Telangana/Hyderabad."""
    dates = pd.date_range(start="2023-01-01", periods=60, freq="D")
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "date": dates,
            "cmdty": ["Tomato"] * 60,
            "variety": ["Local"] * 60,
            "market_name": ["Bowenpally"] * 60,
            "state_name": ["Telangana"] * 60,
            "district_name": ["Hyderabad"] * 60,
            "p_min": np.random.uniform(800, 1200, 60),
            "p_max": np.random.uniform(1200, 2000, 60),
            "p_modal": np.random.uniform(1000, 1600, 60),
        }
    )
    return df


@pytest.fixture
def sample_price_df_with_missing():
    """Mock DataFrame with missing values and outliers for edge-case testing."""
    dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
    np.random.seed(7)
    p_modal = np.random.uniform(1000, 1500, 30).astype(float)
    p_modal[5] = np.nan
    p_modal[10] = 5000  # outlier
    df = pd.DataFrame(
        {
            "date": dates,
            "cmdty": ["Onion"] * 30,
            "market_name": ["Gudimalkapur"] * 30,
            "state_name": ["Telangana"] * 30,
            "district_name": ["Hyderabad"] * 30,
            "p_min": np.random.uniform(600, 900, 30),
            "p_max": np.random.uniform(900, 1400, 30),
            "p_modal": p_modal,
        }
    )
    return df


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def sample_csv_path(tmp_path, sample_price_df):
    path = tmp_path / "test_price_data.csv"
    sample_price_df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def mock_ensemble_path(tmp_path):
    """Create a minimal simple ensemble artifact for testing prediction engine."""
    import joblib
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge

    m1 = RandomForestRegressor(n_estimators=5, random_state=42)
    m2 = RandomForestRegressor(n_estimators=5, random_state=43)
    meta = Ridge()
    # dummy fit so predict works
    X_dummy = np.array([[1, 2], [3, 4], [5, 6]])
    y_dummy = np.array([10, 20, 30])
    m1.fit(X_dummy, y_dummy)
    m2.fit(X_dummy, y_dummy)
    meta.fit(np.array([[10, 10], [20, 20], [30, 30]]), y_dummy)

    ensemble = {"m1": m1, "m2": m2, "meta": meta}
    path = tmp_path / "ensemble_test.joblib"
    joblib.dump(ensemble, path)
    return str(path)


@pytest.fixture(scope="session")
def dataset_dir():
    return os.path.join(ROOT, "dataset")
