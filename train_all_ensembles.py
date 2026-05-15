#!/usr/bin/env python3
"""Batch train stacked ensembles for all commodities and markets.

Creates models under models/<sanitized_market>/ensemble_<Commodity>_<Market>.joblib

By default the script runs in --dry-run mode which only lists valid combinations.
Run without --dry-run to actually train (may take long).
"""
import os
import argparse
import shutil
from pathlib import Path
from utils import get_logger
from data_preprocessing import load_dataset, preprocess_prices
from feature_engineering import prepare_features
from model_training import train_stacked_ensemble
from config import DATA_DIR, MODELS_DIR

logger = get_logger('train_all_ensembles')


def sanitize_name(s: str) -> str:
    # safe folder/file name
    return str(s).strip().replace('/', '_').replace('\\', '_').replace(' ', '_')


def find_dataset_files(patterns=None):
    p = Path(DATA_DIR)
    files = []
    if patterns:
        for pat in patterns:
            files.extend(list(p.glob(pat)))
    else:
        files.extend(list(p.glob('*.csv')))
    return [str(f) for f in sorted(files)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-rows', type=int, default=100, help='Minimum rows required to train for a market+commodity')
    ap.add_argument('--dry-run', action='store_true', default=True, help='If set, only list combinations (default True)')
    ap.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='Disable dry-run and actually train')
    ap.add_argument('--files', nargs='*', help='Specific dataset files (relative to dataset/) to process')
    ap.add_argument('--limit', type=int, default=None, help='Limit number of combinations to train (for quick runs)')
    args = ap.parse_args(argv)

    logger.info('Scanning dataset files...')
    if args.files:
        dataset_files = [os.path.join(DATA_DIR, f) if not os.path.isabs(f) else f for f in args.files]
    else:
        dataset_files = find_dataset_files()

    if not dataset_files:
        logger.error('No dataset files found in dataset/; nothing to do')
        return

    combos = []
    for fn in dataset_files:
        try:
            df = load_dataset(fn)
        except Exception as e:
            logger.warning(f'Skipping {fn}: {e}')
            continue

        # basic preprocess
        try:
            df = preprocess_prices(df)
        except Exception:
            # allow continue even if preprocess fails
            pass

        # prepare features
        try:
            feat = prepare_features(df.copy())
        except Exception as e:
            logger.warning(f'Feature preparation failed for {fn}: {e}')
            feat = df.copy()

        # ensure columns
        if 'market_name' not in feat.columns or 'cmdty' not in feat.columns or 'p_modal' not in feat.columns:
            logger.debug(f'File {fn} missing required columns; skipping')
            continue

        for market in feat['market_name'].dropna().unique():
            for cmd in feat['cmdty'].dropna().unique():
                sub = feat[(feat['market_name'].str.lower().str.strip() == str(market).lower().strip()) &
                           (feat['cmdty'].str.lower().str.strip() == str(cmd).lower().strip())]
                if len(sub) >= args.min_rows:
                    combos.append({'file': fn, 'market': market, 'commodity': cmd, 'rows': len(sub)})

    if not combos:
        logger.info('No valid market+commodity combinations found (try lowering --min-rows)')
        return

    logger.info(f'Found {len(combos)} valid combinations (min-rows={args.min_rows})')

    # show a sample
    for c in combos[:10]:
        logger.info(f" - {c['commodity']} @ {c['market']} ({c['rows']} rows) from {Path(c['file']).name}")

    if args.limit:
        combos = combos[:args.limit]

    if args.dry_run:
        logger.info('Dry-run enabled; not training. To train, run with --no-dry-run')
        return

    # training loop
    trained = []
    for i, c in enumerate(combos, 1):
        market = c['market']
        commodity = c['commodity']
        fn = c['file']
        logger.info(f'[{i}/{len(combos)}] Training ensemble for {commodity} @ {market} (rows={c["rows"]})')

        df = load_dataset(fn)
        df = preprocess_prices(df)
        feat = prepare_features(df.copy())
        sub = feat[(feat['market_name'].str.lower().str.strip() == str(market).lower().strip()) &
                   (feat['cmdty'].str.lower().str.strip() == str(commodity).lower().strip())].copy()

        # training input
        X = sub.drop(columns=['p_modal'], errors='ignore')
        y = sub['p_modal']

        try:
            path = train_stacked_ensemble(X, y, market, commodity)
        except Exception as e:
            logger.error(f'Failed to train {commodity}@{market}: {e}')
            continue

        # Move model into market-specific folder for tidy organization
        market_dir = os.path.join(MODELS_DIR, sanitize_name(market))
        os.makedirs(market_dir, exist_ok=True)
        src = path
        dst = os.path.join(market_dir, os.path.basename(path))
        try:
            shutil.move(src, dst)
            logger.info(f'Model moved to {dst}')
            trained.append({'market': market, 'commodity': commodity, 'model_path': dst})
        except Exception as e:
            logger.warning(f'Could not move model file: {e} (left at {src})')

    logger.info(f'Training complete. Trained {len(trained)} models.')


if __name__ == '__main__':
    main()
