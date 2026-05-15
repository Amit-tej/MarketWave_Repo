import pandas as pd
import numpy as np
from prediction_engine import predict_with_blended_forecast, fallback_stats_predict

# Create sample data for testing
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
sample_data = pd.DataFrame(
    {
        "p_modal": np.random.uniform(100, 200, 100),
        "cmdty": ["wheat"] * 100,
        "market_name": ["Delhi"] * 100,
    },
    index=dates,
)

# Test predict_with_blended_forecast determinism
print("Testing predict_with_blended_forecast determinism...")
results = []
for i in range(5):
    try:
        result = predict_with_blended_forecast(
            "dummy_ensemble.joblib", sample_data, horizon=10
        )
        results.append(result["yhat"])
        print(f"Run {i + 1}: First 5 predictions: {result['yhat'][:5]}")
    except Exception as e:
        print(f"Run {i + 1} failed: {e}")
        results.append(None)

# Check if all results are identical
if all(r is not None for r in results):
    all_identical = all(np.allclose(results[0], r) for r in results[1:])
    print(f"All predictions identical: {all_identical}")
else:
    print("Some runs failed")

# Test fallback_stats_predict determinism
print("\nTesting fallback_stats_predict determinism...")
results_fallback = []
for i in range(5):
    try:
        result = fallback_stats_predict(sample_data, horizon=10)
        results_fallback.append(result["yhat"])
        print(f"Run {i + 1}: First 5 predictions: {result['yhat'][:5]}")
    except Exception as e:
        print(f"Run {i + 1} failed: {e}")
        results_fallback.append(None)

# Check if all results are identical
if all(r is not None for r in results_fallback):
    all_identical_fallback = all(
        np.allclose(results_fallback[0], r) for r in results_fallback[1:]
    )
    print(f"All fallback predictions identical: {all_identical_fallback}")
else:
    print("Some fallback runs failed")

print("\nTesting edge case: Empty data")
empty_data = pd.DataFrame()
try:
    result = fallback_stats_predict(empty_data, horizon=10)
    print(f"Empty data result: {result['yhat'][:5]}")
except Exception as e:
    print(f"Empty data failed: {e}")

print("\nTesting edge case: Data without p_modal")
no_pmodal_data = sample_data.drop(columns=["p_modal"])
try:
    result = fallback_stats_predict(no_pmodal_data, horizon=10)
    print(f"No p_modal result: {result['yhat'][:5]}")
except Exception as e:
    print(f"No p_modal failed: {e}")
