import os
from utils import get_logger

logger = get_logger('xgboost_wrapper')

def train_xgboost(X, y, model_path, params=None, num_round=100):
    try:
        import xgboost as xgb
    except Exception as e:
        logger.error('xgboost is not installed. Install xgboost to train this model.')
        raise

    # preprocess: convert object/category columns to numeric codes so DMatrix accepts them
    X_proc = X.copy()
    for c in X_proc.select_dtypes(include=['object', 'category']).columns:
        X_proc[c] = X_proc[c].astype('category').cat.codes.replace(-1, None)

    dtrain = xgb.DMatrix(X_proc, label=y)
    params = params or {'objective':'reg:squarederror', 'tree_method':'hist', 'verbosity':0}
    booster = xgb.train(params, dtrain, num_boost_round=num_round)
    booster.save_model(model_path)
    logger.info(f'XGBoost model saved to {model_path}')
    return model_path

def load_xgboost(model_path):
    try:
        import xgboost as xgb
    except Exception:
        logger.error('xgboost is not installed.')
        raise
    model = xgb.Booster()
    model.load_model(model_path)
    return model

def predict_xgboost(model, X):
    import xgboost as xgb
    X_proc = X.copy()
    for c in X_proc.select_dtypes(include=['object', 'category']).columns:
        X_proc[c] = X_proc[c].astype('category').cat.codes.replace(-1, None)
    d = xgb.DMatrix(X_proc)
    return model.predict(d)
