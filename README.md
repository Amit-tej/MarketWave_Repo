# AgriWave — Terminal-based Agri Commodity Forecasting

This repository contains a terminal-driven forecasting toolkit for Indian agri-commodity markets. It includes data loaders, feature engineering, lightweight fallback forecasting, and a hybrid training harness (Optuna + XGBoost + Prophet + LSTM placeholders). The CLI provides commands for dataset preflight checks, training, forecasting, and market comparison.

## Quick overview

## Tech stack & roles
This project uses a collection of Python libraries and tools. Below is a concise list describing each technology and the role it plays in AgriWave.

- Python (3.9+) — the implementation language; scripts and modules are written in Python.
- pandas — primary data frame library for reading CSVs, cleaning, and tabular operations.
- numpy — numerical operations, arrays, and helper functions used across features and models.
- scikit-learn — feature transforms, baseline models (e.g., Ridge), stacking/meta models, and utilities like scaling and metrics.
- joblib — save/load model artifacts (ensemble joblib files) and scalers.
- statsmodels — used by the fallback predictor to run ExponentialSmoothing (Holt-Winters) for short-term seasonal forecasts.
- xgboost / lightgbm / catboost — gradient-boosted tree libraries used as base learners in the hybrid ensemble when installed; wrappers present in `models/`.
- prophet — additive time-series model (seasonality/trend) used as a base model in the ensemble (installation may require conda on Windows).
- tensorflow / keras — used to build/train LSTM models (sequence models) if enabled; optional and heavier to install.
- optuna — hyperparameter optimization for XGBoost and other models (used by the hybrid training harness).
- shap — explainability library; available to add model explainers (not required for core predictions).
- matplotlib — plotting and diagnostic visualizations (optional for scripts / notebooks).
- tabulate / rich — terminal display helpers for pretty tables and formatted CLI output.
- tqdm — progress bars used during training/processing loops.

Notes on heavy packages and installation:
- `prophet` and `tensorflow` frequently require platform-specific handling on Windows; using conda (`conda create -n agriwave python=3.10`) often simplifies installation.
- The fallback predictor (ridge regression and/or statsmodels) is designed to work without the heavy packages; you only need `pandas`, `numpy`, and `scikit-learn` for reasonable forecasts.


## Prerequisites
- Python 3.9+ (3.10/3.11 recommended)
- Recommended: create a virtual environment

Optional (heavy) libraries for full model training:
- xgboost, lightgbm, catboost, prophet (a.k.a. `prophet` / `fbprophet`), tensorflow (for LSTM)

On Windows: installing `prophet` and `tensorflow` often works better with conda. If you only want fallback forecasts, the lightweight flow will work with core libs.

## Install (recommended)
Open PowerShell in the repo root and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
# Optional (for better fallback forecasts):
pip install statsmodels
# If you need Prophet or TensorFlow on Windows, consider conda:
# conda create -n agriwave python=3.10
# conda activate agriwave
# pip install -r requirements.txt
```

If `prophet` or `tensorflow` fail on Windows, install via conda or skip them — the fallback and regression-based predictors will still work.

## Files: dataset schema
Each price CSV should contain, at minimum, these columns (field names are flexible — adapter supports `t` as date):
- `t` or `date` — date of observation
- `cmdty` — commodity name
- `market_name` — market name
- `p_modal` — modal per-quintal price (₹/quintal)

Quantity CSVs (optional) can contain `t`/`date`, `cmdty`, `market_name`, and a quantity column (e.g., `quantity`, `qty`). The fallback regression will attempt to load matching quantity files to use as exogenous features.

## Useful commands

1) Preflight (inspect CSV & environment)

```powershell
python .\farmer_price_predictor.py preflight --data brinjal_price_data2021-2024.csv
```

2) Quick fallback prediction (no training required)

```powershell
python .\farmer_price_predictor.py predict --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --horizon 30
```

If no trained ensemble artifact exists for the market+commodity the CLI will use a robust fallback (Holt-Winters if `statsmodels` installed, otherwise a ridge regression with lags and seasonal features). This produces daily forecasts and simple uncertainty bands.

3) Hybrid (ensemble) training (quick)

```powershell
python .\farmer_price_predictor.py hybrid-train --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --quick
```

Notes: full hybrid training requires heavy dependencies (xgboost, prophet, tensorflow). Use `--quick` to run a faster tuning path for testing.

4) Batch training across dataset CSVs

```powershell
python .\farmer_price_predictor.py hybrid-train --all --quick
```

5) Compare markets and view ranked markets

```powershell
python .\farmer_price_predictor.py compare --data brinjal_price_data2021-2024.csv
```

6) See how many commodities a market is top for

```powershell
python .\farmer_price_predictor.py top-summary --data potato_price_data2021-2024.csv
```

## Interpreting outputs
- Forecasts are printed per-day with an 80% CI (conformal/residual-based estimate). Values are in ₹/quintal and converted to ₹/kg in prints.
- `TOP RECOMMENDATION` is chosen by highest modal price (median) in the comparison table. If you want profit-based ranking (taking quantities & transport into account), request `profit-summary` (I can add it) and we will use quantity CSVs.

## Troubleshooting (common issues)
- KeyError: "['date'] not in columns" — your CSV uses `t` as the date column. The loader recognizes `t`, `date`, and `ds` but if you modified the CSV, ensure a parseable date column exists.
- XGBoost ValueError about object dtypes — fixed in code: categorical/object columns are converted to numeric codes before building DMatrix.
- Model not found warning — this means no `models/ensemble_<Commodity>_<Market>.joblib` artifact exists yet; run `hybrid-train` to create it, or rely on the fallback predictor.
- Prophet or TensorFlow install failures on Windows — use conda for these packages.

## Want model-based forecasts for production?
1. Install heavy deps (xgboost, prophet, tensorflow) — preferably with conda on Windows.
2. Run `hybrid-train` for target datasets (remove `--quick` for full tuning).
3. Then run `predict` which will use the saved ensemble artifact for better forecasts.

## Extending the project
- Add new model wrappers under `models/` (follow existing wrapper patterns: train/load/predict).
- Improve conformal intervals by replacing residual quantiles with time-aware conformal techniques.

## Contributing
- Open a PR with a small change and a short description. Add tests where appropriate.

## License
MIT-style (no explicit license file provided in this repo). Check with the project owner if you intend to redistribute.

---
If you want, I can:
- Add a `--export-csv` option to `top-summary` or `predict` to save outputs.
- Add profit-based top-market ranking using quantity files and a transport-cost parameter.
- Create a small demo script that trains a quick model and shows side-by-side fallbacks vs ensemble forecasts.

Tell me which of the above you want next and I'll implement it.
CUTTING-EDGE AGRI-COMMODITY PRICE PREDICTION SYSTEM

This repository contains a terminal-based prediction system scaffold for multi-market commodity price forecasting and comparison. It includes modular components for data preprocessing, feature engineering, model training, prediction, market comparison and a CLI interface.

Notes:
- Implementations are intentionally modular and use lazy imports so the CLI can run even when heavy ML dependencies are not installed.
- See `requirements.txt` for recommended packages.

Quick start (after installing requirements):

python farmer_price_predictor.py --help
