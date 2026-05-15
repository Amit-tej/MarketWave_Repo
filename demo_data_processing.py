#!/usr/bin/env python3
"""
Demo: Data Processing & Normalization in MarketWave
Run this to see how data preprocessing works step by step.
"""

import os
import sys
import pandas as pd
import numpy as np

# Add project root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from data_preprocessing import (
    load_dataset,
    filter_telangana_hyderabad,
    preprocess_prices,
)
from feature_engineering import prepare_features, get_scalers
from sklearn.preprocessing import MinMaxScaler, StandardScaler

print("=" * 70)
print("MARKETWAVE DATA PROCESSING DEMONSTRATION")
print("=" * 70)

# Load sample data
print("\n[1] LOADING RAW DATA...")
df = load_dataset("tomato_price_data2021-2024.csv")
print(f"    Raw data: {len(df)} rows, {len(df.columns)} columns")
print(f"    Columns: {list(df.columns)}")

# Filter
print("\n[2] FILTERING (Telangana + Hyderabad)...")
df = filter_telangana_hyderabad(df)
print(f"    Filtered: {len(df)} rows")

# Preprocess
print("\n[3] PREPROCESSING PRICES...")
print("    - Forward fill missing values")
print("    - Backward fill missing values")
print("    - Interpolate gaps")
print("    - Winsorize outliers (IQR)")
df = preprocess_prices(df)
print(f"    Preprocessed: {len(df)} rows")

# Show sample of preprocessed data
print("\n    Sample (first 5 rows):")
print(df[["p_min", "p_max", "p_modal"]].head().to_string())

# Feature Engineering
print("\n[4] FEATURE ENGINEERING...")
print("    - Temporal features (day, week, month, quarter, year)")
print("    - Lag features (1, 3, 7, 14, 30 days)")
print("    - Rolling statistics (7, 14, 30 day windows)")
print("    - Momentum & RSI")
print("    - Fourier terms")
print("    - Target encoding")

df_feat = prepare_features(df)
print(f"    Features created: {len(df_feat.columns)} total columns")

# Show feature names
feature_groups = {
    "Temporal": [
        c
        for c in df_feat.columns
        if c
        in [
            "day",
            "week",
            "month",
            "quarter",
            "year",
            "day_of_week",
            "is_weekend",
            "season",
        ]
    ],
    "Lags": [c for c in df_feat.columns if "lag" in c],
    "Rolling": [c for c in df_feat.columns if "ma_" in c or "std_" in c],
    "Momentum": [c for c in df_feat.columns if "momentum" in c or "rsi" in c],
    "Fourier": [c for c in df_feat.columns if "sin_" in c or "cos_" in c],
}

for group, features in feature_groups.items():
    if features:
        print(f"    {group}: {features[:5]}{'...' if len(features) > 5 else ''}")

# Normalization
print("\n[5] NORMALIZATION / SCALING...")
print("\n    Scalers available:")
scalers = get_scalers()
print(f"    - LSTM Scaler: {type(scalers['lstm']).__name__} (range 0-1)")
print(f"    - Tree Scaler: {type(scalers['tree']).__name__} (mean=0, std=1)")

# Demonstrate scaling on a sample
sample_prices = df["p_modal"].tail(30).values.reshape(-1, 1)
print(f"\n    Sample prices (raw): {sample_prices[:5].flatten()}")

minmax = MinMaxScaler()
scaled_minmax = minmax.fit_transform(sample_prices)
print(f"    After MinMaxScaler: {scaled_minmax[:5].flatten()}")

standard = StandardScaler()
scaled_std = standard.fit_transform(sample_prices)
print(f"    After StandardScaler: {scaled_std[:5].flatten()}")

# Data Leakage Prevention
print("\n[6] DATA LEAKAGE PREVENTION...")
print("    ✓ Time-based train/test split (never random)")
print("    ✓ Lag features use only PAST data (shift)")
print("    ✓ Rolling stats use only historical window")
print("    ✓ Test data is always in FUTURE relative to training")

# Train/Test Split Example
train_size = int(len(df) * 0.8)
print(f"\n    Example split:")
print(f"    - Training: rows 0-{train_size} (dates before cutoff)")
print(f"    - Testing: rows {train_size}-{len(df)} (dates after cutoff)")

print("\n" + "=" * 70)
print("PROCESSING COMPLETE!")
print("=" * 70)

print("\nTo use this in your project:")
print("1. API: POST http://localhost:8000/predict")
print("2. Frontend: http://localhost:5173")
print("3. Script: python demo_data_processing.py")
