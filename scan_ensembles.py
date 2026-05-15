#!/usr/bin/env python3
"""Scan all ensemble_*.joblib files under models/ and produce a CSV report.

Report columns:
 - ensemble_path
 - ensemble_type (simple/hybrid/unknown)
 - has_m1_m2_meta (bool)
 - meta_horizons (int)
 - xgb_path, xgb_exists
 - prophet_path, prophet_exists
 - lstm_path, lstm_exists
 - file_size_bytes

Outputs `ensemble_report.csv` at project root and prints a short summary.
"""
import os
import sys
import joblib
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / 'models'
OUT_CSV = ROOT / 'ensemble_report.csv'

def inspect_ensemble(p: Path):
    rec = {
        'ensemble_path': str(p),
        'ensemble_type': 'unknown',
        'has_m1_m2_meta': False,
        'meta_horizons': 0,
        'xgb_path': None,
        'xgb_exists': False,
        'prophet_path': None,
        'prophet_exists': False,
        'lstm_path': None,
        'lstm_exists': False,
        'file_size_bytes': p.stat().st_size if p.exists() else None
    }
    try:
        obj = joblib.load(str(p))
    except Exception as e:
        rec['ensemble_type'] = f'load_error: {e}'
        return rec

    if isinstance(obj, dict):
        # simple stacked ensemble created by train_stacked_ensemble
        if all(k in obj for k in ('m1','m2','meta')):
            rec['ensemble_type'] = 'simple_stacked'
            rec['has_m1_m2_meta'] = True
        # hybrid ensemble structure
        if 'meta_models' in obj:
            rec['ensemble_type'] = 'hybrid'
            try:
                rec['meta_horizons'] = len(obj['meta_models']) if obj['meta_models'] else 0
            except Exception:
                rec['meta_horizons'] = 0
        # check base artifact paths
        for key in ('xgb_path','prophet_path','lstm_path'):
            v = obj.get(key)
            if isinstance(v, str) and v:
                rec[key] = v
                rec[f'{key.split("_")[0]}_exists'] = Path(v).exists()

    else:
        rec['ensemble_type'] = type(obj).__name__

    return rec

def main():
    if not MODELS_DIR.exists():
        print('models/ directory not found; aborting')
        sys.exit(1)

    files = list(MODELS_DIR.rglob('ensemble_*.joblib'))
    if not files:
        print('No ensemble_*.joblib files found under models/')
        sys.exit(0)

    rows = []
    for f in sorted(files):
        r = inspect_ensemble(f)
        rows.append(r)

    # write CSV
    fieldnames = ['ensemble_path','ensemble_type','has_m1_m2_meta','meta_horizons','xgb_path','xgb_exists','prophet_path','prophet_exists','lstm_path','lstm_exists','file_size_bytes']
    with open(OUT_CSV, 'w', newline='', encoding='utf8') as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fieldnames})

    # print summary
    total = len(rows)
    simple = sum(1 for r in rows if r['ensemble_type'].startswith('simple'))
    hybrid = sum(1 for r in rows if r['ensemble_type'].startswith('hybrid'))
    loads_failed = sum(1 for r in rows if r['ensemble_type'].startswith('load_error'))
    missing_artifacts = sum(1 for r in rows if (not r.get('xgb_exists') and not r.get('prophet_exists') and not r.get('lstm_exists')))

    print(f'Found {total} ensemble files: {simple} simple, {hybrid} hybrid, {loads_failed} load errors')
    print(f'{missing_artifacts} ensembles reference no base artifacts (xgb/prophet/lstm)')
    print(f'Report written to: {OUT_CSV}')

if __name__ == '__main__':
    main()
