# AgriWave — Project Report

Date: 2025-09-25

This document is a comprehensive project report for AgriWave — a terminal-first agricultural commodity forecasting toolkit developed to read CSV datasets, produce short-term forecasts, compare markets, and support an iterative model-improvement workflow.

## Executive summary
AgriWave provides an end-to-end pipeline that: ingests commodity price (and optional quantity) CSVs, preprocesses and engineers time-series features, and produces either a fallback statistical forecast (fast) or a model-based ensemble forecast (when trained). It includes utilities for market comparison and a CLI to run preflight checks, training, prediction, and ranked summaries. The design prioritizes usability (terminal-first), graceful degradation when heavy ML libraries are not installed, and easy extensibility for adding models and metrics.

## Goals and scope
- Provide immediate, usable forecasts with minimal dependencies.
- Support a hybrid/ensemble training path that leverages XGBoost, Prophet, LSTM, and stacking where available.
- Let users run predictions locally from CSV files and compare markets by modal price and potential profit.
- Make the system robust: when heavy models are missing, fall back to a statistically sound predictor.

## Project layout (key files)
- `farmer_price_predictor.py`: CLI entrypoint for `preflight`, `predict`, `hybrid-train`, `compare`, `top-summary`.
- `dataset/`: input CSVs (price & optional quantity files).
- `models/`: model artifacts (ensemble_*.joblib saved by training flows).
- `data_preprocessing.py`: CSV loader, date normalization, basic cleaning.
- `feature_engineering.py`: generates temporal features, lags, rolling stats, Fourier terms, etc.
- `prediction_engine.py`: ensemble predict + improved fallback predictor (ExponentialSmoothing or Ridge recursion).
- `market_comparison.py`: ranking, potential profit, and top-summary utilities.
- `models/` subdirectory: model wrappers (xgboost, prophet, lstm, optuna tuner, hybrid trainer).
- `README.md`, `workflow.md`, `report.md`: docs and workflow guidance.

## Data schema and assumptions
Expected fields in price CSVs (flexible names supported):
- date column: `t`, `date`, or `ds` (loader will detect and normalize).
- `cmdty` — commodity name.
- `market_name` — market identifier.
- `p_modal` — modal per-quintal price (₹/quintal). The code prints conversions to ₹/kg by dividing by 100.

Quantity CSVs (optional) should contain `date`/`t`, `cmdty`, `market_name` and a quantity column (e.g., `qty`, `quantity`). When present, the fallback regression attempts to use quantity as an exogenous feature.

## Pipeline (end-to-end)
1. CLI parse and route to `cmd_predict` / `cmd_hybrid_train` / etc.
2. Load CSV with `load_dataset` (resolves `dataset/` path). Filter to project region subset (Telangana-Hyderabad) using `filter_telangana_hyderabad`.
3. Clean prices with `preprocess_prices` (fillna, winsorize, dtype normalization).
4. Build features via `prepare_features`: temporal encodings, lag and rolling features, Fourier terms, and target encodings.
5. Select market & commodity subset; ensure DataFrame is datetime-indexed (`_ensure_dt_index`).
6. If an ensemble artifact exists, run `predict_with_ensemble`; otherwise call `fallback_stats_predict`.
7. Render results: calendar view, ASCII sparkline, day-by-day forecast, 80% CI, market comparison table, top recommendation.

## Modeling strategy
- Ensemble (optional): a stacked approach combining base learners (XGBoost, Prophet, LSTM) with a per-horizon linear meta-model. The ensemble includes conformal-like residual quantiles (q80, q90, q95) saved at training time to produce uncertainty bands.
- Fallback predictor (default if no ensemble):
  - Primary attempt: `statsmodels` ExponentialSmoothing (Holt-Winters) to capture trend and weekly seasonality.
  - Secondary fallback: Ridge regression trained on time features, day-of-year Fourier terms, lags (1,7,30), and rolling statistics. It supports optional exogenous quantity series.

Rationale: this layered approach gives a fast, reliable fallback when heavy ML frameworks are unavailable, while allowing higher-fidelity ensemble models where computational resources and dependencies exist.

## Training and tuning
- `hybrid-train` orchestrates tuning (Optuna for XGBoost) and training of base and meta models. It writes an ensemble artifact `models/ensemble_{commodity}_{market}.joblib` containing paths to base models, meta-models, conformal quantiles, and metadata (seq_len, feature list).
- Quick mode (`--quick`) reduces Optuna trials and LSTM epochs for development/testing.

## CLI usage (examples)
- Preflight: sanity-check CSV and environment
  - `python .\farmer_price_predictor.py preflight --data brinjal_price_data2021-2024.csv`
- Quick predict (fallback):
  - `python .\farmer_price_predictor.py predict --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --horizon 30`
- Quick hybrid train (dev):
  - `python .\farmer_price_predictor.py hybrid-train --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --quick`
- Top-summary (how often each market is top):
  - `python .\farmer_price_predictor.py top-summary --data potato_price_data2021-2024.csv`

## Output and interpretation
- Forecast values are returned in ₹/quintal and printed with per-kg conversions. The 80% CI uses residual quantiles (or model residuals from fallback) as a pragmatic uncertainty estimate.
- `TOP RECOMMENDATION` is currently computed by comparing modal (median) prices per market — this prioritizes markets with consistently higher modal prices, not direct profit (profit needs quantity and transport cost).

## Validation & example traces
- Early runs in the user's environment showed:
  - successful data loading and preprocessing (e.g., 4666 rows for brinjal, 4755 rows for potato)
  - fallback predictions when ensemble artifacts were missing
  - statsmodels warnings about index frequency (harmless for current forecast usage)

## Known limitations
- Ensemble model training requires heavy dependencies (xgboost, prophet, tensorflow) which may be hard to install on Windows without conda.
- The top-market recommendation uses modal price only; this can be misleading if sellers care about traded volume or transport costs. A profit-based ranking is a planned improvement.
- Forecast intervals are based on residual quantiles, which are simple and not time-adaptive; conformal or time-series-specific interval methods would be preferred for rigorous coverage guarantees.

## Reproducibility & installation
1. Create a venv and activate it.
2. `pip install -r requirements.txt`
3. (Optional) `pip install statsmodels` for a stronger fallback predictor.
4. Place CSVs in `dataset/` and run `preflight` to validate.

## Next steps (recommended roadmap)
- Add `profit-summary` that computes expected revenue using quantity CSVs and transport-cost inputs.
- Persist forecasts as CSV/JSON via `--export-csv` and add a small ingestion API.
- Add unit tests covering data preprocessing, feature engineering, fallback predictor, and CLI behaviors.
- Improve conformal intervals and integrate SHAP explainability for model-based predictions.

## Contact & contributors
- See repository files for authoring and commit history. If you want me to implement any of the roadmap items, tell me which and I will add the code and tests.

---
Report generated by the project tooling on 2025-09-25.
