# Data Processing & Normalization in MarketWave

## 1. Data Leakage Prevention

### How Data Leakage is Handled in This Project

Data leakage is prevented through **temporal (time-series) splitting** rather than random train/test splitting. The project uses a strict chronological approach:

```python
# In accuracy_benchmark.py - Time Series CV Split
train_end = total_size - (n_splits - fold) * test_size
test_start = train_end
test_end = test_start + test_size

train_data = sub.iloc[:train_end].copy()   # Past data only
test_data = sub.iloc[test_start:test_end].copy()  # Future data only
```

### Data Leakage Prevention Techniques

| Technique | Implementation | Purpose |
|----------|--------------|---------|
| **Time-based Splitting** | `train_data = sub.iloc[:train_end]` | Ensures test data is always AFTER train data chronologically |
| **No Future Information in Lags** | `df[col].shift(lag)` creates lag features | Uses only PAST values to predict FUTURE |
| **Rolling Statistics** | `df[col].rolling(window)` | Uses only historical window, no lookahead |
| **Sequential Train/Test** | Train models first, then predict | Models never see test data during training |

### Why This Prevents Data Leakage

1. **Lagged Features**: When predicting day 30, we only use features from days 1-29 (not day 30)
2. **Rolling Means**: Rolling average uses only past N days, never includes future
3. **Train/Test Split**: Test set is ALWAYS in the future relative to training set
4. **No Shuffling**: Time series order is preserved, no random sampling

---

## 2. Normalization & Scaling

### Scalers Used in the Project

```python
# In feature_engineering.py
def get_scalers():
    return {
        'lstm': MinMaxScaler(),    # For LSTM neural network (0-1 range)
        'tree': StandardScaler()  # For XGBoost (mean=0, std=1)
    }
```

### Where Normalization is Applied

| Component | Scaler Used | Purpose |
|-----------|-------------|---------|
| **LSTM** | MinMaxScaler | Neural networks need bounded inputs (0-1) |
| **XGBoost** | StandardScaler | Tree-based models less sensitive, but helps |
| **Prophet** | None needed | Handles raw prices directly |
| **Feature Engineering** | Fill NaN → 0 | Handles missing values before scaling |

### How Scaling is Applied

**For LSTM:**
```python
# In lstm_wrapper.py
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(raw_data.reshape(-1,1))
# Inverse transform after prediction
predicted_raw = scaler.inverse_transform(predicted_scaled)
```

**For XGBoost:**
```python
# In xgboost_wrapper.py  
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaled_X = scaler.fit_transform(X)
```

---

## 3. Complete Data Preprocessing Pipeline

### Step-by-Step Flow

```
Raw CSV Data
    │
    ▼
┌─────────────────────────────────────┐
│ 1. LOAD CSV                        │
│    - Detect date column             │
│    - Parse dates                 │
│    - Normalize column names       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. FILTER                        │
│    - Filter by State (Telangana)  │
│    - Filter by District (Hyderabad) │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. PREPROCESS PRICES              │
│    - Forward fill missing         │
│    - Backward fill missing      │
│    - Interpolate gaps         │
│    - Winsorize outliers (IQR)  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 4. FEATURE ENGINEERING          │
│    - Temporal features         │
│    - Lag features           │
│    - Rolling statistics     │
│    - Momentum & RSI         │
│    - Fourier terms          │
│    - Target encoding       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 5. NORMALIZE/SCALE            │
│    - LSTM: MinMaxScaler      │
│    - XGB: StandardScaler  │
│    - Fill remaining NaN    │
└─────────────────────────────────────┘
    │
    ▼
Ready for Model Training / Prediction
```

---

## 4. How to Run the Data Processing

### Option A: Using Python Script

```python
from data_preprocessing import load_dataset, filter_telangana_hyderabad, preprocess_prices
from feature_engineering import prepare_features

# Load raw data
df = load_dataset('tomato_price_data2021-2024.csv')

# Filter
df = filter_telangana_hyderabad(df)

# Preprocess prices (missing values, outliers)
df = preprocess_prices(df)

# Create features
df_features = prepare_features(df)

print(f"Processed {len(df_features)} rows")
print(f"Features: {list(df_features.columns)}")
```

### Option B: Using the API

```bash
# Start the backend
python api_server.py

# Make a prediction (automatically processes data)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"market": "Bowenpally", "commodity": "Tomato", "horizon": 7}'
```

### Option C: Using the Frontend

1. Open http://localhost:5173
2. Select Market (e.g., Bowenpally)
3. Select Commodity (e.g., Tomato)
4. Select Horizon (e.g., 7 days)
5. Click "Predict"
6. Backend automatically runs all preprocessing

---

## 5. Data Quality Checks

### Missing Values Handling (in `preprocess_prices`)

```python
# 1. Forward fill: Use previous value
df[price_cols] = df[price_cols].ffill()

# 2. Backward fill: Use next value (for first rows)
df[price_cols] = df[price_cols].bfill()

# 3. Interpolate: Linear interpolation
df[price_cols] = df[price_cols].interpolate()
```

### Outlier Handling (Winsorization)

```python
# IQR-based outlier clipping
q1 = df[col].quantile(0.25)
q3 = df[col].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
df[col] = df[col].clip(lower, upper)
```

---

## 6. Summary

| Aspect | Technique Used |
|--------|-------------|
| **Data Leakage Prevention** | Time-based train/test split, no future information in features |
| **Missing Values** | Forward fill → Backward fill → Interpolation |
| **Outliers** | IQR-based winsorization (clip to Q1-1.5*IQR, Q3+1.5*IQR) |
| **Scaling (LSTM)** | MinMaxScaler (0-1 range) |
| **Scaling (XGBoost)** | StandardScaler (mean=0, std=1) |
| **Categorical Encoding** | Target encoding with smoothing |
| **Feature Creation** | Temporal, Lag, Rolling, Momentum, Fourier |

All preprocessing is applied automatically when you make a prediction via API or frontend!
