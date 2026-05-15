#!/usr/bin/env python
"""
Comprehensive environment fix script for MarketWave
Handles Python dependency resolution, cache clearing, and validation
"""
import subprocess
import sys
import os
import shutil
import site

def run_cmd(cmd, desc=""):
    """Run a command and print output"""
    if desc:
        print(f"\n{'='*60}")
        print(f"[STEP] {desc}")
        print('='*60)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"ERROR: Command timed out: {cmd}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def clear_python_cache():
    """Clear all Python cache files and directories"""
    print("\n[STEP] Clearing Python cache...")
    patterns = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.egg-info'
    ]
    
    # Clear project cache
    for root, dirs, files in os.walk('.'):
        for d in dirs[:]:
            if d == '__pycache__':
                try:
                    shutil.rmtree(os.path.join(root, d))
                    print(f"  Removed: {os.path.join(root, d)}")
                except Exception as e:
                    print(f"  Could not remove {os.path.join(root, d)}: {e}")
        for f in files:
            if f.endswith(('.pyc', '.pyo')):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass
    
    # Clear site-packages cache
    try:
        site_packages = site.getsitepackages()
        for sp in site_packages:
            for root, dirs, files in os.walk(sp):
                for d in list(dirs):
                    if d == '__pycache__':
                        try:
                            shutil.rmtree(os.path.join(root, d))
                        except Exception:
                            pass
    except Exception as e:
        print(f"  Could not clear site-packages cache: {e}")

def uninstall_conflicting_packages():
    """Uninstall known problematic packages"""
    packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'typing_extensions',
        'starlette'
    ]
    print("\n[STEP] Uninstalling conflicting packages...")
    for pkg in packages:
        run_cmd(f"python -m pip uninstall -y {pkg}", f"Uninstall {pkg}")

def install_base_dependencies():
    """Install base dependencies from requirements.txt"""
    print("\n[STEP] Installing base requirements...")
    # First install base ML dependencies
    base_deps = [
        'numpy>=1.19.0',
        'pandas>=1.1.0',
        'scikit-learn>=0.24.0',
        'joblib>=1.0.0'
    ]
    for dep in base_deps:
        cmd = f"python -m pip install --no-cache-dir {dep}"
        run_cmd(cmd, f"Installing {dep}")

def install_fastapi_stack():
    """Install FastAPI and related packages with correct versions"""
    print("\n[STEP] Installing FastAPI stack...")
    # For Python 3.9, use compatible versions
    packages = [
        'typing_extensions==4.12.0',
        'pydantic==2.5.0',
        'fastapi==0.104.1',
        'uvicorn==0.24.0'
    ]
    
    for pkg in packages:
        cmd = f"python -m pip install --no-cache-dir --force-reinstall {pkg}"
        success = run_cmd(cmd, f"Installing {pkg}")
        if not success:
            print(f"WARNING: Failed to install {pkg}, attempting without --force-reinstall")
            cmd = f"python -m pip install --no-cache-dir {pkg}"
            run_cmd(cmd, f"Installing {pkg} (retry)")

def install_ml_dependencies():
    """Install ML and data processing dependencies"""
    print("\n[STEP] Installing ML dependencies...")
    ml_deps = [
        'prophet>=1.1',
        'xgboost>=1.5.0',
        'lightgbm>=3.3.0',
        'catboost>=1.1',
        'tensorflow>=2.10.0',
        'shap>=0.41.0',
        'optuna>=2.10.0'
    ]
    
    for dep in ml_deps:
        cmd = f"python -m pip install --no-cache-dir {dep}"
        run_cmd(cmd, f"Installing {dep}")

def validate_imports():
    """Validate all critical imports"""
    print("\n[STEP] Validating imports...")
    imports = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'typing_extensions',
        'pandas',
        'joblib',
        'prediction_engine'
    ]
    
    failed = []
    for imp in imports:
        try:
            if imp == 'prediction_engine':
                # Try local import
                spec = __import__('importlib').util.spec_from_file_location("prediction_engine", "prediction_engine.py")
                if spec and spec.loader:
                    spec.loader.exec_module(__import__('importlib').util.module_from_spec(spec))
                print(f"  ✓ {imp}")
            else:
                __import__(imp)
                print(f"  ✓ {imp}")
        except Exception as e:
            print(f"  ✗ {imp}: {e}")
            failed.append(imp)
    
    return len(failed) == 0

def test_api_server():
    """Test if api_server.py can be imported"""
    print("\n[STEP] Testing API server import...")
    try:
        spec = __import__('importlib').util.spec_from_file_location("api_server", "api_server.py")
        if spec and spec.loader:
            mod = __import__('importlib').util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            print("  ✓ api_server.py imports successfully")
            return True
    except Exception as e:
        print(f"  ✗ api_server.py import failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("   MarketWave Environment Fix Script")
    print("="*60)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    
    # Execute fix steps
    clear_python_cache()
    uninstall_conflicting_packages()
    install_base_dependencies()
    install_fastapi_stack()
    install_ml_dependencies()
    
    # Validate
    print("\n" + "="*60)
    print("   Validation")
    print("="*60)
    
    imports_ok = validate_imports()
    api_ok = test_api_server()
    
    print("\n" + "="*60)
    print("   Summary")
    print("="*60)
    print(f"  Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"  API Server: {'✓ PASS' if api_ok else '✗ FAIL'}")
    print("\n[NEXT] If all checks pass, run: python api_server.py")
    print("="*60 + "\n")
    
    return 0 if (imports_ok and api_ok) else 1

if __name__ == '__main__':
    sys.exit(main())
