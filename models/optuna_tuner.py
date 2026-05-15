import os
import numpy as np
from utils import get_logger
from config import MODELS_DIR, HYPER

logger = get_logger('optuna_tuner')

def tune_xgboost(X, y, n_trials=20):
    try:
        import optuna
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error
    except Exception:
        logger.error('Optuna and xgboost are required for tuning. Install them to use tuner.')
        raise

    Xtr, Xval, ytr, yval = train_test_split(X, y, test_size=0.2, random_state=HYPER['random_state'])

    def objective(trial):
        param = {
            'objective':'reg:squarederror',
            'tree_method':'hist',
            'eta': trial.suggest_loguniform('eta', 0.01, 0.3),
            'max_depth': trial.suggest_int('max_depth', 3, 12),
            'subsample': trial.suggest_uniform('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_uniform('colsample_bytree', 0.5, 1.0),
            'lambda': trial.suggest_loguniform('lambda', 1e-3, 10.0)
        }
        # convert any object/category columns to numeric codes to avoid DMatrix dtype errors
        def _preproc(df):
            df2 = df.copy()
            # convert string-like columns to categorical codes
            for c in df2.select_dtypes(include=['object', 'category']).columns:
                df2[c] = df2[c].astype('category').cat.codes.replace(-1, np.nan)
            return df2

        Xtr_proc = _preproc(Xtr)
        Xval_proc = _preproc(Xval)

        dtrain = xgb.DMatrix(Xtr_proc, label=ytr)
        dval = xgb.DMatrix(Xval_proc, label=yval)
        bst = xgb.train(param, dtrain, num_boost_round=100, evals=[(dval,'eval')], verbose_eval=False)
        preds = bst.predict(dval)
        mse = mean_squared_error(yval, preds)
        return mse

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=n_trials)
    logger.info(f'Best params: {study.best_params}')
    return study.best_params

def train_hybrid(X, y, market, commodity, tmp_dir=MODELS_DIR):
    # Tune XGBoost
    best = tune_xgboost(X, y, n_trials=min(HYPER.get('optuna_trials',20), 20))
    from models.xgboost_wrapper import train_xgboost
    xgb_path = os.path.join(tmp_dir, f'xgb_{commodity}_{market}.model')
    train_xgboost(X, y, xgb_path, params=best, num_round=200)

    # Train Prophet
    try:
        from models.prophet_wrapper import train_prophet
        p_path = os.path.join(tmp_dir, f'prophet_{commodity}_{market}.json')
        # requires df with date and p_modal - assume calling function saves appropriate df
    except Exception:
        logger.warning('Prophet not available; skipping prophet training')
        p_path = None

    # Train LSTM (placeholder)
    try:
        from models.lstm_wrapper import build_lstm, train_lstm
        lstm_path = os.path.join(tmp_dir, f'lstm_{commodity}_{market}.h5')
    except Exception:
        logger.warning('TensorFlow not available; skipping LSTM training')
        lstm_path = None

    return {'xgb': xgb_path, 'prophet': p_path, 'lstm': lstm_path}
