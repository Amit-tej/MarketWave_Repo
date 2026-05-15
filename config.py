import os

# Paths
ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, 'dataset')
MODELS_DIR = os.path.join(ROOT, 'models')
CACHE_DIR = os.path.join(ROOT, 'cache')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Training hyperparameters (defaults)
HYPER = {
    'optuna_trials': 20,
    'lstm_epochs': 5,
    'random_state': 42,
}

# Field name mapping (full names)
FIELD_MAP = {
    't': 'Date',
    'cmdty': 'Commodity',
    'market_id': 'Market ID',
    'market_name': 'Market Name',
    'state_id': 'State ID',
    'state_name': 'State Name',
    'district_id': 'District ID',
    'district_name': 'District Name',
    'variety': 'Commodity Variety',
    'p_min': 'Minimum Price (₹/quintal)',
    'p_max': 'Maximum Price (₹/quintal)',
    'p_modal': 'Modal Price (₹/quintal)'
}
