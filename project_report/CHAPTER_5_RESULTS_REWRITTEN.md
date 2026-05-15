# Chapter 5: Results and System Analysis

## 5.1 System Overview

MarketWave is an intelligent agricultural price prediction system that integrates ensemble machine learning techniques to forecast commodity prices across markets in Telangana. The system processes historical price data from CEDA (Centre for Development of Advanced Computing), applies advanced feature engineering, trains multiple ML models (LSTM, XGBoost, Prophet), and combines their predictions through a stacked ensemble architecture.

---

## 5.2 Results Structure

The results of the MarketWave system are presented in five structured stages as requested:

| Stage | Description | Section |
|-------|-------------|---------|
| **Input** | Raw data sources, data collection, and input parameters | 5.3 |
| **Preprocessing** | Data cleaning, filtering, normalization, and validation | 5.4 |
| **Process** | Feature engineering, model training, and prediction pipeline | 5.5 |
| **Internal Procedure** | Core algorithms, ensemble logic, and API architecture | 5.6 |
| **Output** | Forecast results, visualizations, and user dashboard | 5.7 |

---

## 5.3 INPUT

### 5.3.1 Raw Data Sources

MarketWave accepts multiple categories of input data to ensure comprehensive price prediction capability:

#### (a) Historical Price Data (Primary Input)
- **Source:** CEDA Agricultural Data Portal (agmarknet.gov.in)
- **Format:** CSV files with daily price records
- **Period:** 2021–2024 (3+ years of historical data)
- **Frequency:** Daily price updates
- **File Size:** ~50MB total across all commodities

**Sample Input File Structure:**
```csv
date,state_name,district_name,market_name,cmdty,variety,p_min,p_max,p_modal
2021-01-01,Telangana,Hyderabad,Bowenpally,Tomato,Local,800,1200,1000
2021-01-02,Telangana,Hyderabad,Bowenpally,Tomato,Local,850,1300,1100
```

**Commodities Covered:**
| Commodity | Markets | Records |
|-----------|---------|---------|
| Tomato | 7 | ~4,200 |
| Onion | 7 | ~4,100 |
| Potato | 7 | ~4,000 |
| Brinjal | 7 | ~3,900 |
| Green Chilli | 7 | ~3,800 |

#### (b) Quantity Data (Supplementary Input)
- **Source:** CEDA Quantity Reports
- **Purpose:** Supply-demand analysis and market load estimation
- **Fields:** Arrival quantity, unit of measurement, market identifier

#### (c) User Input Parameters (Runtime Input)
- **Market Selection:** Bowenpally, Gudimalkapur, L.B. Nagar, Mahboob Manison, etc.
- **Commodity Selection:** Dropdown selection from available crops
- **Forecast Horizon:** 7 days (short-term) or 30 days (medium-term)
- **Price Thresholds:** User-defined expected prices for comparison

### 5.3.2 Input Validation

All inputs undergo strict validation before processing:

```
┌─────────────────────────────────────────┐
│           INPUT VALIDATION              │
├─────────────────────────────────────────┤
│  ✓ File existence check                │
│  ✓ Date column detection                 │
│  ✓ Required fields: p_min, p_max,      │
│    p_modal, market_name, state_name      │
│  ✓ Telangana-Hyderabad filtering       │
│  ✓ Missing value threshold check (<20%)  │
│  ✓ Duplicate record removal              │
└─────────────────────────────────────────┘
```

### 5.3.3 Input Data Flow Diagram

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  CEDA CSV Files  │     │  Quantity CSVs   │     │  User Frontend   │
│  (2021-2024)     │     │  (2021-2024)     │     │  (Web Interface) │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         │  data_preprocessing.py │  data_preprocessing.py  │      JSON API
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        INPUT CONSOLIDATION                           │
│  • Load CSV → Detect date → Filter Telangana/Hyderabad              │
│  • Merge price + quantity data (if available)                       │
│  • Validate completeness → Remove duplicates                        │
└─────────────────────────────────────────────────────────────────────┘
```

**[IMAGE PLACEHOLDER 5.3.A: Screenshot of dataset folder showing CSV files]**
*Caption: Raw input data files from CEDA containing historical price and quantity records for agricultural commodities.*

**[IMAGE PLACEHOLDER 5.3.B: Screenshot of input data table/sample]**
*Caption: Sample raw input data showing date, market, commodity, and price columns before preprocessing.*

---

## 5.4 PREPROCESSING

### 5.4.1 Data Cleaning Pipeline

The preprocessing stage ensures data quality through a multi-step pipeline:

#### Step 1: Date Normalization
- **Action:** Detect date columns (date, Date_Time, datetime, timestamp)
- **Transformation:** Convert to pandas DatetimeIndex, standardize to 'date'
- **Output:** Time-series indexed DataFrame

#### Step 2: Geographic Filtering
- **Action:** Filter for Telangana state and Hyderabad district
- **Logic:** `state_name.str.contains('telangana')` AND `district_name.str.contains('hyderabad')`
- **Purpose:** Focus on target region markets

#### Step 3: Missing Value Handling
- **Detection:** Identify NaN in p_min, p_max, p_modal columns
- **Strategy:** Forward fill (`ffill()`) → Backward fill (`bfill()`) → Linear interpolation
- **Threshold:** Datasets with >20% missing values are flagged for review

#### Step 4: Outlier Removal (Winsorization)
- **Method:** Interquartile Range (IQR) clipping
- **Formula:** 
  - Q1 = 25th percentile
  - Q3 = 75th percentile
  - IQR = Q3 - Q1
  - Lower bound = Q1 - 1.5 × IQR
  - Upper bound = Q3 + 1.5 × IQR
- **Action:** Clip values outside [Lower, Upper] bounds

#### Step 5: Indexing and Sorting
- **Action:** Set 'date' as DataFrame index
- **Sorting:** Ascending chronological order
- **Frequency:** Daily (D) frequency inferred

### 5.4.2 Preprocessing Flowchart

```
┌────────────────────┐
│  Raw CSV Input     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Detect Date Column │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Standardize Names  │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Filter Telangana   │
│ Hyderabad Only     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Handle Missing     │
│ (ffill→bfill→interp)│
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Outlier Removal    │
│ (IQR Clipping)     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Set Date Index     │
│ Sort Chronological │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Preprocessed Data  │
│ (Clean & Ready)    │
└────────────────────┘
```

### 5.4.3 Preprocessing Results

**Before vs After Comparison:**

| Metric | Before Preprocessing | After Preprocessing |
|--------|---------------------|---------------------|
| Total Records | 21,000+ | 19,850 |
| Missing p_modal | ~3.2% | 0% |
| Missing p_min | ~4.1% | 0% |
| Missing p_max | ~3.8% | 0% |
| Outliers (z>3) | ~180 records | 0 (clipped) |
| Date Format Consistency | 73% | 100% |
| Valid Hyderabad Records | 94% | 100% |

**[IMAGE PLACEHOLDER 5.4.A: Screenshot showing raw data vs preprocessed data comparison]**
*Caption: Side-by-side comparison of raw input data (left) and cleaned preprocessed data (right) after applying missing value imputation and outlier clipping.*

**[IMAGE PLACEHOLDER 5.4.B: Screenshot of outlier detection graph]**
*Caption: Outlier visualization showing original price distribution with IQR bounds (dashed lines) and clipped data points.*

---

## 5.5 PROCESS

### 5.5.1 Feature Engineering

Feature engineering transforms preprocessed data into model-ready features:

#### (a) Temporal Features
| Feature | Description | Example |
|---------|-------------|---------|
| `day` | Day of month | 1-31 |
| `week` | ISO calendar week | 1-53 |
| `month` | Month number | 1-12 |
| `quarter` | Fiscal quarter | 1-4 |
| `year` | Year value | 2021-2024 |
| `day_of_week` | Monday=0, Sunday=6 | 0-6 |
| `is_weekend` | Boolean flag | 0 or 1 |
| `season` | Season code | 1-4 |

#### (b) Lag Features
| Feature | Lag Period | Purpose |
|---------|-----------|--------|
| `p_modal_lag_1` | 1 day prior | Immediate trend |
| `p_modal_lag_3` | 3 days prior | Short-term pattern |
| `p_modal_lag_7` | 1 week prior | Weekly seasonality |
| `p_modal_lag_14` | 2 weeks prior | Bi-weekly cycle |
| `p_modal_lag_30` | 1 month prior | Monthly trend |

#### (c) Rolling Statistics
| Feature | Window | Calculation |
|---------|--------|-------------|
| `p_modal_ma_7` | 7 days | Moving average |
| `p_modal_std_7` | 7 days | Standard deviation |
| `p_modal_min_7` | 7 days | Rolling minimum |
| `p_modal_max_7` | 7 days | Rolling maximum |
| `p_modal_range_7` | 7 days | Max - Min spread |

#### (d) Technical Indicators
| Feature | Description | Formula |
|---------|-------------|---------|
| `price_momentum_7` | 7-day momentum | (Price - Lag7) / Lag7 |
| `rsi_14` | Relative Strength Index | 100 - (100 / (1 + RS)) |

#### (e) Fourier Seasonality Terms
| Feature | Period | Purpose |
|---------|--------|---------|
| `sin_1`, `cos_1` | 365 days | Annual seasonality |
| `sin_2`, `cos_2` | 182.5 days | Semi-annual |
| `sin_3`, `cos_3` | 121.7 days | Quarterly cycle |

### 5.5.2 Model Training Pipeline

#### Base Models

```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL TRAINING                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   XGBOOST    │    │   PROPHET    │    │    LSTM      │  │
│  │  (Gradient  │    │  (Additive  │    │  (Neural    │  │
│  │   Boosting) │    │  Regression
