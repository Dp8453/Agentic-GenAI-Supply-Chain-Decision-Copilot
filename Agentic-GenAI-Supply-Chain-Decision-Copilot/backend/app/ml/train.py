import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

# Add backend directory to sys.path for direct execution
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    from sklearn.ensemble import HistGradientBoostingRegressor
    HAS_XGBOOST = False

from app.ml.features import prepare_daily_sales, create_features, FEATURE_COLUMNS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "sales.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def train_forecasting_models(sales_df: pd.DataFrame = None):
    print("--- Starting Demand Forecaster Training Pipeline ---")

    if sales_df is None:
        if os.path.exists(DATA_RAW_PATH):
            sales_df = pd.read_csv(DATA_RAW_PATH)
        else:
            raise FileNotFoundError(f"Sales dataset not found at {DATA_RAW_PATH}")

    # 1. Prepare daily aggregated sales and create features
    daily_df = prepare_daily_sales(sales_df)
    dataset = create_features(daily_df)
    
    dataset = dataset.sort_values(by="sale_date").reset_index(drop=True)
    total_samples = len(dataset)
    print(f"Total processed feature records: {total_samples}")

    # 2. Chronological Split (70% Train, 15% Validation, 15% Test)
    train_end = int(total_samples * 0.70)
    val_end = int(total_samples * 0.85)

    train_df = dataset.iloc[:train_end]
    val_df = dataset.iloc[train_end:val_end]
    test_df = dataset.iloc[val_end:]

    print(f"Split sizes -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["quantity"]
    X_val, y_val = val_df[FEATURE_COLUMNS], val_df["quantity"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["quantity"]

    # 3. Train Baseline Model (Seasonal Naive / 7-Day Lag)
    baseline_preds = test_df["lag_7"]
    baseline_mae = float(mean_absolute_error(y_test, baseline_preds))
    baseline_rmse = float(root_mean_squared_error(y_test, baseline_preds))

    print("\n--- Baseline Model (7-Day Seasonal Naive) ---")
    print(f"  Test MAE:  {baseline_mae:.4f}")
    print(f"  Test RMSE: {baseline_rmse:.4f}")

    # 4. Train Gradient Boosting Model (XGBoost or HistGradientBoosting)
    if HAS_XGBOOST:
        model_name = "XGBoost Regressor"
        ml_model = XGBRegressor(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        ml_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    else:
        model_name = "HistGradientBoosting Regressor"
        ml_model = HistGradientBoostingRegressor(
            max_iter=120,
            max_depth=5,
            learning_rate=0.05,
            random_state=42
        )
        ml_model.fit(X_train, y_train)

    ml_test_preds = ml_model.predict(X_test)
    ml_test_preds = np.clip(ml_test_preds, a_min=0, a_max=None)

    ml_mae = float(mean_absolute_error(y_test, ml_test_preds))
    ml_rmse = float(root_mean_squared_error(y_test, ml_test_preds))

    print(f"\n--- {model_name} Demand Forecaster ---")
    print(f"  Test MAE:  {ml_mae:.4f}")
    print(f"  Test RMSE: {ml_rmse:.4f}")

    # 5. Compare & Select Best Model
    selected_model_name = model_name if ml_mae < baseline_mae else "Baseline_SeasonalNaive"
    selected_mae = ml_mae if selected_model_name == model_name else baseline_mae
    selected_rmse = ml_rmse if selected_model_name == model_name else baseline_rmse

    print(f"\n[SUCCESS] Selected Model based on Test MAE: {selected_model_name}")

    # 6. Save Model Artifacts & Metadata
    model_path = os.path.join(ARTIFACTS_DIR, "forecaster.joblib")
    metadata_path = os.path.join(ARTIFACTS_DIR, "metadata.json")

    joblib.dump(ml_model, model_path)

    metadata = {
        "model_name": f"{model_name} Demand Forecaster",
        "version": "1.0.0",
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "training_data_end": str(dataset["sale_date"].max()),
        "selected_model": selected_model_name,
        "features": FEATURE_COLUMNS,
        "metrics": {
            "baseline": {"mae": baseline_mae, "rmse": baseline_rmse},
            "gradient_boosting": {"mae": ml_mae, "rmse": ml_rmse},
            "selected": {"mae": selected_mae, "rmse": selected_rmse}
        }
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model artifact -> {model_path}")
    print(f"Saved metadata -> {metadata_path}")
    print("--- Training Pipeline Completed Successfully! ---")
    return metadata


if __name__ == "__main__":
    train_forecasting_models()
