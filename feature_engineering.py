import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from utils import get_logger, cache_save, cache_load

logger = get_logger('feature_engineering')

def add_temporal_features(df):
    df = df.copy()
    idx = df.index if hasattr(df, 'index') else pd.to_datetime(df['date'])
    df['day'] = idx.day
    df['week'] = idx.isocalendar().week
    df['month'] = idx.month
    df['quarter'] = idx.quarter
    df['year'] = idx.year
    df['day_of_week'] = idx.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5,6]).astype(int)
    # seasons: simple grouping by month
    df['season'] = df['month']%12 // 3 + 1
    return df

def add_lag_features(df, cols=['p_modal'], lags=[1,3,7,14,30]):
    df = df.copy()
    for col in cols:
        for lag in lags:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    return df

def add_rolling_stats(df, cols=['p_modal'], windows=[7,14,30]):
    df = df.copy()
    for col in cols:
        for w in windows:
            df[f'{col}_ma_{w}'] = df[col].rolling(w, min_periods=1).mean()
            df[f'{col}_min_{w}'] = df[col].rolling(w, min_periods=1).min()
            df[f'{col}_max_{w}'] = df[col].rolling(w, min_periods=1).max()
            df[f'{col}_std_{w}'] = df[col].rolling(w, min_periods=1).std().fillna(0)
            df[f'{col}_range_{w}'] = df[f'{col}_max_{w}'] - df[f'{col}_min_{w}']
    return df

def add_momentum_rsi(df, col='p_modal'):
    df = df.copy()
    # Momentum (7-day)
    df['price_momentum_7'] = (df[col] - df[f'{col}_lag_7']) / df[f'{col}_lag_7']

    # RSI (14-day)
    window = 14
    delta = df[col].diff()
    up = delta.clip(lower=0).rolling(window=window).mean()
    down = -delta.clip(upper=0).rolling(window=window).mean()
    rs = up / (down + 1e-8)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    return df

def add_fourier_terms(df, period=365, order=3):
    df = df.copy()
    t = np.arange(len(df))
    for k in range(1, order+1):
        df[f'sin_{k}'] = np.sin(2 * np.pi * k * t / period)
        df[f'cos_{k}'] = np.cos(2 * np.pi * k * t / period)
    return df

def target_encode(df, col, target='p_modal', min_samples=1, smoothing=1):
    # Simple target encoding
    means = df.groupby(col)[target].mean()
    counts = df.groupby(col)[target].count()
    global_mean = df[target].mean()
    smooth = (counts * means + smoothing * global_mean) / (counts + smoothing)
    return df[col].map(smooth)

def prepare_features(df):
    df = df.copy()
    df = add_temporal_features(df)
    df = add_lag_features(df, cols=['p_min','p_max','p_modal'])
    df = add_rolling_stats(df, cols=['p_modal'])
    df = add_momentum_rsi(df, col='p_modal')
    df = add_fourier_terms(df)

    # Simple target encoding for categorical columns if present
    for c in ['cmdty','variety','market_name']:
        if c in df.columns:
            df[f'{c}_te'] = target_encode(df, c)

    # Fill remaining NaNs using forward/backward fill then zeros
    df = df.ffill().bfill().fillna(0)
    # ensure 'date' column exists if original had 't'
    if 't' in df.columns and 'date' not in df.columns:
        df['date'] = pd.to_datetime(df['t'], errors='coerce')
    return df

def get_scalers():
    return {
        'lstm': MinMaxScaler(),
        'tree': StandardScaler()
    }
