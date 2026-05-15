import os
import joblib
import numpy as np
import pandas as pd
from utils import get_logger
from config import MODELS_DIR, HYPER

logger = get_logger('hybrid_trainer')

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def train_hybrid_full(df, market, commodity, horizon=30, optuna_trials=100, lstm_epochs=20):
    """
    Full hybrid training pipeline (XGBoost with Optuna, Prophet, LSTM) producing stacked meta models per-horizon.
    Saves ensemble to MODELS_DIR/ensemble_{commodity}_{market}.joblib
    """
    _ensure_dir(MODELS_DIR)

    # Filter data for market and commodity
    sdf = df[(df.get('market_name')==market) & (df.get('cmdty')==commodity)].sort_values('date')
    if sdf.empty:
        raise ValueError('No data for market/commodity')

    sdf = sdf.reset_index(drop=True)
    # require at least 2 * horizon samples
    if len(sdf) < max(60, horizon*3):
        logger.warning('Dataset is small; results may be poor')

    # Prepare features (we'll use prepare_features externally) but for base models we'll use simple inputs
    # Split train/holdout (time-based)
    n = len(sdf)
    split = int(n*0.8)
    train_df = sdf.iloc[:split].copy()
    hold_df = sdf.iloc[split:].copy()

    # --- Train XGBoost (one-step recursive model) ---
    xgb_path = os.path.join(MODELS_DIR, f'xgb_{commodity}_{market}.model')
    try:
        from models.optuna_tuner import tune_xgboost
        from models.xgboost_wrapper import train_xgboost, load_xgboost
    except Exception as e:
        logger.error('xgboost/optuna components missing: ' + str(e))
        raise

    # Build training matrix: features from prepare_features
    from feature_engineering import prepare_features
    train_feat = prepare_features(train_df.set_index('date'))
    # Align X and y for next-day prediction
    X_train = train_feat.drop(columns=['p_modal'], errors='ignore')
    y_train = train_feat['p_modal'].shift(-1).dropna()
    X_train = X_train.loc[y_train.index]

    best_params = tune_xgboost(X_train, y_train, n_trials=min(optuna_trials, HYPER.get('optuna_trials',100)))
    train_xgboost(X_train, y_train, xgb_path, params=best_params, num_round=200)
    xgb_model = load_xgboost(xgb_path)

    # --- Train Prophet ---
    try:
        from models.prophet_wrapper import train_prophet
        p_path = os.path.join(MODELS_DIR, f'prophet_{commodity}_{market}.json')
        prophet_model = train_prophet(train_df.rename(columns={'date':'date'}), ds_col='date', y_col='p_modal', model_path=p_path)
    except Exception as e:
        logger.warning('Prophet training skipped: ' + str(e))
        prophet_model = None
        p_path = None

    # --- Train LSTM on p_modal series ---
    try:
        from models.lstm_wrapper import build_lstm, train_lstm, load_lstm_weights
        from sklearn.preprocessing import MinMaxScaler
        lstm_path = os.path.join(MODELS_DIR, f'lstm_{commodity}_{market}.h5')
        seq_len = 30
        series = train_df['p_modal'].values.reshape(-1,1)
        scaler = MinMaxScaler()
        series_s = scaler.fit_transform(series)
        Xs = []
        ys = []
        for i in range(len(series_s)-seq_len):
            Xs.append(series_s[i:i+seq_len,0])
            ys.append(series_s[i+seq_len,0])
        Xs = np.array(Xs)
        ys = np.array(ys)
        Xs = Xs.reshape((Xs.shape[0], Xs.shape[1], 1))
        lstm_model = build_lstm(input_shape=(seq_len,1))
        train_lstm(lstm_model, Xs, ys, lstm_path, epochs=max(1,lstm_epochs), batch_size=32)
        # save scaler
        joblib.dump(scaler, lstm_path + '.scaler')
    except Exception as e:
        logger.warning('LSTM training skipped: ' + str(e))
        lstm_model = None
        lstm_path = None

    # --- Create meta training data using holdout and recursive forecasts from base models ---
    logger.info('Generating meta training data using holdout forecasts')
    meta_rows = []
    # we need a prediction function using trained base models
    from models.xgboost_wrapper import predict_xgboost, load_xgboost as load_xgb
    try:
        from models.prophet_wrapper import predict_prophet
    except Exception:
        predict_prophet = None
    try:
        from models.lstm_wrapper import load_lstm_weights
    except Exception:
        load_lstm_weights = None

    # ensure hold_df has date index
    hold_df = hold_df.reset_index(drop=True)
    # For each origin in holdout where origin + horizon exists
    for i in range(0, len(hold_df)-horizon):
        origin_idx = split + i
        origin_date = sdf.loc[origin_idx, 'date']
        # initial last known p_modal is value at origin
        last_known = float(sdf.loc[origin_idx, 'p_modal'])
        # prepare a copy of features for XGBoost; use prepare_features single-row
        feat_row = prepare_features(sdf.loc[:origin_idx].set_index('date')).iloc[-1:]

        # recursive forecasts
        xgb_preds = []
        prop_preds = []
        lstm_preds = []
        # for prophet, we can ask for future from model if available starting at origin_date
        if prophet_model is not None:
            try:
                pfc = prophet_model.predict(prophet_model.make_future_dataframe(periods=horizon, freq='D'))
                # find values corresponding to dates > last train date
                pvals = pfc[['ds','yhat']].tail(horizon)['yhat'].values.tolist()
            except Exception:
                pvals = [np.nan]*horizon
        else:
            pvals = [np.nan]*horizon

        # LSTM initial sequence
        if lstm_model is not None:
            try:
                scaler = joblib.load(lstm_path + '.scaler')
                # build sequence from last seq_len p_modal values up to origin
                seq = sdf.loc[max(0, origin_idx-seq_len+1):origin_idx, 'p_modal'].values
                if len(seq) < seq_len:
                    seq = np.pad(seq, (seq_len-len(seq),0), 'edge')
                seq_s = scaler.transform(seq.reshape(-1,1)).reshape(1,seq_len,1)
                # iterative predict
                sseq = seq_s.copy()
                for k in range(horizon):
                    p = float(lstm_model.predict(sseq)[0,0])
                    p_raw = scaler.inverse_transform([[p]])[0,0]
                    lstm_preds.append(p_raw)
                    # append p to sseq
                    new = np.append(sseq[0,1:,0], p)
                    sseq = new.reshape(1,seq_len,1)
            except Exception:
                lstm_preds = [np.nan]*horizon
        else:
            lstm_preds = [np.nan]*horizon

        # XGBoost recursive using predict_xgboost
        try:
            # prepare X row for xgboost: drop p_modal
            xrow = feat_row.drop(columns=['p_modal'], errors='ignore')
            xrow_local = xrow.copy()
            last = last_known
            for k in range(horizon):
                # set p_modal in xrow_local if exists
                if 'p_modal' in xrow_local.columns:
                    xrow_local['p_modal'] = last
                pred = predict_xgboost(xgb_model, xrow_local)[0]
                xgb_preds.append(pred)
                last = pred
        except Exception:
            xgb_preds = [np.nan]*horizon

        # assemble meta rows for each horizon
        for h in range(horizon):
            obs_idx = origin_idx + h + 1
            if obs_idx >= len(sdf):
                break
            actual = float(sdf.loc[obs_idx, 'p_modal'])
            row = {
                'origin_date': origin_date,
                'horizon': h+1,
                'xgb': xgb_preds[h] if h < len(xgb_preds) else np.nan,
                'prophet': pvals[h] if h < len(pvals) else np.nan,
                'lstm': lstm_preds[h] if h < len(lstm_preds) else np.nan,
                'y': actual
            }
            meta_rows.append(row)

    meta_df = pd.DataFrame(meta_rows).dropna()
    if meta_df.empty:
        raise RuntimeError('No meta training rows generated; check data/model availability')

    # Train meta models per horizon
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    meta_models = {}
    for h in sorted(meta_df['horizon'].unique()):
        sub = meta_df[meta_df['horizon']==h]
        X_meta = sub[['xgb','prophet','lstm']].fillna(0)
        y_meta = sub['y']
        meta = LinearRegression()
        meta.fit(X_meta, y_meta)
        meta_models[int(h)] = meta

    # Compute residuals for conformal intervals using meta_df predictions
    preds = []
    for idx, r in meta_df.iterrows():
        m = meta_models[int(r['horizon'])]
        fv = np.array([[r['xgb'] if not np.isnan(r['xgb']) else 0,
                        r['prophet'] if not np.isnan(r['prophet']) else 0,
                        r['lstm'] if not np.isnan(r['lstm']) else 0]])
        preds.append(float(m.predict(fv)[0]))
    residuals = np.abs(meta_df['y'].values - np.array(preds))
    # quantiles for 80/90/95
    q80 = np.quantile(residuals, 0.8)
    q90 = np.quantile(residuals, 0.9)
    q95 = np.quantile(residuals, 0.95)

    ensemble = {
        'xgb_path': xgb_path,
        'prophet_path': p_path,
        'lstm_path': lstm_path,
        'meta_models': meta_models,
        'conformal': {'q80': float(q80), 'q90': float(q90), 'q95': float(q95)},
        'seq_len': 30
    }

    ensemble_path = os.path.join(MODELS_DIR, f'ensemble_{commodity}_{market}.joblib')
    joblib.dump(ensemble, ensemble_path)
    logger.info(f'Ensemble saved to {ensemble_path}')
    return ensemble_path
