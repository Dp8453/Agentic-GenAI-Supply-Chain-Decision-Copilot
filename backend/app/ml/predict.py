import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.ml.features import FEATURE_COLUMNS, prepare_daily_sales

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "forecaster.joblib")
METADATA_PATH = os.path.join(ARTIFACTS_DIR, "metadata.json")

_cached_model = None
_cached_metadata = None


def load_model_and_metadata():
    global _cached_model, _cached_metadata
    if _cached_model is None:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(METADATA_PATH):
            raise FileNotFoundError("Trained forecasting model artifact or metadata missing. Run train.py first.")
        _cached_model = joblib.load(MODEL_PATH)
        with open(METADATA_PATH, "r") as f:
            _cached_metadata = json.load(f)
    return _cached_model, _cached_metadata


def forecast_product(
    product_id: int, 
    horizon_days: int = 14, 
    sku: Optional[str] = None,
    sales_df: Optional[pd.DataFrame] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Produces multi-step recursive demand forecasts for a target product.
    Includes numerical output validation (non-negative clipping, finite checks)
    and confidence bounds derived from historical validation MAE.
    """
    if horizon_days <= 0 or horizon_days > 90:
        raise ValueError("horizon_days must be between 1 and 90.")

    model, metadata = load_model_and_metadata()
    mae_error = metadata.get("metrics", {}).get("selected", {}).get("mae", 5.0)

    # Fetch historical sales data
    if sales_df is None:
        if db is not None:
            try:
                from app.database.models import Sale, Product
                prod = db.query(Product).filter(Product.id == product_id).first()
                if prod:
                    sku = prod.sku
                sales = db.query(Sale).filter(Sale.product_id == product_id).order_by(Sale.sale_date.asc()).all()
                if sales:
                    sales_df = pd.DataFrame([{
                        "product_id": s.product_id,
                        "sale_date": str(s.sale_date),
                        "quantity": s.quantity
                    } for s in sales])
            except Exception:
                sales_df = None

        if sales_df is None or sales_df.empty:
            raw_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "sales.csv")
            if os.path.exists(raw_path):
                all_sales = pd.read_csv(raw_path)
                sales_df = all_sales[all_sales["product_id"] == product_id].copy()
                if not sales_df.empty and not sku:
                    sku = f"SKU-{product_id:03d}"

    if sales_df is None or sales_df.empty:
        raise ValueError(f"No historical sales data found for product_id {product_id}")

    # Prepare daily continuous sales series
    daily_df = prepare_daily_sales(sales_df)
    daily_df = daily_df.sort_values(by="sale_date").reset_index(drop=True)

    if len(daily_df) < 28:
        raise ValueError(f"Product {product_id} requires at least 28 days of history for lag calculation.")

    last_date = pd.to_datetime(daily_df["sale_date"].max())
    history_qty = list(daily_df["quantity"].values)
    history_dates = list(pd.to_datetime(daily_df["sale_date"]).values)

    forecast_results = []
    current_date = last_date

    # Multi-step recursive forecasting loop
    for day_step in range(1, horizon_days + 1):
        current_date = current_date + timedelta(days=1)

        # Build feature vector for current_date using past history_qty
        lag_1 = history_qty[-1]
        lag_7 = history_qty[-7] if len(history_qty) >= 7 else history_qty[-1]
        lag_14 = history_qty[-14] if len(history_qty) >= 14 else history_qty[-1]
        lag_28 = history_qty[-28] if len(history_qty) >= 28 else history_qty[-1]

        rolling_mean_7 = float(np.mean(history_qty[-7:]))
        rolling_mean_14 = float(np.mean(history_qty[-14:]))
        rolling_mean_28 = float(np.mean(history_qty[-28:]))

        rolling_std_7 = float(np.std(history_qty[-7:]))
        rolling_std_14 = float(np.std(history_qty[-14:]))

        day_of_week = current_date.dayofweek
        day_of_month = current_date.day
        month = current_date.month
        week_of_year = current_date.isocalendar().week
        trend = (current_date - pd.to_datetime(history_dates[0])).days

        feature_dict = {
            "lag_1": lag_1,
            "lag_7": lag_7,
            "lag_14": lag_14,
            "lag_28": lag_28,
            "rolling_mean_7": rolling_mean_7,
            "rolling_mean_14": rolling_mean_14,
            "rolling_mean_28": rolling_mean_28,
            "rolling_std_7": rolling_std_7,
            "rolling_std_14": rolling_std_14,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "month": month,
            "week_of_year": week_of_year,
            "trend": trend
        }

        X_step = pd.DataFrame([feature_dict])[FEATURE_COLUMNS]
        pred_qty = float(model.predict(X_step)[0])

        # Numerical boundary validation (non-negative, finite checks)
        if np.isnan(pred_qty) or np.isinf(pred_qty):
            pred_qty = 0.0
        else:
            pred_qty = max(0.0, round(pred_qty, 2))

        # Append prediction to history for next recursive step
        history_qty.append(pred_qty)
        history_dates.append(current_date)

        lower_bound = max(0.0, round(pred_qty - 1.5 * mae_error, 2))
        upper_bound = round(pred_qty + 1.5 * mae_error, 2)

        forecast_results.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "predicted_demand": pred_qty,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        })

    return {
        "product_id": product_id,
        "sku": sku or f"SKU-{product_id:03d}",
        "horizon_days": horizon_days,
        "model_used": metadata.get("model_name", "Demand Forecaster"),
        "model_version": metadata.get("version", "1.0.0"),
        "total_predicted_demand": round(sum(f["predicted_demand"] for f in forecast_results), 2),
        "forecast": forecast_results
    }
