#!/usr/bin/env python3
"""Organize model artifact files in the models/ directory into per-market folders.

Rules:
- Only move artifact files (extensions: .joblib, .model, .h5, .json, .pkl, .sav)
- Skip Python source files and other non-artifact files (leave wrappers like *.py in place)
- Infer market name from filename by taking the last '_'-separated token before the extension
  (falls back to parent folder name or 'misc' if not found)
- If a destination file already exists and is identical (same size and checksum), remove the duplicate.
- If destination file exists but differs, keep both by appending a numeric suffix.
"""
import os
import shutil
import hashlib
from pathlib import Path
from utils import get_logger

logger = get_logger('organize_models')

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / 'models'

ARTIFACT_EXTS = {'.joblib', '.model', '.h5', '.json', '.pkl', '.sav'}


def file_checksum(path, algo='md5'):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def sanitize_folder(name: str) -> str:
    s = str(name).strip()
    # Replace spaces and illegal path chars
    for ch in ('/', '\\', ':', '*', '?', '"', '<', '>', '|'):
        s = s.replace(ch, '_')
    s = s.replace(' ', '_')
    return s


def infer_market_from_name(stem: str, parent_name: str = None) -> str:
    # Try by splitting on '_', then '-' if underscore not helpful
    parts = stem.split('_')
    if len(parts) >= 2:
        candidate = parts[-1]
        if candidate:
            return candidate
    parts2 = stem.split('-')
    if len(parts2) >= 2:
        return parts2[-1]
    if parent_name:
        return parent_name
    return 'misc'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true', help='Preview planned moves without performing them')
    args = ap.parse_args()

    if not MODELS_DIR.exists():
        logger.error(f'Models directory not found: {MODELS_DIR}')
        return

    moved = 0
    duplicates = 0
    conflicts = 0
    planned_actions = []

    # Walk the models directory
    for root, dirs, files in os.walk(MODELS_DIR):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue

        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()

            # Skip python source and wrappers
            if ext == '.py' or fname.endswith('.pyc'):
                continue

            # Only handle artifact extensions
            if ext not in ARTIFACT_EXTS:
                continue

            # Determine inferred market
            stem = fpath.stem
            parent = Path(root).name if Path(root) != MODELS_DIR else None
            market_raw = infer_market_from_name(stem, parent_name=parent)
            market = sanitize_folder(market_raw)

            dest_dir = MODELS_DIR / market
            dest_path = dest_dir / fname

            # If file already in destination (already organized), skip
            try:
                if dest_path.exists() and fpath.samefile(dest_path):
                    continue
            except Exception:
                pass

            # If destination exists, check for duplicate by checksum and size
            action = {'src': str(fpath), 'dest_dir': str(dest_dir), 'dest': str(dest_path), 'action': None}
            if dest_path.exists():
                try:
                    src_sz = fpath.stat().st_size
                    dst_sz = dest_path.stat().st_size
                except Exception:
                    src_sz = dst_sz = -1

                if src_sz == dst_sz and src_sz > 0:
                    # compare checksum
                    try:
                        if file_checksum(fpath) == file_checksum(dest_path):
                            action['action'] = 'remove_duplicate'
                            action['reason'] = f'same as {dest_path}'
                            planned_actions.append(action)
                            duplicates += 1
                            continue
                    except Exception:
                        pass

                # conflict: keep both by renaming
                base = dest_path.stem
                i = 1
                while True:
                    new_name = f"{base}__dup{i}{ext}"
                    new_path = dest_dir / new_name
                    if not new_path.exists():
                        action['dest'] = str(new_path)
                        action['action'] = 'move_conflict'
                        action['reason'] = 'conflict_keep_both'
                        planned_actions.append(action)
                        conflicts += 1
                        break
                    i += 1
            else:
                action['action'] = 'move'
                planned_actions.append(action)

            # if not preview, perform move/remove
            if not args.preview and action['action'] == 'move':
                dest_dir.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(fpath), action['dest'])
                    logger.info(f'Moved: {fpath} -> {action["dest"]}')
                    moved += 1
                except Exception as e:
                    logger.error(f'Failed to move {fpath} -> {action["dest"]}: {e}')
            elif not args.preview and action['action'] == 'move_conflict':
                dest_dir.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(fpath), action['dest'])
                    logger.info(f'Moved (conflict rename): {fpath} -> {action["dest"]}')
                    moved += 1
                except Exception as e:
                    logger.error(f'Failed to move {fpath} -> {action["dest"]}: {e}')
            elif not args.preview and action['action'] == 'remove_duplicate':
                try:
                    fpath.unlink()
                    logger.info(f'Removed duplicate: {fpath}')
                except Exception as e:
                    logger.error(f'Failed to remove duplicate {fpath}: {e}')

    # summary / preview output
    if args.preview:
        logger.info('Preview mode: planned actions (no files changed)')
        for a in planned_actions:
            logger.info(f"{a['action']}: {a['src']} -> {a['dest']}  ({a.get('reason','')})")
        logger.info(f'Planned moves: {sum(1 for a in planned_actions if a["action"] in ("move","move_conflict"))}, duplicates: {duplicates}, conflicts: {conflicts}')
    else:
        logger.info(f'Organization complete. Moved: {moved}, Duplicates removed: {duplicates}, Conflicts kept: {conflicts}')


if __name__ == '__main__':
    main()
