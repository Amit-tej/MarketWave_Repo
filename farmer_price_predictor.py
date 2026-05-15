import argparse
import os
import sys
from utils import get_logger
try:
    from importlib.metadata import version
except ImportError:
    # Fallback for older Python versions
    from importlib_metadata import version

# Check scikit-learn version
required_sklearn_version = '1.6.1'
try:
    sklearn_version = version('scikit-learn')
    if sklearn_version != required_sklearn_version:
        logger = get_logger('cli')
        logger.warning(f"Warning: scikit-learn version mismatch. Required: {required_sklearn_version}, Found: {sklearn_version}")
        logger.warning("Please run: pip install scikit-learn==1.6.1")
        sys.exit(1)
except Exception as e:
    pass

from data_preprocessing import load_dataset, filter_telangana_hyderabad, preprocess_prices
from feature_engineering import prepare_features
from terminal_interface import choose_from_list, show_calendar, ascii_sparkline, display_ranked_markets, show_progress
from model_training import train_simple_rf, train_stacked_ensemble
from prediction_engine import predict_with_ensemble, predict_with_simple_ensemble, fallback_stats_predict
import numpy as np
from market_comparison import market_recommendations
from market_comparison import top_recommendation_summary
import pandas as pd
from config import DATA_DIR, MODELS_DIR

logger = get_logger('cli')

def cmd_train(args):
    # Load CSV
    df = load_dataset(args.data)
    df = filter_telangana_hyderabad(df)
    df = preprocess_prices(df)
    df_feat = prepare_features(df)

    # For simplicity train on market+commodity provided or first found
    # case-insensitive matching for market and commodity
    def pick_case_insensitive(series, value):
        if value is None:
            return None
        s = series.astype(str)
        matches = s[s.str.lower().str.strip() == str(value).lower().strip()]
        return matches.iloc[0] if not matches.empty else None

    if args.market:
        market_match = pick_case_insensitive(df_feat['market_name'], args.market)
        market = market_match if market_match is not None else args.market
    else:
        market = df_feat['market_name'].iloc[0]

    if args.commodity:
        cmd_match = pick_case_insensitive(df_feat['cmdty'], args.commodity)
        commodity = cmd_match if cmd_match is not None else args.commodity
    else:
        commodity = df_feat['cmdty'].iloc[0]

    sub = df_feat[(df_feat['market_name'].str.lower().str.strip()==str(market).lower().strip()) & (df_feat['cmdty'].str.lower().str.strip()==str(commodity).lower().strip())]
    if sub.empty:
        logger.error('No data for specified market/commodity')
        return
    X = sub.drop(columns=['p_modal'], errors='ignore')
    y = sub['p_modal']
    path = train_stacked_ensemble(X, y, market, commodity)
    logger.info(f'Trained ensemble saved to {path}')

def cmd_hybrid_train(args):
    # Hybrid training harness using Optuna tuner
    try:
        from models.optuna_tuner import train_hybrid
    except Exception as e:
        logger.error('Optuna tuner not available or missing dependencies: ' + str(e))
        return
    # support training across all CSVs in dataset when --all is provided
    if getattr(args, 'all', False):
        # scan dataset dir for CSVs
        files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
        results = {}
        for fn in files:
            try:
                df = load_dataset(fn)
                df = filter_telangana_hyderabad(df)
                df = preprocess_prices(df)
                df_feat = prepare_features(df)
                market = df_feat['market_name'].iloc[0]
                commodity = df_feat['cmdty'].iloc[0]
                X = df_feat.drop(columns=['p_modal'], errors='ignore')
                y = df_feat['p_modal']
                res = train_hybrid(X, y, market, commodity)
                results[fn] = res
            except Exception as e:
                logger.error(f'Failed hybrid train for {fn}: {e}')
        logger.info(f'Batch hybrid training finished for files: {list(results.keys())}')
        return

    df = load_dataset(args.data)
    df = filter_telangana_hyderabad(df)
    df = preprocess_prices(df)
    df_feat = prepare_features(df)
    # case-insensitive matching
    def pick(series, value, default):
        if value:
            m = series[series.str.lower().str.strip() == str(value).lower().strip()]
            if not m.empty:
                return m.iloc[0]
            return value
        return default

    market = pick(df_feat['market_name'], args.market, df_feat['market_name'].iloc[0])
    commodity = pick(df_feat['cmdty'], args.commodity, df_feat['cmdty'].iloc[0])
    sub = df_feat[(df_feat['market_name'].str.lower().str.strip()==str(market).lower().strip()) & (df_feat['cmdty'].str.lower().str.strip()==str(commodity).lower().strip())]
    if sub.empty:
        logger.error('No data for specified market/commodity')
        return
    X = sub.drop(columns=['p_modal'], errors='ignore')
    y = sub['p_modal']
    res = train_hybrid(X, y, market, commodity)
    logger.info(f'Hybrid training finished, artifacts: {res}')

def cmd_predict(args):
    # Enforce horizon limit
    if args.horizon > 30:
        logger.warning(f'Horizon {args.horizon} exceeds maximum of 30 days. Please provide a value less than or equal to 30.')
        return
    elif args.horizon <= 0:
        logger.warning(
            f'Horizon {args.horizon} is not positive. '
            'Setting to a minimum horizon of 1 day.'
        )
        args.horizon = 1

    df = load_dataset(args.data)
    df = filter_telangana_hyderabad(df)
    df = preprocess_prices(df)
    df_feat = prepare_features(df)
    # accept case-insensitive values from args
    def pick_case_insensitive(series, value):
        if value is None:
            return None
        s = series.astype(str)
        matches = s[s.str.lower().str.strip() == str(value).lower().strip()]
        return matches.iloc[0] if not matches.empty else None

    market = None
    commodity = None
    if args.market:
        m = pick_case_insensitive(df_feat['market_name'], args.market)
        market = m if m is not None else args.market
    if args.commodity:
        c = pick_case_insensitive(df_feat['cmdty'], args.commodity)
        commodity = c if c is not None else args.commodity
    # interactive selection
    if market is None:
        markets = sorted(df_feat['market_name'].unique().tolist())
        market = choose_from_list('Choose a market', markets)
    if commodity is None:
        commodities = sorted(df_feat['cmdty'].unique().tolist())
        commodity = choose_from_list('Choose a commodity', commodities)
    sub = df_feat[(df_feat['market_name'].str.lower().str.strip()==str(market).lower().strip()) & (df_feat['cmdty'].str.lower().str.strip()==str(commodity).lower().strip())]
    if sub.empty:
        logger.error('No data for specified market/commodity')
        return
    X_last = sub.tail(1).drop(columns=['p_modal'], errors='ignore')
    # find ensemble model artifact; if missing use fallback stats predictor
    # ensure sub has a datetime index (handle 'date' or 't' columns)
    def _ensure_dt_index(df):
        df2 = df.copy()
        # if index already datetime, return
        if isinstance(df2.index, pd.DatetimeIndex):
            return df2
        # prefer explicit names
        for col in ('date','t','datetime','ds'):
            if col in df2.columns:
                df2[col] = pd.to_datetime(df2[col], errors='coerce')
                return df2.set_index(col)
        # try to infer from object columns
        for c in df2.columns:
            if df2[c].dtype == object:
                parsed = pd.to_datetime(df2[c], errors='coerce')
                if parsed.notna().sum() > 0.6 * len(parsed):
                    df2['date_inferred'] = parsed
                    return df2.set_index('date_inferred')
        # last resort: if any index-like values
        try:
            df2.index = pd.to_datetime(df2.index)
            return df2
        except Exception:
            raise KeyError('No datetime column found (expected "date" or "t" or a parseable column)')

    # Try several locations for an ensemble model to support per-market folders
    def _find_ensemble_model(commodity, market):
        # exact match in models/ (legacy location)
        candidate = os.path.join(MODELS_DIR, f'ensemble_{commodity}_{market}.joblib')
        if os.path.exists(candidate):
            return candidate

        # try sanitized market folder (spaces -> underscores)
        sanitized = str(market).replace(' ', '_').replace('/', '_').replace('', '_')
        candidate2 = os.path.join(MODELS_DIR, sanitized, f'ensemble_{commodity}_{market}.joblib')
        if os.path.exists(candidate2):
            return candidate2

        # scan models/ tree for a matching ensemble file (case-insensitive)
        # prefer files that contain both commodity and market tokens
        lower_commodity = str(commodity).lower()
        lower_market = str(market).lower().replace(' ', '')
        best_match = None
        for root, _, files in os.walk(MODELS_DIR):
            for fname in files:
                if not fname.lower().endswith('.joblib'):
                    continue
                fname_low = fname.lower()
                if lower_commodity in fname_low and lower_market in fname_low.replace(' ', ''):
                    # return first strong match
                    return os.path.join(root, fname)
                if lower_commodity in fname_low and best_match is None:
                    best_match = os.path.join(root, fname)

        # return best found or the original candidate (which may not exist)
        return best_match or candidate

    sub_dt = _ensure_dt_index(sub)
    model_path = _find_ensemble_model(commodity, market)
    if model_path and os.path.exists(model_path):
        logger.info(f'Using ensemble model: {model_path}')
        # Decide which prediction function to use based on ensemble contents
        try:
            import joblib as _joblib
            ensemble_obj = _joblib.load(model_path)
            # simple stacked ensemble created by train_stacked_ensemble uses keys 'm1','m2','meta'
            if isinstance(ensemble_obj, dict) and all(k in ensemble_obj for k in ('m1','m2','meta')):
                logger.info('Ensemble appears to be a simple stacked RF ensemble; using predict_with_simple_ensemble')
                res = predict_with_simple_ensemble(model_path, sub_dt, horizon=args.horizon)
            else:
                logger.info('Ensemble appears to be a complex hybrid ensemble; using predict_with_ensemble')
                res = predict_with_ensemble(model_path, sub_dt, horizon=args.horizon)
        except Exception as e:
            logger.warning(f'Failed to inspect ensemble file; falling back to complex predictor: {e}')
            res = predict_with_ensemble(model_path, sub_dt, horizon=args.horizon)
    else:
        logger.warning(f'Model not found: {model_path}; using fallback historical stats predictor')
        res = fallback_stats_predict(sub_dt, horizon=args.horizon)

    yhat = res.get('yhat', [])
    intervals = res.get('intervals', {})

     # display with calendar and sparkline
    show_calendar(horizon=args.horizon)
    spark = ascii_sparkline(yhat)
    print('Forecast sparkline:')
    print(spark)

    # If user requested a specific day index (1-based), summarize that day; otherwise show day-by-day condensed
    sel_day = args.day if hasattr(args, 'day') and args.day else None
    if sel_day:
        idx = int(sel_day) - 1
        if idx < 0 or idx >= len(yhat):
            logger.error('Selected day out of range')
            return
        p = yhat[idx]
        per_quintal = p if p is not None else float('nan')
        per_kg = per_quintal / 100.0 if per_quintal is not None else float('nan')
        i80 = intervals.get('80', [(None,None)]*len(yhat))[idx]
        print(f"\nPREDICTION SUMMARY FOR {commodity} IN {market} -- Day +{sel_day}\n")
        print('Per Kg Prices:')
        print(f'  Min Price: ₹{(i80[0]/100.0) if i80[0] is not None else 0:.2f}/kg')
        print(f'  Max Price: ₹{(i80[1]/100.0) if i80[1] is not None else 0:.2f}/kg')
        print(f'  Modal Price: ₹{per_kg:.2f}/kg')
        print('\nPer Quintal Prices:')
        print(f'  Min Price: ₹{(i80[0]) if i80[0] is not None else 0:.0f}/quintal')
        print(f'  Max Price: ₹{(i80[1]) if i80[1] is not None else 0:.0f}/quintal')
        print(f'  Modal Price: ₹{per_quintal if per_quintal is not None else 0:.0f}/quintal')
    else:
        print('\nDay-by-day:')
        for i,p in enumerate(yhat, start=1):
            per_quintal = p if p is not None else float('nan')
            per_kg = per_quintal / 100.0 if per_quintal is not None else float('nan')
            i80 = intervals.get('80', [(None,None)]*len(yhat))[i-1]
            print(f"  Day {i}: Modal ₹{per_kg:.2f}/kg (80% interval: ₹{i80[0]/100.0 if i80[0] else 0:.2f}-₹{i80[1]/100.0 if i80[1] else 0:.2f})")

   # Simple trend detection using linear slope over forecast
    try:
        x = np.arange(len(yhat))
        slope = np.polyfit(x, [v if v is not None and not np.isnan(v) else 0 for v in yhat], 1)[0]
        trend = '↗️ Increasing' if slope > 0.01 else ('↘️ Decreasing' if slope < -0.01 else '→ Stable')
    except Exception:
        trend = '→ Stable'
    print(f'\nTrend: {trend}')
    
    

    # Market comparison using predicted prices for each market
    try:
        predictions = {}
        min_prices = {}
        max_prices = {}
        
        comp = df_feat[df_feat['cmdty'].str.lower().str.strip()==str(commodity).lower().strip()]
        for mkt in comp['market_name'].unique():
            mkt_sub = df_feat[(df_feat['market_name'].str.lower().str.strip()==str(mkt).lower().strip()) & 
                            (df_feat['cmdty'].str.lower().str.strip()==str(commodity).lower().strip())]
            if not mkt_sub.empty:
                mkt_model_path = os.path.join(MODELS_DIR, f'ensemble_{commodity}_{mkt}.joblib')
                mkt_sub_dt = _ensure_dt_index(mkt_sub)
                
                try:
                    if os.path.exists(mkt_model_path):
                        # Use ensemble model if available
                        mkt_pred = predict_with_ensemble(mkt_model_path, mkt_sub_dt, horizon=args.horizon)
                    else:
                        # Use fallback predictor if no model exists
                        mkt_pred = fallback_stats_predict(mkt_sub_dt, horizon=args.horizon)
                except Exception as e:
                    logger.warning(f"Failed to predict for market {mkt}, using historical data")
                    # Fallback to historical statistics
                    mkt_pred = {
                        'yhat': [float(mkt_sub['p_modal'].median())] * args.horizon,
                        'intervals': {
                            '80': [(float(mkt_sub['p_modal'].quantile(0.1)), 
                                   float(mkt_sub['p_modal'].quantile(0.9)))] * args.horizon
                        }
                    }
                
                # Calculate average predicted price for the horizon
                yhat = mkt_pred.get('yhat', [])
                if yhat:
                    predictions[mkt] = np.mean(yhat)
                    min_prices[mkt] = min(yhat)
                    max_prices[mkt] = max(yhat)
                else:
                    # Fallback to historical if prediction fails
                    predictions[mkt] = mkt_sub['p_modal'].median()
                    min_prices[mkt] = mkt_sub['p_modal'].min()
                    max_prices[mkt] = mkt_sub['p_modal'].max()

        # Create DataFrame with predictions
        grp = pd.DataFrame([
            {'market_name': mkt, 
             'modal': pred,
             'min': min_prices[mkt],
             'max': max_prices[mkt]} 
            for mkt, pred in predictions.items()
        ])
        
        grp['min_kg'] = grp['min'] / 100.0
        grp['max_kg'] = grp['max'] / 100.0
        grp['modal_kg'] = grp['modal'] / 100.0
        grp = grp.sort_values('modal', ascending=False)
        
        print(f"\nCOMPARISON WITH OTHER MARKETS IN {market.split(',')[0].upper()} FOR {commodity.upper()} (modal shown):")
        # Print header with labels for each column
        header = f"{'Market':<25} | {'Min (₹/kg)':>10} | {'Max (₹/kg)':>10} | {'Modal (₹/kg)':>12} | {'Min (₹/qtl)':>12} | {'Max (₹/qtl)':>12} | {'Modal (₹/qtl)':>14}"
        sep = '-' * len(header)
        print(header)
        print(sep)
        
        for _, r in grp.head(5).iterrows():
            print(f"{r['market_name']:<25} | {r['min_kg']:10.2f} | {r['max_kg']:10.2f} | {r['modal_kg']:12.2f} | {int(r['min']):12d} | {int(r['max']):12d} | {int(r['modal']):14d}")
        
        if not grp.empty:
            best = grp.iloc[0]
            next_best = grp.iloc[1] if len(grp) > 1 else None
            extra = int(best['modal'] - (next_best['modal'] if next_best is not None else best['modal'])) if next_best is not None else 0
            print(f"\nTOP RECOMMENDATION: {best['market_name']} (₹{best['modal_kg']:.2f}/kg or ₹{int(best['modal'])}/quintal)")
            if next_best is not None:
                print(f"POTENTIAL EXTRA PROFIT: ₹{extra} per quintal compared to {next_best['market_name']}")

    except Exception as e:
        logger.error(f"Error in market comparison: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def cmd_compare(args):
    df = load_dataset(args.data)
    df = filter_telangana_hyderabad(df)
    df = preprocess_prices(df)
    ranked = market_recommendations(df)
    rows = ranked[['market_name','modal','volatility','category']].to_dict('records')
    display_ranked_markets(rows)


def cmd_top_summary(args):
    df = load_dataset(args.data)
    df = filter_telangana_hyderabad(df)
    df = preprocess_prices(df)
    res = top_recommendation_summary(df)
    print('\nTop market per commodity:')
    if res['per_commodity'].empty:
        print('  No commodity data found')
    else:
        for _, r in res['per_commodity'].iterrows():
            print(f"  {r['commodity']}: {r['top_market']} (modal={r['top_modal']})")
    print('\nOverall counts:')
    if res['overall'].empty:
        print('  No top recommendations computed')
    else:
        for _, r in res['overall'].iterrows():
            print(f"  {r['market_name']}: {int(r['count'])} commodities ({r['percent']:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Farmer Price Predictor')
    parser.add_argument('--data', default='brinjal_price_data2021-2024.csv', help='CSV data file in dataset/')
    sub = parser.add_subparsers(dest='mode')

    p_train = sub.add_parser('train')
    p_train.add_argument('--market')
    p_train.add_argument('--commodity')
    p_train.add_argument('--data', help='CSV data file in dataset/')
    p_train.set_defaults(func=cmd_train)

    p_hybrid = sub.add_parser('hybrid-train')
    p_hybrid.add_argument('--market')
    p_hybrid.add_argument('--commodity')
    p_hybrid.add_argument('--quick', action='store_true', help='Run a quick trial with fewer optuna trials and LSTM epochs')
    p_hybrid.add_argument('--all', action='store_true', help='Train across all CSV files in dataset/')
    p_hybrid.add_argument('--data', help='CSV data file in dataset/')
    p_hybrid.set_defaults(func=cmd_hybrid_train)

    p_pred = sub.add_parser('predict')
    p_pred.add_argument('--market')
    p_pred.add_argument('--commodity')
    p_pred.add_argument('--horizon', type=int, default=30)
    p_pred.add_argument('--day', type=int, help='Select a specific day index within the horizon (1-based)')
    p_pred.add_argument('--data', help='CSV data file in dataset/')
    p_pred.set_defaults(func=cmd_predict)

    p_comp = sub.add_parser('compare')
    p_comp.add_argument('--commodity', required=False)
    p_comp.add_argument('--data', help='CSV data file in dataset/')
    p_comp.set_defaults(func=cmd_compare)

    p_top = sub.add_parser('top-summary')
    p_top.add_argument('--data', help='CSV data file in dataset/')
    p_top.set_defaults(func=cmd_top_summary)

    p_pre = sub.add_parser('preflight')
    p_pre.add_argument('--data', help='CSV data file in dataset/')
    def _run_preflight(args):
        import preflight
        path = args.data if args.data and os.path.isabs(args.data) else os.path.join(DATA_DIR, args.data)
        info = preflight.run_preflight(path)
        import json
        print(json.dumps(info, indent=2))
    p_pre.set_defaults(func=_run_preflight)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
