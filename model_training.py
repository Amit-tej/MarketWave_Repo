import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from utils import get_logger
from config import MODELS_DIR, HYPER

logger = get_logger('model_training')

def train_simple_rf(X, y, market, commodity):
    logger.info('Training RandomForest (simple)')
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=HYPER['random_state'])
    model.fit(X, y)
    path = os.path.join(MODELS_DIR, f'rf_{commodity}_{market}.joblib')
    joblib.dump(model, path)
    logger.info(f'Model saved: {path}')
    return path

def train_stacked_ensemble(X, y, market, commodity):
    # Placeholder stacked ensemble using RF + LinearRegression meta
    logger.info('Training stacked ensemble (placeholder)')
    
    # Preprocess features to handle categorical columns
    X_processed = X.copy()
    
    # Convert categorical/object columns to numeric codes
    for col in X_processed.select_dtypes(include=['object', 'category']).columns:
        X_processed[col] = X_processed[col].astype('category').cat.codes.replace(-1, np.nan)
    
    # Fill any remaining NaN values
    X_processed = X_processed.fillna(X_processed.mean())
    
    # Ensure all columns are numeric
    for col in X_processed.columns:
        X_processed[col] = pd.to_numeric(X_processed[col], errors='coerce')
    
    # Fill any NaN values created by coercion
    X_processed = X_processed.fillna(0)
    
    # base models
    m1 = RandomForestRegressor(n_estimators=100, random_state=HYPER['random_state'])
    m2 = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=HYPER['random_state'])

    tscv = TimeSeriesSplit(n_splits=3)
    S = np.zeros((len(X_processed), 2))
    for i, (train_idx, test_idx) in enumerate(tscv.split(X_processed)):
        Xtr, Xte = X_processed.iloc[train_idx], X_processed.iloc[test_idx]
        ytr, yte = y.iloc[train_idx], y.iloc[test_idx]
        m1.fit(Xtr, ytr)
        m2.fit(Xtr, ytr)
        S[test_idx,0] = m1.predict(Xte)
        S[test_idx,1] = m2.predict(Xte)

    meta = LinearRegression()
    meta.fit(S, y)

    # Fit base models on full data
    m1.fit(X_processed, y)
    m2.fit(X_processed, y)

    ensemble = {'m1': m1, 'm2': m2, 'meta': meta, 'feature_columns': list(X_processed.columns)}
    path = os.path.join(MODELS_DIR, f'ensemble_{commodity}_{market}.joblib')
    joblib.dump(ensemble, path)
    logger.info(f'Ensemble saved: {path}')
    return path

def load_model(path):
    if os.path.exists(path):
        return joblib.load(path)
    else:
        raise FileNotFoundError(path)
