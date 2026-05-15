#!/usr/bin/env python3
"""
Accuracy Benchmarking Script for AgriWave
==========================================

This script runs comprehensive accuracy benchmarks on your datasets including:
- Multiple accuracy metrics (MAE, RMSE, MAPE, R²)
- Time series cross-validation
- Fallback vs Ensemble model comparison
- Prediction interval coverage analysis
- Performance across commodities and markets
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_preprocessing import load_dataset, filter_telangana_hyderabad, preprocess_prices
from feature_engineering import prepare_features
from prediction_engine import predict_with_ensemble, fallback_stats_predict
from model_training import train_stacked_ensemble
from utils import get_logger
from config import DATA_DIR, MODELS_DIR

logger = get_logger('benchmark')

class AccuracyBenchmark:
    def __init__(self):
        self.results = {
            'benchmark_date': datetime.now().isoformat(),
            'datasets': {},
            'summary': {}
        }
        
    def calculate_metrics(self, y_true, y_pred, model_name=""):
        """Calculate comprehensive accuracy metrics"""
        # Remove NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]
        
        if len(y_true_clean) == 0:
            return {
                'mae': np.nan, 'rmse': np.nan, 'mape': np.nan, 
                'r2': np.nan, 'n_samples': 0
            }
        
        # Mean Absolute Error
        mae = np.mean(np.abs(y_true_clean - y_pred_clean))
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((y_true_clean - y_pred_clean) ** 2))
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_true_clean - y_pred_clean) / y_true_clean)) * 100
        
        # R-squared
        ss_res = np.sum((y_true_clean - y_pred_clean) ** 2)
        ss_tot = np.sum((y_true_clean - np.mean(y_true_clean)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan
        
        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'r2': float(r2),
            'n_samples': int(len(y_true_clean))
        }
    
    def calculate_interval_coverage(self, y_true, intervals, confidence_level=80):
        """Calculate prediction interval coverage"""
        if not intervals or len(intervals) == 0:
            return {'coverage': np.nan, 'width': np.nan}
            
        coverage_count = 0
        widths = []
        valid_count = 0
        
        for i, (lower, upper) in enumerate(intervals):
            if i >= len(y_true) or np.isnan(y_true[i]):
                continue
                
            if lower is not None and upper is not None and not (np.isnan(lower) or np.isnan(upper)):
                valid_count += 1
                if lower <= y_true[i] <= upper:
                    coverage_count += 1
                widths.append(upper - lower)
        
        coverage = (coverage_count / valid_count * 100) if valid_count > 0 else np.nan
        avg_width = np.mean(widths) if widths else np.nan
        
        return {
            'coverage': float(coverage),
            'width': float(avg_width),
            'valid_intervals': int(valid_count)
        }
    
    def time_series_cv_benchmark(self, df_feat, market, commodity, n_splits=3):
        """Perform time series cross-validation benchmark"""
        logger.info(f"Running time series CV for {commodity} in {market}")
        
        # Filter data for specific market and commodity
        sub = df_feat[
            (df_feat['market_name'].str.lower().str.strip() == str(market).lower().strip()) & 
            (df_feat['cmdty'].str.lower().str.strip() == str(commodity).lower().strip())
        ].copy()
        
        if len(sub) < 100:  # Need sufficient data for CV
            logger.warning(f"Insufficient data for {commodity} in {market}: {len(sub)} rows")
            return None
        
        # Sort by date
        if 'date' in sub.columns:
            sub = sub.sort_values('date')
        elif hasattr(sub.index, 'sort_values'):
            sub = sub.sort_index()
        
        results = {
            'fallback_metrics': [],
            'ensemble_metrics': [],
            'interval_coverage': []
        }
        
        # Time series split
        total_size = len(sub)
        test_size = total_size // (n_splits + 1)
        
        for fold in range(n_splits):
            train_end = total_size - (n_splits - fold) * test_size
            test_start = train_end
            test_end = test_start + test_size
            
            if test_end > total_size:
                test_end = total_size
            
            train_data = sub.iloc[:train_end].copy()
            test_data = sub.iloc[test_start:test_end].copy()
            
            if len(train_data) < 50 or len(test_data) < 10:
                continue
            
            logger.info(f"Fold {fold + 1}: Train={len(train_data)}, Test={len(test_data)}")
            
            # Prepare test data with datetime index
            test_indexed = self._ensure_dt_index(test_data)
            
            # Test fallback predictor
            try:
                fallback_result = fallback_stats_predict(train_data, horizon=len(test_data))
                y_true = test_data['p_modal'].values
                y_pred = np.array(fallback_result['yhat'][:len(y_true)])
                
                fallback_metrics = self.calculate_metrics(y_true, y_pred, "fallback")
                results['fallback_metrics'].append(fallback_metrics)
                
                # Test interval coverage
                intervals_80 = fallback_result.get('intervals', {}).get('80', [])
                coverage = self.calculate_interval_coverage(y_true, intervals_80, 80)
                results['interval_coverage'].append(coverage)
                
            except Exception as e:
                logger.error(f"Fallback prediction failed in fold {fold + 1}: {e}")
                continue
            
            # Test ensemble predictor (if model exists)
            model_path = os.path.join(MODELS_DIR, f'ensemble_{commodity}_{market}.joblib')
            if os.path.exists(model_path):
                try:
                    ensemble_result = predict_with_ensemble(model_path, train_data.tail(30), horizon=len(test_data))
                    y_pred_ensemble = np.array(ensemble_result['yhat'][:len(y_true)])
                    
                    ensemble_metrics = self.calculate_metrics(y_true, y_pred_ensemble, "ensemble")
                    results['ensemble_metrics'].append(ensemble_metrics)
                    
                except Exception as e:
                    logger.error(f"Ensemble prediction failed in fold {fold + 1}: {e}")
        
        return results
    
    def _ensure_dt_index(self, df):
        """Ensure DataFrame has datetime index"""
        df2 = df.copy()
        if isinstance(df2.index, pd.DatetimeIndex):
            return df2
        
        # Try to find date column
        for col in ('date', 't', 'datetime', 'ds'):
            if col in df2.columns:
                df2[col] = pd.to_datetime(df2[col], errors='coerce')
                return df2.set_index(col)
        
        # Try to parse index as datetime
        try:
            df2.index = pd.to_datetime(df2.index)
            return df2
        except Exception:
            # Create a simple date range
            start_date = datetime(2021, 1, 1)
            df2.index = pd.date_range(start=start_date, periods=len(df2), freq='D')
            return df2
    
    def benchmark_dataset(self, filename):
        """Benchmark a single dataset"""
        logger.info(f"Benchmarking dataset: {filename}")
        
        try:
            # Load and preprocess data
            df = load_dataset(filename)
            df = filter_telangana_hyderabad(df)
            df = preprocess_prices(df)
            df_feat = prepare_features(df)
            
            dataset_results = {
                'filename': filename,
                'total_rows': len(df),
                'processed_rows': len(df_feat),
                'markets': {},
                'commodities': list(df_feat['cmdty'].unique()),
                'market_names': list(df_feat['market_name'].unique())
            }
            
            # Get top markets and commodities by data volume
            market_commodity_counts = df_feat.groupby(['market_name', 'cmdty']).size().reset_index(name='count')
            top_combinations = market_commodity_counts.nlargest(5, 'count')
            
            for _, row in top_combinations.iterrows():
                market = row['market_name']
                commodity = row['cmdty']
                count = row['count']
                
                if count < 50:  # Skip if insufficient data
                    continue
                
                logger.info(f"Benchmarking {commodity} in {market} ({count} data points)")
                
                # Run time series CV
                cv_results = self.time_series_cv_benchmark(df_feat, market, commodity)
                
                if cv_results:
                    market_key = f"{market}_{commodity}"
                    dataset_results['markets'][market_key] = {
                        'market': market,
                        'commodity': commodity,
                        'data_points': int(count),
                        'cv_results': cv_results
                    }
            
            return dataset_results
            
        except Exception as e:
            logger.error(f"Failed to benchmark {filename}: {e}")
            return {
                'filename': filename,
                'error': str(e)
            }
    
    def run_full_benchmark(self):
        """Run benchmark on all available datasets"""
        logger.info("Starting comprehensive accuracy benchmark")
        
        # Get all price CSV files
        csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('_price_data2021-2024.csv')]
        
        if not csv_files:
            logger.error("No price data files found in dataset directory")
            return
        
        logger.info(f"Found {len(csv_files)} datasets to benchmark")
        
        for filename in csv_files:
            dataset_results = self.benchmark_dataset(filename)
            self.results['datasets'][filename] = dataset_results
        
        # Calculate summary statistics
        self._calculate_summary()
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
    
    def _calculate_summary(self):
        """Calculate summary statistics across all datasets"""
        all_fallback_metrics = []
        all_ensemble_metrics = []
        all_coverage_stats = []
        
        for dataset_name, dataset_data in self.results['datasets'].items():
            if 'error' in dataset_data:
                continue
                
            for market_key, market_data in dataset_data.get('markets', {}).items():
                cv_results = market_data.get('cv_results', {})
                
                # Collect fallback metrics
                for metrics in cv_results.get('fallback_metrics', []):
                    if not np.isnan(metrics.get('mae', np.nan)):
                        all_fallback_metrics.append(metrics)
                
                # Collect ensemble metrics
                for metrics in cv_results.get('ensemble_metrics', []):
                    if not np.isnan(metrics.get('mae', np.nan)):
                        all_ensemble_metrics.append(metrics)
                
                # Collect coverage stats
                for coverage in cv_results.get('interval_coverage', []):
                    if not np.isnan(coverage.get('coverage', np.nan)):
                        all_coverage_stats.append(coverage)
        
        # Calculate averages
        self.results['summary'] = {
            'total_datasets': len([d for d in self.results['datasets'].values() if 'error' not in d]),
            'total_market_commodity_pairs': sum(len(d.get('markets', {})) for d in self.results['datasets'].values() if 'error' not in d),
            'fallback_performance': self._average_metrics(all_fallback_metrics),
            'ensemble_performance': self._average_metrics(all_ensemble_metrics),
            'interval_coverage': self._average_coverage(all_coverage_stats)
        }
    
    def _average_metrics(self, metrics_list):
        """Calculate average metrics"""
        if not metrics_list:
            return {'mae': np.nan, 'rmse': np.nan, 'mape': np.nan, 'r2': np.nan, 'count': 0}
        
        return {
            'mae': float(np.mean([m['mae'] for m in metrics_list])),
            'rmse': float(np.mean([m['rmse'] for m in metrics_list])),
            'mape': float(np.mean([m['mape'] for m in metrics_list])),
            'r2': float(np.mean([m['r2'] for m in metrics_list])),
            'count': len(metrics_list)
        }
    
    def _average_coverage(self, coverage_list):
        """Calculate average coverage statistics"""
        if not coverage_list:
            return {'coverage': np.nan, 'width': np.nan, 'count': 0}
        
        return {
            'coverage': float(np.mean([c['coverage'] for c in coverage_list])),
            'width': float(np.mean([c['width'] for c in coverage_list])),
            'count': len(coverage_list)
        }
    
    def _save_results(self):
        """Save benchmark results to JSON file"""
        output_file = 'accuracy_benchmark_results.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Benchmark results saved to {output_file}")
    
    def _print_summary(self):
        """Print benchmark summary to console"""
        print("\n" + "="*80)
        print("AGRIWAVE ACCURACY BENCHMARK RESULTS")
        print("="*80)
        
        summary = self.results['summary']
        
        print(f"\nDatasets Processed: {summary['total_datasets']}")
        print(f"Market-Commodity Pairs: {summary['total_market_commodity_pairs']}")
        
        # Fallback performance
        fallback = summary['fallback_performance']
        if fallback['count'] > 0:
            print(f"\nFALLBACK MODEL PERFORMANCE (n={fallback['count']} tests):")
            print(f"  Mean Absolute Error (MAE): ₹{fallback['mae']:.2f}/quintal")
            print(f"  Root Mean Squared Error (RMSE): ₹{fallback['rmse']:.2f}/quintal")
            print(f"  Mean Absolute Percentage Error (MAPE): {fallback['mape']:.2f}%")
            print(f"  R-squared (R²): {fallback['r2']:.3f}")
        
        # Ensemble performance
        ensemble = summary['ensemble_performance']
        if ensemble['count'] > 0:
            print(f"\nENSEMBLE MODEL PERFORMANCE (n={ensemble['count']} tests):")
            print(f"  Mean Absolute Error (MAE): ₹{ensemble['mae']:.2f}/quintal")
            print(f"  Root Mean Squared Error (RMSE): ₹{ensemble['rmse']:.2f}/quintal")
            print(f"  Mean Absolute Percentage Error (MAPE): {ensemble['mape']:.2f}%")
            print(f"  R-squared (R²): {ensemble['r2']:.3f}")
            
            # Compare with fallback
            if fallback['count'] > 0:
                mae_improvement = ((fallback['mae'] - ensemble['mae']) / fallback['mae']) * 100
                rmse_improvement = ((fallback['rmse'] - ensemble['rmse']) / fallback['rmse']) * 100
                print(f"\nENSEMBLE vs FALLBACK IMPROVEMENT:")
                print(f"  MAE Improvement: {mae_improvement:.1f}%")
                print(f"  RMSE Improvement: {rmse_improvement:.1f}%")
        
        # Interval coverage
        coverage = summary['interval_coverage']
        if coverage['count'] > 0:
            print(f"\nPREDICTION INTERVAL PERFORMANCE (n={coverage['count']} tests):")
            print(f"  80% Interval Coverage: {coverage['coverage']:.1f}%")
            print(f"  Average Interval Width: ₹{coverage['width']:.2f}/quintal")
            
            # Coverage quality assessment
            if 75 <= coverage['coverage'] <= 85:
                coverage_quality = "EXCELLENT"
            elif 70 <= coverage['coverage'] <= 90:
                coverage_quality = "GOOD"
            else:
                coverage_quality = "NEEDS CALIBRATION"
            print(f"  Coverage Quality: {coverage_quality}")
        
        print("\n" + "="*80)
        print("Detailed results saved to: accuracy_benchmark_results.json")
        print("="*80)


def main():
    """Main function to run the benchmark"""
    benchmark = AccuracyBenchmark()
    benchmark.run_full_benchmark()


if __name__ == "__main__":
    main()