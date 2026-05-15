import os
from utils import get_logger

logger = get_logger('prophet_wrapper')

def train_prophet(df, ds_col='date', y_col='p_modal', model_path=None, yearly=True, weekly=True):
    try:
        from prophet import Prophet
    except Exception:
        try:
            from fbprophet import Prophet
        except Exception:
            logger.error('prophet is not installed. Install prophet (or fbprophet) to use this wrapper.')
            raise

    df2 = df[[ds_col, y_col]].rename(columns={ds_col:'ds', y_col:'y'})
    m = Prophet(yearly_seasonality=yearly, weekly_seasonality=weekly, daily_seasonality=False)
    m.fit(df2)
    if model_path:
        m.save(model_path)
    logger.info(f'Prophet model trained and saved to {model_path}')
    return m

def load_prophet(model_path):
    try:
        from prophet.serialize import model_from_json
    except Exception:
        try:
            from fbprophet.serialize import model_from_json
        except Exception:
            logger.error('prophet serialize import failed. prophet may not be installed.')
            raise
    with open(model_path, 'r') as f:
        j = f.read()
    return model_from_json(j)

def predict_prophet(model, periods, freq='D'):
    future = model.make_future_dataframe(periods=periods, freq=freq)
    fcst = model.predict(future)
    return fcst[['ds','yhat','yhat_lower','yhat_upper']].tail(periods)
