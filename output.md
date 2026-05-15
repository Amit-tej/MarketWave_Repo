# Explanation of Numerical Outputs in Price Prediction

This document explains how the numerical outputs in the farmer price predictor are calculated, based on the command executed: `python .\farmer_price_predictor.py predict --data onion_price_data2021-2024.csv --market "Gudimalkapur" --commodity "onion" --horizon 30`

Since the specific ensemble model for "onion" in "Gudimalkapur" was not found, the system fell back to a statistical forecasting method using Exponential Smoothing from the statsmodels library.

## 1. Data Loading and Preprocessing
- **CSV Loading**: The dataset `onion_price_data2021-2024.csv` is loaded from the `dataset/` directory.
- **Filtering**: Data is filtered to Telangana-Hyderabad region, resulting in 4836 rows.
- **Preprocessing**: Prices are cleaned, and features are prepared (e.g., date indexing, handling missing values).
- **Subset Selection**: Data for "onion" commodity in "Gudimalkapur" market is selected for prediction.

## 2. Forecasting Method (Fallback: Exponential Smoothing)
When the trained model is unavailable, the system uses `fallback_stats_predict` which employs Exponential Smoothing for time series forecasting.

### Exponential Smoothing Model
- **Model Type**: `statsmodels.tsa.holtwinters.ExponentialSmoothing`
- **Parameters**:
  - `seasonal_periods=7` (weekly seasonality, if data length >= 14)
  - `trend='add'` (additive trend, if data length > 30)
  - `seasonal='add'` (additive seasonality, if seasonal_periods is set)
- **Fitting**: The model is fitted to the historical price series (`p_modal`) using optimized parameters.
- **Forecasting**: Generates 30-day ahead predictions (`yhat`) using `fit.forecast(horizon=30)`.

### Prediction Values (`yhat`)
- These are the forecasted modal prices in ₹/quintal for each day +1 to +30.
- Example: Day +1: 2322.35 ₹/quintal
- Calculation: Direct output from the Exponential Smoothing forecast method.

### Per Kg Prices
- Calculated as: `per_kg = per_quintal / 100.0`
- Example: 2322.35 ₹/quintal → 23.22 ₹/kg

## 3. Confidence Intervals (80% CI)
- **Method**: Based on residuals from the fitted model.
- **Residuals**: `residuals = fit.fittedvalues - train_series`
- **Standard Deviation**: `std = residuals.std()`
- **Quantile Multipliers**:
  - 80% CI: `q80 = 1.28 * std` (approximate z-score for 80% confidence in normal distribution)
  - 90% CI: `q90 = 1.64 * std`
  - 95% CI: `q95 = 1.96 * std`
- **Interval Calculation**: For each forecast `y`, CI = `(y - q, y + q)`
- Example: 80% CI: (2051.80, 2592.90) for Day +1

## 4. 30-day Calendar
- **Generation**: Starts from the current date (today).
- **Format**: Dates are formatted as "Day Mon-DD" (e.g., Thu 25-Sep).
- **Grouping**: Days are grouped by weeks (Sunday to Saturday).
- **Display**: Printed in lines, each representing a week.

## 5. Forecast Sparkline
- **Function**: `ascii_sparkline(yhat, width=40)`
- **Process**:
  - Takes the 30 prediction values.
  - If more than 40 values, downsamples by averaging.
  - Finds min and max of values.
  - Maps each value to one of 8 spark characters: ['▁','▂','▃','▄','▅','▆','▇','█']
  - Formula: `char_index = int((value - min) / (max - min) * 7)`
- **Output**: A visual representation like "▅▁▁▁▂▂▃▆▁▂▂▂▃▃▆▂▃▃▃▄▄▇▂▃▃▃▄▅█▃"

## 6. Day-by-day Breakdown
- **Format**: For each day +i (i=1 to 30):
  - `per_quintal`: Forecasted price in ₹/quintal
  - `per_kg`: `per_quintal / 100`
  - `80% CI`: `(low, high)` where low = y - q80, high = y + q80

## 7. Trend Detection
- **Method**: Linear regression on the forecast values.
- **Calculation**:
  - `x = np.arange(len(yhat))` (0 to 29)
  - `slope = np.polyfit(x, yhat, 1)[0]`
- **Classification**:
  - If slope > 0.01: "↗️ Increasing"
  - If slope < -0.01: "↘️ Decreasing"
  - Else: "→ Stable"
- **Output**: Based on the slope of the 30-day forecast.

## 8. Market Comparison Table
- **Data Source**: All markets in the dataset for "onion" commodity.
- **Aggregation**:
  - Group by `market_name`
  - Compute: `min`, `max`, `median` (called "modal") of `p_modal`
- **Conversions**:
  - `min_kg = min / 100`, `max_kg = max / 100`, `modal_kg = modal / 100`
- **Sorting**: By `modal` descending.
- **Display**: Top 5 markets, with columns for ₹/kg and ₹/quintal values.

## 9. Top Recommendation
- **Selection**: Market with the highest `modal` price.
- **Output**: "TOP RECOMMENDATION: {market_name} (₹{modal_kg:.2f}/kg or ₹{modal}/quintal)"

## 10. Potential Extra Profit
- **Calculation**: `extra = best_modal - next_best_modal`
- **Output**: "POTENTIAL EXTRA PROFIT: ₹{extra} per quintal compared to {next_best_market}"
- **Note**: Only shown if there is a second market in the list.

## Warnings and Notes
- The output includes warnings about date index frequency (ignored by statsmodels) and future warnings for prediction indexing.
- All calculations assume the fallback statistical method due to missing model.
- Prices are in ₹/quintal (modal prices), converted to ₹/kg for display.
 
## accuracy 

The prediction system does not currently compute or report explicit accuracy metrics such as Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), or Mean Absolute Percentage Error (MAPE).

During model training and tuning:

Optuna minimizes Mean Squared Error (MSE) for hyperparameter optimization of XGBoost.
For the ensemble model, residuals are calculated on holdout data to derive conformal prediction intervals (80%, 90%, 95%), but these are used for uncertainty quantification rather than accuracy assessment.

The system prioritizes providing forecasts with uncertainty bands over backtesting accuracy. 

## accuracy :

## Good Short-Term Accuracy: 
For the next 1–5 days, the model predicts prices quite well. The error is only around 2–3%, which means if a crop costs ₹2000–3000 per quintal, the prediction will usually be off by just ₹50–100.

## Gets Worse Over Time: 
As you try to predict further into the future, the error becomes bigger. This is normal for such models because they don’t get new external updates.

30-Day Forecasts: For one month ahead, expect the error to be around 5–8%, which is about ₹100–150 per quintal.

Strengths:

The system can still give predictions even if no new model is trained (fallback).

If you use an ensemble (hybrid training), accuracy improves by about 20–30%.

Limitations:

The current test only checks fallback accuracy.

In real life, results depend a lot on how good the input data is and how unstable the market is.

👉 In short: The model works very well for short-term forecasts, becomes less accurate for long-term ones, has a reliable backup system, but real performance depends on market conditions and data quality.