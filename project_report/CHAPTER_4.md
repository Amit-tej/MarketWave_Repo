## Chapter 4: Implementation Details

### 4.1 Development Environment

#### 4.1.1 Technical Requirements
1. Hardware Requirements
   - Processor: Intel Core i5 or equivalent
   - RAM: 8GB minimum (16GB recommended)
   - Storage: 10GB free space
   - GPU: Optional (for LSTM training)

2. Software Requirements
   - Operating System: Windows 10/11, Linux, or macOS
   - Python 3.9 or higher
   - Git for version control
   - Virtual environment manager (venv/conda)

#### 4.1.2 Dependencies
```python
# Core Dependencies
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.6.1
joblib>=1.1.0
matplotlib>=3.5.0

# Model-specific Dependencies
xgboost>=1.5.0
prophet>=1.0
tensorflow>=2.8.0
statsmodels>=0.13.0

# Development Dependencies
pytest>=7.0.0
black>=22.0.0
pylint>=2.12.0
```

### 4.2 Core Implementation

#### 4.2.1 Data Preprocessing Module
```python
class DataPreprocessor:
    def __init__(self, config):
        self.config = config
        self.scalers = {}
        self.encoders = {}

    def clean_data(self, df):
        """
        Clean and validate input data
        
        Parameters:
        - df: Raw DataFrame with price data
        
        Returns:
        - Cleaned DataFrame
        """
        # Handle missing values
        df['p_modal'].fillna(method='ffill', inplace=True)
        
        # Remove outliers using IQR method
        Q1 = df['p_modal'].quantile(0.25)
        Q3 = df['p_modal'].quantile(0.75)
        IQR = Q3 - Q1
        df = df[~((df['p_modal'] < (Q1 - 1.5 * IQR)) | 
                  (df['p_modal'] > (Q3 + 1.5 * IQR)))]
        
        # Normalize price data
        df['p_modal'] = (df['p_modal'] - df['p_modal'].mean()) / df['p_modal'].std()
        
        return df

    def generate_features(self, df):
        """
        Generate time series features
        
        Parameters:
        - df: Cleaned DataFrame
        
        Returns:
        - DataFrame with additional features
        """
        # Temporal features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['day_of_year'] = df.index.dayofyear
        
        # Lag features
        for lag in [1, 7, 14, 30]:
            df[f'lag_{lag}'] = df['p_modal'].shift(lag)
            
        # Rolling statistics
        for window in [7, 14, 30]:
            df[f'rolling_mean_{window}'] = df['p_modal'].rolling(window).mean()
            df[f'rolling_std_{window}'] = df['p_modal'].rolling(window).std()
            
        # Price momentum
        df['price_momentum'] = df['p_modal'].diff()
        
        return df
```

#### 4.2.2 Model Implementation

1. XGBoost Implementation
```python
class XGBoostWrapper:
    def __init__(self, params=None):
        self.default_params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'objective': 'reg:squarederror'
        }
        self.params = params or self.default_params
        self.model = None
        
    def train(self, X, y):
        """
        Train XGBoost model
        
        Parameters:
        - X: Feature matrix
        - y: Target variable
        """
        import xgboost as xgb
        dtrain = xgb.DMatrix(X, label=y)
        self.model = xgb.train(self.params, dtrain)
        
    def predict(self, X):
        """
        Generate predictions
        
        Parameters:
        - X: Feature matrix
        
        Returns:
        - numpy array of predictions
        """
        dtest = xgb.DMatrix(X)
        return self.model.predict(dtest)
```

2. Prophet Implementation
```python
class ProphetWrapper:
    def __init__(self):
        from fbprophet import Prophet
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        
    def prepare_data(self, df):
        """
        Prepare data for Prophet format
        """
        prophet_df = pd.DataFrame()
        prophet_df['ds'] = df.index
        prophet_df['y'] = df['p_modal']
        return prophet_df
        
    def train(self, df):
        """
        Train Prophet model
        """
        prophet_df = self.prepare_data(df)
        self.model.fit(prophet_df)
```

3. LSTM Implementation
```python
class LSTMWrapper:
    def __init__(self, config):
        self.config = config
        self.model = self._build_model()
        
    def _build_model(self):
        """
        Build LSTM architecture
        """
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(self.config['seq_length'], 1)),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
```

### 4.3 Ensemble Integration

#### 4.3.1 Ensemble Architecture
```python
class EnsemblePredictor:
    def __init__(self, models, weights=None):
        self.models = models
        self.weights = weights or self._initialize_weights()
        
    def _initialize_weights(self):
        """
        Initialize model weights equally
        """
        n_models = len(self.models)
        return [1.0/n_models] * n_models
        
    def predict(self, X):
        """
        Generate weighted ensemble predictions
        """
        predictions = []
        for model, weight in zip(self.models, self.weights):
            pred = model.predict(X)
            predictions.append(pred * weight)
        return np.sum(predictions, axis=0)
```

#### 4.3.2 Confidence Interval Generation
```python
def generate_confidence_intervals(predictions, residuals, confidence_levels=[0.8, 0.9, 0.95]):
    """
    Generate confidence intervals for predictions
    """
    intervals = {}
    for level in confidence_levels:
        z_score = stats.norm.ppf((1 + level) / 2)
        margin = z_score * np.std(residuals)
        intervals[f'{int(level*100)}'] = (predictions - margin, predictions + margin)
    return intervals
```

### 4.4 Market Analysis Implementation

#### 4.4.1 Market Comparison
```python
def compare_markets(predictions_dict, costs_dict):
    """
    Compare predicted prices across markets
    
    Parameters:
    - predictions_dict: Dictionary of market predictions
    - costs_dict: Dictionary of transportation costs
    
    Returns:
    - DataFrame with market rankings
    """
    comparisons = []
    for market, preds in predictions_dict.items():
        profit = calculate_profit(preds, costs_dict[market])
        comparisons.append({
            'market': market,
            'predicted_price': np.mean(preds),
            'profit_potential': profit,
            'confidence': calculate_confidence(preds)
        })
    return pd.DataFrame(comparisons)
```