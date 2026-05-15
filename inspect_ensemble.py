#!/usr/bin/env python3
"""Inspect saved ensemble joblib file and report contents and referenced artifact files.

Usage:
    python inspect_ensemble.py path/to/ensemble.joblib

If no path provided, lists ensemble files under models/ and prompts to choose one.
"""
import os
import sys
import joblib
from pathlib import Path
from pprint import pprint

def inspect(path):
    p = Path(path)
    if not p.exists():
        print(f'File not found: {p}')
        return
    print(f'Loading ensemble: {p}')
    obj = joblib.load(str(p))
    print('\nTop-level keys and types:')
    for k,v in (obj.items() if isinstance(obj, dict) else enumerate([obj])):
        if isinstance(obj, dict):
            print(f' - {k}: {type(v).__name__}')
    print('\nFull dict keys:')
    if isinstance(obj, dict):
        pprint(list(obj.keys()))
    else:
        print(' - Ensemble is not a dict, type:', type(obj))

    # Common artifact keys
    for key in ('xgb_path','prophet_path','lstm_path','meta_models','conformal','seq_len','feature_columns'):
        if isinstance(obj, dict) and key in obj:
            val = obj[key]
            print(f'\n{key}:')
            print('  ', val)
            # if it's a path, check existence
            if isinstance(val, str) and val:
                exists = Path(val).exists()
                print(f'    -> exists: {exists}  size: {Path(val).stat().st_size if exists else None}')

    # If meta_models present, list horizons and model types
    if isinstance(obj, dict) and 'meta_models' in obj and obj['meta_models']:
        mm = obj['meta_models']
        print('\nmeta_models per horizon:')
        try:
            for h, m in sorted(mm.items() if isinstance(mm, dict) else enumerate(mm)):
                print(f' - horizon {h}: {type(m).__name__}')
        except Exception as e:
            print('  Could not iterate meta_models:', e)

    # If there are base model paths, check their files
    print('\nScanning models/ directory for ensemble-like files...')
    models_dir = Path(__file__).resolve().parent / 'models'
    if models_dir.exists():
        files = list(models_dir.rglob('ensemble_*.joblib'))
        print(f' Found {len(files)} ensemble files under {models_dir}')
        for f in files:
            print('  -', f)

def choose_file_under_models():
    models_dir = Path(__file__).resolve().parent / 'models'
    if not models_dir.exists():
        print('models/ directory not found')
        return None
    files = list(models_dir.rglob('ensemble_*.joblib'))
    if not files:
        print('No ensemble_*.joblib files found under models/')
        return None
    print('Ensemble files found:')
    for i,f in enumerate(files, start=1):
        print(f' {i}. {f}')
    sel = input('Enter number to inspect (or press Enter to cancel): ').strip()
    if not sel:
        return None
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(files):
            return None
        return files[idx]
    except Exception:
        return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        inspect(sys.argv[1])
    else:
        chosen = choose_file_under_models()
        if chosen:
            inspect(chosen)
        else:
            print('No file chosen. Exiting.')
