#!/usr/bin/env python3
"""
Train Ensemble Models and Test Accuracy Improvement
==================================================

This script trains ensemble models for the best-performing market-commodity
combinations and compares accuracy with the fallback predictor.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_preprocessing import load_dataset, filter_telangana_hyderabad, preprocess_prices
from feature_engineering import prepare_features
from prediction_engine import predict_with_ensemble, predict_with_simple_ensemble, fallback_stats_predict
from model_training import train_stacked_ensemble
from utils import get_logger
from config import MODELS_DIR

logger = get_logger('ensemble_test')

def calculate_metrics(y_true, y_pred):
    """Calculate accuracy metrics"""
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return None
    
    mae = np.mean(np.abs(y_true_clean - y_pred_clean))
    rmse = np.sqrt(np.mean((y_true_clean - y_pred_clean) ** 2))
    mape = np.mean(np.abs((y_true_clean - y_pred_clean) / y_true_clean)) * 100
    
    ss_res = np.sum((y_true_clean - y_pred_clean) ** 2)
    ss_tot = np.sum((y_true_clean - np.mean(y_true_clean)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'r2': r2,
        'n_samples': len(y_true_clean)
    }

def train_and_test_combination(filename, market, commodity):
    """Train ensemble and test against fallback for a specific combination"""
    print(f"\n{'='*60}")
    print(f"TESTING: {commodity} in {market}")
    print(f"Dataset: {filename}")
    print(f"{'='*60}")
    
    try:
        # Load data
        df = load_dataset(filename)
        df = filter_telangana_hyderabad(df)
        df = preprocess_prices(df)
        df_feat = prepare_features(df)
        
        # Filter for specific market and commodity
        sub = df_feat[
            (df_feat['market_name'].str.lower().str.strip() == str(market).lower().strip()) & 
            (df_feat['cmdty'].str.lower().str.strip() == str(commodity).lower().strip())
        ].copy()
        
        if len(sub) < 100:
            print(f"❌ Insufficient data: {len(sub)} rows")
            return None
        
        print(f"📊 Total data points: {len(sub)}")
        
        # Split into train/test (80/20)
        split_point = int(len(sub) * 0.8)
        train_data = sub.iloc[:split_point]
        test_data = sub.iloc[split_point:]
        
        print(f"🔄 Train: {len(train_data)} rows, Test: {len(test_data)} rows")
        
        # Test fallback predictor
        print("\n1️⃣ Testing Fallback Predictor...")
        fallback_result = fallback_stats_predict(train_data, horizon=len(test_data))
        
        y_true = test_data['p_modal'].values
        y_pred_fallback = np.array(fallback_result['yhat'][:len(y_true)])
        
        fallback_metrics = calculate_metrics(y_true, y_pred_fallback)
        
        if fallback_metrics:
            print(f"   MAE: ₹{fallback_metrics['mae']:.2f}/quintal")
            print(f"   RMSE: ₹{fallback_metrics['rmse']:.2f}/quintal")
            print(f"   MAPE: {fallback_metrics['mape']:.1f}%")
            print(f"   R²: {fallback_metrics['r2']:.3f}")
        
        # Train ensemble model
        print("\n2️⃣ Training Ensemble Model...")
        X_train = train_data.drop(columns=['p_modal'], errors='ignore')
        y_train = train_data['p_modal']
        
        ensemble_path = train_stacked_ensemble(X_train, y_train, market, commodity)
        print(f"   ✅ Ensemble saved to: {ensemble_path}")
        
        # Test ensemble predictor
        print("\n3️⃣ Testing Ensemble Predictor...")
        
        # Ensure train_data has datetime index for ensemble prediction
        train_indexed = train_data.copy()
        if not isinstance(train_indexed.index, pd.DatetimeIndex):
            # Create a simple date range
            start_date = datetime(2021, 1, 1)
            train_indexed.index = pd.date_range(start=start_date, periods=len(train_indexed), freq='D')
        
        ensemble_result = predict_with_simple_ensemble(ensemble_path, train_indexed.tail(30), horizon=len(test_data))
        y_pred_ensemble = np.array(ensemble_result['yhat'][:len(y_true)])
        
        ensemble_metrics = calculate_metrics(y_true, y_pred_ensemble)
        
        if ensemble_metrics:
            print(f"   MAE: ₹{ensemble_metrics['mae']:.2f}/quintal")
            print(f"   RMSE: ₹{ensemble_metrics['rmse']:.2f}/quintal")
            print(f"   MAPE: {ensemble_metrics['mape']:.1f}%")
            print(f"   R²: {ensemble_metrics['r2']:.3f}")
        
        # Compare results
        if fallback_metrics and ensemble_metrics:
            print(f"\n📈 IMPROVEMENT ANALYSIS:")
            mae_improvement = ((fallback_metrics['mae'] - ensemble_metrics['mae']) / fallback_metrics['mae']) * 100
            rmse_improvement = ((fallback_metrics['rmse'] - ensemble_metrics['rmse']) / fallback_metrics['rmse']) * 100
            mape_improvement = ((fallback_metrics['mape'] - ensemble_metrics['mape']) / fallback_metrics['mape']) * 100
            
            print(f"   MAE Improvement: {mae_improvement:+.1f}%")
            print(f"   RMSE Improvement: {rmse_improvement:+.1f}%")
            print(f"   MAPE Improvement: {mape_improvement:+.1f}%")
            
            if mae_improvement > 0:
                print(f"   🎉 Ensemble is better by ₹{fallback_metrics['mae'] - ensemble_metrics['mae']:.2f}/quintal")
            else:
                print(f"   ⚠️  Fallback is better by ₹{ensemble_metrics['mae'] - fallback_metrics['mae']:.2f}/quintal")
        
        return {
            'market': market,
            'commodity': commodity,
            'data_points': len(sub),
            'fallback_metrics': fallback_metrics,
            'ensemble_metrics': ensemble_metrics
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Test ensemble training on best combinations"""
    print("🚀 ENSEMBLE TRAINING AND ACCURACY TEST")
    print("="*60)
    
    # Best combinations based on benchmark results
    test_combinations = [
        ('brinjal_price_data2021-2024.csv', 'Gudimalkapur', 'Brinjal'),
        ('onion_price_data2021-2024.csv', 'Mahboob Manison', 'Onion'),
        ('potato_price_data2021-2024.csv', 'Bowenpally', 'Potato'),
        ('greenchilli_price_data2021-2024.csv', 'Gudimalkapur', 'Green Chilli'),
        ('tomato_price_data2021-2024.csv', 'Bowenpally', 'Tomato')
    ]
    
    results = []
    
    for filename, market, commodity in test_combinations:
        result = train_and_test_combination(filename, market, commodity)
        if result:
            results.append(result)
    
    # Summary
    if results:
        print(f"\n{'='*60}")
        print("📊 SUMMARY OF ENSEMBLE vs FALLBACK COMPARISON")
        print(f"{'='*60}")
        
        improvements = []
        for result in results:
            if result['fallback_metrics'] and result['ensemble_metrics']:
                fallback_mae = result['fallback_metrics']['mae']
                ensemble_mae = result['ensemble_metrics']['mae']
                improvement = ((fallback_mae - ensemble_mae) / fallback_mae) * 100
                improvements.append(improvement)
                
                status = "✅ BETTER" if improvement > 0 else "❌ WORSE"
                print(f"{result['commodity']} in {result['market']}: {improvement:+.1f}% {status}")
        
        if improvements:
            avg_improvement = np.mean(improvements)
            print(f"\n🎯 AVERAGE IMPROVEMENT: {avg_improvement:+.1f}%")
            
            if avg_improvement > 0:
                print("🎉 Ensemble models show overall improvement!")
            else:
                print("⚠️  Ensemble models need further tuning")
        
        print(f"\n💡 Next steps:")
        print("   1. Fine-tune hyperparameters for poor-performing combinations")
        print("   2. Add more external features (weather, market events)")
        print("   3. Implement proper conformal prediction intervals")
        print("   4. Consider commodity-specific model architectures")

if __name__ == "__main__":
    main()