#!/usr/bin/env python3
"""
Quick Accuracy Test for AgriWave
================================

This script runs a quick accuracy test using the fallback predictor
on your existing datasets to give you immediate accuracy metrics.
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
from prediction_engine import fallback_stats_predict
from utils import get_logger

logger = get_logger('quick_test')

def calculate_metrics(y_true, y_pred):
    """Calculate accuracy metrics"""
    # Remove NaN values
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

def test_dataset(filename):
    """Test accuracy on a single dataset"""
    print(f"\nTesting {filename}...")
    
    try:
        # Load data
        df = load_dataset(filename)
        df = filter_telangana_hyderabad(df)
        df = preprocess_prices(df)
        df_feat = prepare_features(df)
        
        # Get the most common market-commodity combination
        combo_counts = df_feat.groupby(['market_name', 'cmdty']).size()
        top_combo = combo_counts.idxmax()
        market, commodity = top_combo
        
        print(f"  Testing: {commodity} in {market}")
        
        # Filter data
        sub = df_feat[
            (df_feat['market_name'].str.lower().str.strip() == str(market).lower().strip()) & 
            (df_feat['cmdty'].str.lower().str.strip() == str(commodity).lower().strip())
        ].copy()
        
        if len(sub) < 60:
            print(f"  Insufficient data: {len(sub)} rows")
            return None
        
        # Split into train/test (80/20)
        split_point = int(len(sub) * 0.8)
        train_data = sub.iloc[:split_point]
        test_data = sub.iloc[split_point:]
        
        print(f"  Train: {len(train_data)} rows, Test: {len(test_data)} rows")
        
        # Make predictions
        result = fallback_stats_predict(train_data, horizon=len(test_data))
        
        # Calculate metrics
        y_true = test_data['p_modal'].values
        y_pred = np.array(result['yhat'][:len(y_true)])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        if metrics:
            print(f"  MAE: ₹{metrics['mae']:.2f}/quintal (₹{metrics['mae']/100:.2f}/kg)")
            print(f"  RMSE: ₹{metrics['rmse']:.2f}/quintal")
            print(f"  MAPE: {metrics['mape']:.1f}%")
            print(f"  R²: {metrics['r2']:.3f}")
            
            # Test interval coverage
            intervals = result.get('intervals', {}).get('80', [])
            if intervals:
                coverage_count = 0
                for i, (lower, upper) in enumerate(intervals[:len(y_true)]):
                    if lower is not None and upper is not None:
                        if lower <= y_true[i] <= upper:
                            coverage_count += 1
                coverage = (coverage_count / len(y_true)) * 100
                print(f"  80% Interval Coverage: {coverage:.1f}%")
        
        return metrics
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    """Run quick accuracy tests"""
    print("="*60)
    print("AGRIWAVE QUICK ACCURACY TEST")
    print("="*60)
    
    # Find all price datasets
    dataset_dir = 'dataset'
    csv_files = [f for f in os.listdir(dataset_dir) if f.endswith('_price_data2021-2024.csv')]
    
    if not csv_files:
        print("No price data files found!")
        return
    
    print(f"Found {len(csv_files)} datasets")
    
    all_metrics = []
    
    for filename in csv_files:
        metrics = test_dataset(filename)
        if metrics:
            all_metrics.append(metrics)
    
    # Summary
    if all_metrics:
        print(f"\n{'='*60}")
        print("SUMMARY ACROSS ALL DATASETS")
        print(f"{'='*60}")
        
        avg_mae = np.mean([m['mae'] for m in all_metrics])
        avg_rmse = np.mean([m['rmse'] for m in all_metrics])
        avg_mape = np.mean([m['mape'] for m in all_metrics])
        avg_r2 = np.mean([m['r2'] for m in all_metrics])
        
        print(f"Average MAE: ₹{avg_mae:.2f}/quintal (₹{avg_mae/100:.2f}/kg)")
        print(f"Average RMSE: ₹{avg_rmse:.2f}/quintal")
        print(f"Average MAPE: {avg_mape:.1f}%")
        print(f"Average R²: {avg_r2:.3f}")
        
        # Interpretation
        print(f"\nINTERPRETATION:")
        if avg_mape < 10:
            print("📈 EXCELLENT: Very accurate predictions")
        elif avg_mape < 20:
            print("✅ GOOD: Reasonably accurate predictions")
        elif avg_mape < 30:
            print("⚠️  FAIR: Moderate accuracy, room for improvement")
        else:
            print("❌ POOR: Low accuracy, needs model improvement")
        
        print(f"\nOn average, predictions are off by ₹{avg_mae:.2f} per quintal")
        print(f"That's about ₹{avg_mae/100:.2f} per kg or {avg_mape:.1f}% error")

if __name__ == "__main__":
    main()