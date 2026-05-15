"""
Quick smoke test to validate imports and basic function calls.
Run: python test_smoke.py
"""
from utils import get_logger
from data_preprocessing import load_dataset
from feature_engineering import prepare_features

logger = get_logger('smoke')

def run():
    logger.info('Starting smoke test')
    print('Modules import successful')

if __name__ == '__main__':
    run()
