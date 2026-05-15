# AgriWave — Project Workflow

This document explains what AgriWave is, why it exists, which components are used, where files and artifacts live, when each step runs, and how the full system runs end-to-end. It's a compact, practical reference to help new contributors or users run and extend the project.

## 1. What (project summary)
- AgriWave is a terminal-first toolkit for forecasting agricultural commodity modal prices at market level. It supports data loading, preprocessing, feature engineering, fallback and model-based forecasting, market comparisons, and simple profit estimation.

## 2. Why (motivation)
- Provide small-scale, reproducible forecasts to help farmers/aggregators compare markets and time their sales.
- Work offline from CSV datasets and allow progressive improvement: start with a robust fallback predictor, then add model-based ensembles for better accuracy.

## 3. Which (key technologies & files)
- Python 3.9+; recommend venv or conda.
- Core libs: pandas, numpy, scikit-learn, joblib, matplotlib (optional), statsmodels (optional, for better fallback forecasts).
- Optional / heavy: xgboost, lightgbm, catboost, prophet, tensorflow, optuna — used by the hybrid training harness.
- Important files:
  - `farmer_price_predictor.py` — CLI entrypoint (preflight, predict, hybrid-train, compare, top-summary, etc.)
  - `dataset/` — input CSVs (price + optional quantity files)
  - `models/` — saved model artifacts (ensemble_*.joblib)
  - `prediction_engine.py` — ensemble/predict and fallback predictors
  - `market_comparison.py` — ranking and top-summary utilities
  - `feature_engineering.py` — builds model features
  - `models/` directory — model wrappers and training helpers

## 4. Where (data and artifact locations)
- Input data: `dataset/` directory at the repository root. Files expected by convention:
  - `<commodity>_price_<yyyymm>.csv` / e.g. `brinjal_price_data2021-2024.csv`
  - `<commodity>_quantity_*.csv` (optional) — used as exogenous features
- Trained artifacts: `models/ensemble_<Commodity>_<Market>.joblib`
- Logs: printed to stdout (CLI) and to any logger the environment is configured to collect.

## 5. When (order of operations & scheduling)
- Manual/local adhoc usage recommended:
  1. Preflight (one-time per CSV): validate columns and environment
  2. Predict (fallback) for immediate insights
  3. Hybrid-train for model-based forecasts (optional; heavy)
  4. Predict (ensemble) once trained
  5. Compare / top-summary to inform market-level decisions

- For regular, automated runs (cron/Task Scheduler):
  - Run `preflight` weekly to detect data changes.
  - Run `hybrid-train --quick` for nightly/weekly incremental training (if resources permit).
  - Run `predict` daily to produce forecasts for stakeholders.

## 6. How (end-to-end workflow)
This is a step-by-step walkthrough from raw CSV to forecast and market recommendation.

1) Prepare dataset
  - Place price CSV(s) in `dataset/`.
  - Confirm required fields: `t` or `date`, `cmdty`, `market_name`, `p_modal` (the loader recognizes `t` as date).

2) Preflight (inspect CSV and environment)
  - Purpose: quick validation that the CSV contains required fields and prints environment status.

```powershell
python .\farmer_price_predictor.py preflight --data brinjal_price_data2021-2024.csv
```

3) Quick prediction (fallback)
  - Purpose: get immediate forecasts without training heavy models. Uses ExponentialSmoothing (statsmodels) if present, otherwise a ridge regression with time features and lags.

```powershell
python .\farmer_price_predictor.py predict --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --horizon 30
```

### What happens internally when you run the example predict command
Below is a precise, step-by-step trace of what the project code does from the moment the CLI receives the command to when the output is printed. This matches the implemented functions in the repository so new contributors can follow the exact data/model flow.

1) CLI parsing and argument resolution
  - `farmer_price_predictor.py` parses the arguments: data file, market, commodity, horizon.
  - The `predict` subcommand handler (`cmd_predict`) is invoked with those args.

2) Load & filter data
  - `load_dataset(args.data)` resolves the path under `dataset/` and loads the CSV into a pandas DataFrame.
  - `filter_telangana_hyderabad(df)` restricts rows to the Telangana / Hyderabad subset used by the project.
  - `preprocess_prices(df)` cleans price fields: normalizes price column, forward/back fills missing values, winsorizes extreme outliers (see `data_preprocessing.py`).

3) Feature construction
  - `prepare_features(df)` builds modeling features: temporal features (day-of-week, month), lag features (1,7,30), rolling statistics (7/30), Fourier terms, momentum indicators and any target encodings. The resulting DataFrame (`df_feat`) contains `p_modal` and feature columns.

4) Market & commodity selection
  - The handler matches the provided `--market` and `--commodity` case-insensitively against `df_feat['market_name']` and `df_feat['cmdty']`.
  - A subset `sub` is created with rows matching that market+commodity.

5) Ensure datetime index
  - The code runs `_ensure_dt_index(sub)` which:
    - Looks for a date column named `date`, `t`, `datetime`, or `ds` and parses it as datetimes.
    - If none found, tries to infer a parseable date column.
    - If it still can't find a date, it attempts to parse the DataFrame index as datetimes and raises a clear KeyError if parsing fails.

6) Locate an ensemble artifact (model-based path)
  - The CLI computes `model_path = models/ensemble_{commodity}_{market}.joblib` and checks for its existence.
  - If the file exists, the code calls `predict_with_ensemble(model_path, sub_dt, horizon=horizon)`.

7) Ensemble prediction (when model artifact exists)
  - `predict_with_ensemble` (in `prediction_engine.py`) does the following:
    - Loads the saved ensemble joblib. The ensemble contains pointers/paths to base models (XGBoost, Prophet, LSTM), meta-models (one per horizon), conformal residual quantiles, and metadata such as `seq_len`.
    - Loads XGBoost via `models.xgboost_wrapper.load_xgboost` (wrapper handles categorical-to-code conversions). If XGBoost exists, the code runs a recursive predict loop that feeds each predicted value back as a feature for the next step.
    - Loads Prophet model (if present) and uses its `make_future_dataframe(periods=horizon)` and `predict` to get multi-day Prophet forecasts.
    - Loads LSTM (if saved) and its scaler and iteratively generates multi-step LSTM forecasts (seq2seq style placeholder).
    - For each horizon day h=1..H the meta-model for that horizon (if present) is used to combine base-model forecasts into a final `yhat[h]`. If a meta-model is missing, the code averages available base-model predictions.
    - Conformal / uncertainty: the ensemble stores pre-computed residual quantiles (q80/q90/q95). The code builds intervals for each horizon as (yhat - q, yhat + q).
    - `predict_with_ensemble` returns a dictionary: `{'yhat': [...], 'intervals': {...}, 'base_preds': {...}}`.

8) Fallback prediction (when ensemble artifact is missing)
  - If the ensemble file is not present, `cmd_predict` logs `Model not found: ...; using fallback historical stats predictor` and calls `fallback_stats_predict(sub_dt, horizon=horizon)`.
  - `fallback_stats_predict` (enhanced fallback) attempts two methods, in order:
    1. Try statsmodels' `ExponentialSmoothing` (Holt-Winters) if the `statsmodels` package is installed. This captures trend + weekly seasonality when data length allows.
    2. If `statsmodels` is not available or fails, build a Ridge regression using time features (t, day-of-year sin/cos), lags (1,7,30), rolling means, and optionally a quantity series from a matching `dataset/*quantity*.csv` file as an exogenous feature. The code trains on existing data and then recursively forecasts H steps ahead.
  - Residuals from the fitted model are used to compute quantile-based intervals (80/90/95) for uncertainty.
  - The fallback returns the same dict shape as the ensemble predictor so the CLI can render identical output.

9) CLI output formatting & display
  - The handler receives the prediction dict and prints:
    - A 30-day calendar overview and an ASCII sparkline of `yhat`.
    - A day-by-day summary (₹/quintal and conversion to ₹/kg) and 80% CI per day.
    - A simple trend indicator (slope over the forecast: increasing/decreasing/stable).
    - A market comparison table computed from `df_feat` that shows min/max/modal per market for the same commodity (labeled columns). It prints the TOP RECOMMENDATION (market with highest modal) and potential extra profit vs the runner-up.

10) Units, logging and artifacts
   - Forecast numbers are in ₹/quintal; the CLI converts to ₹/kg for some printed lines (divide by 100).
   - If no ensemble exists the log shows a WARNING `Model not found` and the fallback is used. If an ensemble exists, you will see fewer warnings and possibly Optuna logs during training runs.
   - Predictions are not saved to disk by default; if you need programmatic output or CSV exports, the codebase can be extended (I can add `--export-csv` if desired).

11) Example runtime traces you may see
   - INFO lines: "Loading CSV: ...", "Filtered to Telangana-Hyderabad: N rows"
   - WARNING line when model artifact missing: "Model not found: ...; using fallback historical stats predictor"
   - If statsmodels is used: statsmodels may warn about missing frequency on the index (harmless for forecasting in this code, but you can add an index frequency to silence warnings).

This section maps each CLI-visible behavior back to the function that implements it so contributors can quickly find where to modify preprocessing, features, models, or display formatting.

4) Hybrid (ensemble) training (optional)
  - Purpose: train stronger models (XGBoost, Prophet, LSTM) and a stacking/meta model. Requires heavy dependencies.

Quick mode (faster, fewer trials):
```powershell
python .\farmer_price_predictor.py hybrid-train --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --quick
```

Batch across all CSVs in `dataset/`:
```powershell
python .\farmer_price_predictor.py hybrid-train --all --quick
```

5) Prediction using trained ensemble
  - After `hybrid-train` completes, an artifact `models/ensemble_<Commodity>_<Market>.joblib` will be saved and used automatically by `predict`.

```powershell
python .\farmer_price_predictor.py predict --data brinjal_price_data2021-2024.csv --market "Bowenpally" --commodity "brinjal" --horizon 30
```

6) Market comparison and top-summary
  - Compare markets and check the top recommendation.

```powershell
python .\farmer_price_predictor.py compare --data brinjal_price_data2021-2024.csv
python .\farmer_price_predictor.py top-summary --data potato_price_data2021-2024.csv
```

## 7. Output artifacts and naming conventions
- Ensemble artifacts: `models/ensemble_{commodity}_{market}.joblib` (capitalization is normalized by code when building names)
- Exported CSVs (if enabled): any `--export-csv` outputs will be saved to the working directory unless a path is provided.

## 8. Logging & diagnostics
- The CLI prints informative logs (INFO/WARNING/ERROR). Redirect stdout/stderr to files when running on a schedule.
- Common log messages:
  - `Filtered to Telangana-Hyderabad` — data was filtered to region subset used by the project
  - `Model not found` — no ensemble artifact exists; fallback used
  - Optuna logs — show tuning progress if hybrid-train runs

## 9. Troubleshooting and tips
- If `predict` prints identical values for many days:
  - The fallback may be using a short history or a mean forecast. Try installing `statsmodels` for Holt-Winters, or run `hybrid-train` for model-based forecasts.
- If `TOP RECOMMENDATION` repeatedly shows the same market:
  - Run `top-summary` to see whether that market is top across many commodities. If you prefer profit-driven ranking, request the profit-based ranking feature.
- If `prophet` or `tensorflow` fail to install on Windows, use conda or run training on Linux/machine with those dependencies.

## 10. Extending the pipeline
- Add new model wrappers under `models/` following the train/load/predict pattern.
- Improve feature engineering in `feature_engineering.py` (add weather, holiday regressors, or external demand signals).
- Add a `profit-summary` mode that uses quantity CSVs and transport-cost assumptions to rank markets by expected profit.

## 11. Quick checklist for a new user
1. Create and activate venv
2. pip install -r requirements.txt
3. (Optional) pip install statsmodels
4. Place CSVs in `dataset/`
5. Run preflight -> predict -> (optional) hybrid-train -> predict

---
If you want, I can:
- Add `profit-summary` that ranks markets by estimated revenue using quantity files.
- Add `--export-csv` flags to `predict` and `top-summary` to produce CSV reports.
- Create a small Jupyter demo that loads a single commodity and shows model vs fallback comparison plots.

Tell me which follow-up you want and I'll implement it next.

## Command walkthroughs — step-by-step (so simple a kid can follow)

Below are four exact commands and a very clear, end-to-end explanation of what happens after you run each one. Read the short "What you will see" section first, then the numbered steps that explain exactly what the program does behind the scenes.

### 1) Predict one-day forecast for potato in L B Nagar

Command (PowerShell):

```powershell
python .\farmer_price_predictor.py predict --data potato_price_data2021-2024.csv --market "L B Nagar" --commodity "potato" --horizon 1
```

What you will see (quick):
- Several INFO lines about loading the CSV and filtering region.
- Either a warning "Model not found" followed by a nice 1-day forecast (fallback), or a short block showing the ensemble prediction (if a trained model exists).
- A tiny table or paragraph showing the predicted price for the next day and an uncertainty interval (e.g. 80% interval).

Step-by-step (what the program does, super simple):
1. The program reads the file `dataset\potato_price_data2021-2024.csv` into memory. If you gave only the filename, the tool looks inside the `dataset/` folder for it.
2. It keeps only rows for the Telangana / Hyderabad region — that is the project's default focus.
3. It looks for a date column named `date` or `t` (the loader accepts either). It turns that column into real calendar dates so the program knows which day each row belongs to.
4. It keeps only rows where `market_name` matches "L B Nagar" (case-insensitive) and `cmdty` matches "potato". This gives a small table of past prices just for that market and crop.
5. The program checks whether a trained ensemble model exists on disk at `models/ensemble_potato_l b nagar.joblib` (names are normalized inside the code). Two possibilities:
  - If the ensemble model is found: the code loads it and asks each base model (XGBoost, Prophet, LSTM if present) to predict the next day. Then a small meta model combines those base predictions into one final number and the program prints the forecast and its interval.
  - If the ensemble model is NOT found: the program prints a short WARNING "Model not found" and uses the fallback predictor. The fallback first tries a statistics method (Holt–Winters) if `statsmodels` is installed; otherwise it uses a simple learned model (ridge regression with time features and recent lags). That fallback always returns a prediction and an uncertainty range.
6. The CLI prints the result in friendly language, for example: "Predicted modal price for 2025-09-26: ₹X per quintal (80% CI: ₹A–₹B)." It also prints a tiny one-line trend (rising / falling / flat).

How to read common messages and what to do:
- "Loading CSV:" — normal; it means your file was found and opened.
- "Filtered to Telangana-Hyderabad: N rows" — normal; N is how many rows remained after filtering for the region.
- "Model not found" — you will still get a forecast; it means we used a simple fallback method. To get the fancy ensemble forecast, run the hybrid-train step (see command 3 below).
- If the program errors with a message about missing columns like `p_modal`, open the CSV and make sure it has a column named `p_modal` or `p_min`/`p_max`/`p_modal` as expected.

---

### 2) Show top-summary from brinjal dataset

Command (PowerShell):

```powershell
python .\farmer_price_predictor.py top-summary --data brinjal_price_data2021-2024.csv
```

What you will see (quick):
- A small table that lists markets and shows which market is the "top" one for brinjal (e.g., the market with the highest modal price). It will also show counts or percentages if the command aggregates across many days.

Step-by-step (what the program does):
1. The CLI opens `dataset\brinjal_price_data2021-2024.csv` and loads it into memory.
2. It cleans the dates and filters to the Telangana / Hyderabad region just like the `predict` command.
3. It groups the data by market and computes simple numbers: modal price (most common reported modal price), the minimum and maximum historic modal prices, and how often a market was the highest on a given day.
4. It ranks markets by the aggregated metric (by default the modal price or a simple count of 'top' days) and prints the results in an easy table with labeled columns.

How to read common messages and what to do:
- If many rows are missing or the CSV is the wrong file, the table may be empty — check that the CSV contains `t`/`date`, `cmdty`, `market_name`, and `p_modal` columns.
- If you want the ranking to use revenue or quantity-aware profit, that feature isn't enabled by default — ask me and I can add a `profit-summary` mode that uses the quantity CSVs.

---

### 3) Train a hybrid ensemble for potato in L B Nagar (single market)

Command (PowerShell):

```powershell
python .\farmer_price_predictor.py hybrid-train --data potato_price_data2021-2024.csv --market "L B Nagar" --commodity "potato"
```

What you will see (quick):
- Many INFO lines showing training progress. If heavy libraries are present you may also see Optuna tuning logs and XGBoost status messages. At the end you will see a message like "Ensemble saved to models/ensemble_potato_l b nagar.joblib".

Step-by-step (what the program does):
1. Loads `dataset\potato_price_data2021-2024.csv` and filters to "L B Nagar" and "potato" like the other commands.
2. Builds training features (lags, rolling means, time-of-year, day-of-week) so the models can learn patterns.
3. Trains one or more base models. By default the trainer attempts to train:
  - XGBoost: a fast tree model (usually works on most machines).
  - Prophet: a time-series model that captures trend and seasonality (requires the `prophet` package).
  - LSTM: a neural network that learns sequential patterns (requires TensorFlow/Keras).
  The trainer will skip any base model whose library is not installed and will log a clear INFO message.
4. Optionally, Optuna hyperparameter tuning runs to pick good XGBoost parameters. Optuna prints trials and the chosen best parameters. This step can take time.
5. A stacking (meta) model is trained that learns how to combine the base models' predictions for each horizon day into a final prediction. The trainer also computes residuals (errors) from cross-validation to produce simple prediction intervals.
6. All the trained pieces are saved in one file `models/ensemble_potato_l b nagar.joblib`. From now on the `predict` command will find this file and use the ensemble path (instead of the fallback).

Important notes and common pitfalls:
- This command is the heaviest: it needs extra libraries (xgboost is usually enough for a usable model). If you don't have Prophet or TensorFlow installed, the trainer will still work and simply skip those parts.
- Training can take minutes or longer on a laptop. If you want a faster trial run, use `--quick` (see next command) which trains a smaller model set and fewer Optuna trials.
- If you see errors mentioning missing columns in quantity files (for example an ERROR like "None of [Index(['p_min', 'p_max', 'p_modal'], dtype='object')] are in the [columns]"), that means the training code tried to read a quantity CSV as if it were a price CSV. The trainer logs which filename caused the error — double-check dataset file names and formats.

---

### 4) Train all CSVs quickly (batch quick mode)

Command (PowerShell):

```powershell
python .\farmer_price_predictor.py hybrid-train --all --quick
```

What you will see (quick):
- The program iterates through every price CSV it finds in `dataset/` and attempts a fast training job for each. You will see INFO lines per file and at the end a summary like "Batch hybrid training finished for files: [...]". For some files you may see ERROR logs (for data-format issues) — those files are skipped.

Step-by-step (what the program does):
1. It lists all CSV files inside the `dataset/` folder and picks the price CSVs by name pattern.
2. For each CSV file (like `potato_price_data2021-2024.csv`) it runs the same training flow described in step 3, but with shortcuts:
  - `--quick` reduces the number of Optuna trials or uses a single fast XGBoost training configuration.
  - `--quick` may skip heavy models (LSTM/Prophet) on some setups to finish quickly.
3. For each successful file, a model file is saved inside `models/`, usually named `xgb_<Commodity>_<Market>.model` (base XGBoost) and, when the stacking step completes, an ensemble `.joblib` file like `ensemble_<Commodity>_<Market>.joblib`.
4. If the training fails for some CSV (for example, the code tries to open a quantity CSV and expects price columns), the error is logged and the file is skipped; training continues for the remaining files.

Why you might see only `xgb_..._Bowenpally.model` files in `models/` (common question):
- The quick batch run often successfully trains XGBoost for markets that have enough clean data and saves those base XGBoost models. If some markets have little data, or if the stacking step failed, you may only see XGBoost files for a few markets (for example Bowenpally) and no `ensemble_...` joblib files for others. To produce full ensemble files for every market, run the non-quick training per-market on a machine with all optional libraries installed.

How to verify the results after training:
- Look in the `models/` folder. Successful outputs include:
  - `xgb_<Commodity>_<Market>.model` — base XGBoost model file
  - `ensemble_<Commodity>_<Market>.joblib` — full stacked ensemble (used automatically by `predict`)
- Run a quick `predict` for a market you just trained; if the ensemble exists, the warn message will not appear and the ensemble forecast will be used.

