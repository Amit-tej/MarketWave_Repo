import os
from utils import get_logger

logger = get_logger('lstm_wrapper')

def build_lstm(input_shape, units=[100,50,25], dropout=0.3):
    try:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.callbacks import EarlyStopping
    except Exception:
        logger.error('TensorFlow is not installed. Install tensorflow to use LSTM wrapper.')
        raise

    model = Sequential()
    for i, u in enumerate(units):
        return_sequences = i < (len(units)-1)
        if i == 0:
            model.add(LSTM(u, return_sequences=return_sequences, input_shape=input_shape))
        else:
            model.add(LSTM(u, return_sequences=return_sequences))
        model.add(Dropout(dropout))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model

def train_lstm(model, X, y, model_path, epochs=10, batch_size=32):
    from tensorflow.keras.callbacks import EarlyStopping
    es = EarlyStopping(patience=5, restore_best_weights=True)
    model.fit(X, y, epochs=epochs, batch_size=batch_size, callbacks=[es])
    # save weights
    model.save_weights(model_path)
    logger.info(f'LSTM weights saved to {model_path}')
    return model_path

def load_lstm_weights(model, model_path):
    model.load_weights(model_path)
    return model
