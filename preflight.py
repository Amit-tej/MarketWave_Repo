import importlib.util
from utils import get_logger
import pandas as pd

logger = get_logger('preflight')

REQUIRED_COLUMNS = ['t','cmdty','market_name','p_modal']

def check_package(name):
    return importlib.util.find_spec(name) is not None

def run_preflight(path):
    info = {}
    try:
        df = pd.read_csv(path, nrows=5)
    except Exception as e:
        logger.error(f'Failed to read CSV: {e}')
        return {'ok': False, 'error': str(e)}

    cols = df.columns.tolist()
    info['columns'] = cols
    missing = [c for c in REQUIRED_COLUMNS if c not in cols]
    info['missing_required_columns'] = missing
    info['row_sample'] = df.head(3).to_dict(orient='records')

    # date parse test
    date_col = None
    for c in cols:
        if c.lower() in ('t','date','datetime','timestamp'):
            date_col = c
            break
    if date_col:
        try:
            parsed = pd.to_datetime(pd.read_csv(path, usecols=[date_col])[date_col], errors='coerce')
            info['date_parsed_count'] = int(parsed.notna().sum())
            info['date_total_count'] = int(len(parsed))
        except Exception as e:
            info['date_parse_error'] = str(e)
    else:
        info['date_parsed_count'] = 0

    # simple stats
    try:
        full = pd.read_csv(path)
        info['rows'] = len(full)
        info['unique_markets'] = int(full['market_name'].nunique()) if 'market_name' in full.columns else 0
        info['unique_commodities'] = int(full['cmdty'].nunique()) if 'cmdty' in full.columns else 0
    except Exception:
        pass

    # check packages
    pkgs = ['xgboost','optuna','prophet','tensorflow','lightgbm','catboost']
    info['packages'] = {p: check_package(p) for p in pkgs}

    info['ok'] = len(missing) == 0 and info.get('rows',0) > 0
    return info
