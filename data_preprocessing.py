import os
import pandas as pd
import numpy as np
from datetime import datetime
from utils import get_logger, cache_save, cache_load
from config import DATA_DIR

logger = get_logger('data_preprocessing')

def load_csv(path):
    logger.info(f'Loading CSV: {path}')
    # detect date-like column
    cols = pd.read_csv(path, nrows=0).columns
    date_col = None
    for c in cols:
        if c.lower() in ('date','date_time','datetime','timestamp','time','dt','t'):
            date_col = c
            break
    if date_col:
        df = pd.read_csv(path, parse_dates=[date_col])
        # normalize to 'date'
        if date_col != 'date':
            df = df.rename(columns={date_col: 'date'})
    else:
        # read without parse and try to infer
        df = pd.read_csv(path)
        # try to find any column with date-like values
        for c in df.columns:
            if df[c].dtype == object:
                try:
                    parsed = pd.to_datetime(df[c], errors='coerce')
                    if parsed.notna().sum() > 0.6 * len(parsed):
                        df['date'] = parsed
                        break
                except Exception:
                    continue
        if 'date' not in df.columns:
            logger.warning('No date column detected in CSV; proceeding without date parsing')
    return df

def load_dataset(filename):
    path = filename
    if not os.path.isabs(path):
        path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logger.error(f'File not found: {path}')
        raise FileNotFoundError(path)
    df = load_csv(path)
    return df

def filter_telangana_hyderabad(df):
    # Infer column names
    cols = df.columns.str.lower()
    # Try multiple possible column names
    if 'state_name' in cols:
        state_col = [c for c in df.columns if c.lower()=='state_name'][0]
    else:
        state_col = 'state_name'
    if 'district_name' in cols:
        dist_col = [c for c in df.columns if c.lower()=='district_name'][0]
    else:
        dist_col = 'district_name'

    df_f = df[df[state_col].str.lower().str.contains('telangana', na=False)]
    df_f = df_f[df_f[dist_col].str.lower().str.contains('hyderabad', na=False)]
    logger.info(f'Filtered to Telangana-Hyderabad: {len(df_f)} rows')
    return df_f

def preprocess_prices(df, price_cols=['p_min','p_max','p_modal']):
    df = df.copy()
    # Ensure date index
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

    # Fill missing prices using forward fill then interpolation
    df[price_cols] = df[price_cols].ffill().bfill().interpolate()

    # Winsorize outliers using IQR
    for col in price_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        df[col] = df[col].clip(lower, upper)

    return df
