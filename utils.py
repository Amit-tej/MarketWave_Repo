import os
import joblib
import logging
from datetime import datetime
from config import CACHE_DIR

def get_logger(name=__name__, level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.handlers:
        ch = logging.StreamHandler()
        fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    logger.setLevel(level)
    return logger

def cache_save(obj, name):
    path = os.path.join(CACHE_DIR, name)
    joblib.dump(obj, path)
    return path

def cache_load(name):
    path = os.path.join(CACHE_DIR, name)
    if os.path.exists(path):
        return joblib.load(path)
    return None
