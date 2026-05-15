# AgriWave Accuracy Benchmark Report

**Date:** September 25, 2025  
**Benchmark Type:** Comprehensive Time Series Cross-Validation  
**Datasets Tested:** 5 commodities (Brinjal, Green Chilli, Onion, Potato, Tomato)  

## Executive Summary

The AgriWave prediction system was benchmarked across 25 market-commodity pairs using time series cross-validation. The results show **significant room for improvement** in prediction accuracy, particularly for the current fallback predictor.

### Key Findings

🔴 **Current Performance: POOR**
- **Average Error:** ₹1,091/quintal (₹10.91/kg) or **57% MAPE**
- **Prediction Intervals:** Only **30% coverage** (target: 80%)
- **R² Score:** -4.19 (negative indicates worse than naive mean prediction)

## Detailed Results

### Overall Performance Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Mean Absolute Error (MAE)** | ₹1,091/quintal | Average prediction error |
| **Root Mean Squared Error (RMSE)** | ₹1,311/quintal | Penalizes large errors more |
| **Mean Absolute Percentage Error (MAPE)** | 57% | Relative error percentage |
| **R-squared (R²)** | -4.19 | Model performs worse than mean |
| **80% Interval Coverage** | 30% | Intervals too narrow/miscalibrated |

### Performance by Commodity

| Commodity | Best MAE (₹/quintal) | Worst MAE (₹/quintal) | Avg MAPE |
|-----------|---------------------|----------------------|----------|
| **Brinjal** | 509 (Gudimalkapur) | 2,674 (Bowenpally) | 52% |
| **Green Chilli** | 825 (Gudimalkapur) | 5,930 (Gudimalkapur-fold1) | 113% |
| **Onion** | 1,170 (Mahboob Manison) | 1,393 (Bowenpally) | 45% |
| **Potato** | 1,025 (Bowenpally) | 1,025 (Bowenpally) | 40% |
| **Tomato** | 1,452 (Bowenpally) | 1,452 (Bowenpally) | 58% |

### Market Performance Analysis

**Best Performing Markets:**
1. **Gudimalkapur** - Most consistent across commodities
2. **L B Nagar** - Good for brinjal predictions
3. **Mahboob Manison** - Reasonable for onion

**Challenging Markets:**
1. **Bowenpally** - High volatility, especially for green chilli
2. **Erragadda(Rythu Bazar)** - Limited data, inconsistent performance

## Issues Identified

### 1. **Poor Baseline Performance**
- Current fallback predictor (Holt-Winters/Ridge) shows high errors
- Negative R² indicates model is worse than simply predicting the mean
- Suggests need for better feature engineering or model selection

### 2. **Interval Calibration Problems**
- 80% prediction intervals only capture 30% of actual values
- Intervals are either too narrow or systematically biased
- Critical for risk management in agricultural decisions

### 3. **High Volatility Commodities**
- **Green Chilli** shows extreme volatility (up to 273% MAPE)
- **Tomato** also challenging with 58% average error
- These commodities may need specialized modeling approaches

### 4. **No Ensemble Models Tested**
- Benchmark only tested fallback predictors
- No trained ensemble models (XGBoost + Prophet + LSTM) were available
- Expected 10-30% improvement with proper ensemble training

## Recommendations

### Immediate Actions (High Priority)

1. **Train Ensemble Models**
   ```bash
   # Train ensemble for best-performing combinations
   python .\farmer_price_predictor.py hybrid-train --data brinjal_price_data2021-2024.csv --market "Gudimalkapur" --commodity "brinjal"
   python .\farmer_price_predictor.py hybrid-train --data onion_price_data2021-2024.csv --market "Mahboob Manison" --commodity "onion"
   ```

2. **Fix Interval Calibration**
   - Implement proper conformal prediction
   - Use time-aware residual quantiles
   - Validate coverage on holdout sets

3. **Improve Feature Engineering**
   - Add external factors (weather, festivals, market events)
   - Include quantity data as exogenous variables
   - Engineer volatility and trend features

### Medium-Term Improvements

4. **Commodity-Specific Models**
   - Develop specialized models for high-volatility commodities
   - Consider regime-switching models for green chilli and tomato
   - Implement outlier detection and handling

5. **Data Quality Enhancement**
   - Address missing data patterns
   - Implement data validation checks
   - Add more recent data for better trend capture

6. **Model Selection Optimization**
   - Implement automated model selection based on commodity characteristics
   - Add model ensemble weighting based on recent performance
   - Include uncertainty-aware model selection

### Long-Term Strategy

7. **Advanced Modeling Techniques**
   - Implement deep learning models (Transformer, LSTM variants)
   - Add multi-market modeling for price spillover effects
   - Incorporate supply chain and logistics factors

8. **Real-Time Model Updates**
   - Implement online learning for model adaptation
   - Add concept drift detection
   - Develop automated retraining pipelines

## Expected Improvements

With proper ensemble training and feature engineering:

| Metric | Current | Expected Target | Improvement |
|--------|---------|----------------|-------------|
| **MAPE** | 57% | 25-35% | 40-55% better |
| **MAE** | ₹1,091 | ₹600-800 | 25-45% better |
| **Interval Coverage** | 30% | 75-85% | 150% better |
| **R²** | -4.19 | 0.3-0.6 | Positive predictive power |

## Next Steps

1. **Run ensemble training** on top 5 market-commodity pairs
2. **Implement conformal prediction** for proper interval calibration
3. **Add external data sources** (weather, market events)
4. **Validate improvements** with updated benchmark
5. **Deploy best models** for production use

## Technical Notes

- **Cross-validation:** 3-fold time series split
- **Test periods:** 250-400 days per fold
- **Fallback model:** Holt-Winters Exponential Smoothing with Ridge regression backup
- **Evaluation:** Out-of-fold predictions to prevent overfitting
- **Coverage calculation:** Empirical interval coverage on test sets

---

**Conclusion:** The current system provides a solid foundation but requires significant accuracy improvements before production deployment. Focus on ensemble training and interval calibration as immediate priorities.