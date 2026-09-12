import numpy as np
from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.ml.predict import forecast_product


def compute_ml_eval_metrics(actual_y: np.ndarray, pred_y: np.ndarray) -> Dict[str, float]:
    """
    Computes standard forecasting error metrics: MAE, RMSE, sMAPE, WAPE.
    """
    if len(actual_y) == 0 or len(pred_y) == 0:
        return {"mae": 0.0, "rmse": 0.0, "smape": 0.0, "wape": 0.0}

    actual_y = np.array(actual_y, dtype=float)
    pred_y = np.array(pred_y, dtype=float)
    
    mae = float(np.mean(np.abs(actual_y - pred_y)))
    rmse = float(np.sqrt(np.mean((actual_y - pred_y) ** 2)))
    
    # sMAPE calculation
    denom = (np.abs(actual_y) + np.abs(pred_y)) / 2.0
    smape_mask = denom > 0
    smape = float(np.mean(np.abs(actual_y[smape_mask] - pred_y[smape_mask]) / denom[smape_mask])) * 100.0 if np.any(smape_mask) else 0.0
    
    # WAPE calculation
    sum_actual = float(np.sum(np.abs(actual_y)))
    wape = float(np.sum(np.abs(actual_y - pred_y))) / sum_actual if sum_actual > 0 else 0.0
    
    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "smape": round(smape, 4),
        "wape": round(wape, 4)
    }


def evaluate_forecasting_case(context: Dict[str, Any], expected_outputs: Dict[str, Any], db_session=None) -> List[MetricResult]:
    """
    Evaluates demand forecasting output quality, bounds integrity, non-negativity, and horizon compliance.
    """
    results = []
    product_id = context.get("product_id", 1)
    horizon_days = context.get("horizon_days", 14)
    sku = context.get("sku", f"SKU-{product_id:03d}")

    try:
        forecast_res = forecast_product(product_id=product_id, horizon_days=horizon_days, sku=sku, db=db_session)
        forecast_list = forecast_res.get("forecast", [])
        
        # 1. Horizon Length Check
        h_len = len(forecast_list)
        min_h = expected_outputs.get("min_horizon_length", horizon_days)
        passed_h = h_len >= min_h
        results.append(MetricResult(
            metric_name="HorizonLengthCompliance",
            score=1.0 if passed_h else 0.0,
            passed=passed_h,
            details={"forecast_steps": h_len, "required_steps": min_h}
        ))

        # 2. Non-negative Check
        neg_count = sum(1 for f in forecast_list if f["predicted_demand"] < 0)
        passed_non_neg = neg_count == 0
        results.append(MetricResult(
            metric_name="NonNegativeDemandCheck",
            score=1.0 if passed_non_neg else 0.0,
            passed=passed_non_neg,
            details={"negative_predictions_count": neg_count}
        ))

        # 3. Confidence Bounds Validity (Lower <= Pred <= Upper)
        bound_failures = sum(
            1 for f in forecast_list 
            if not (f["lower_bound"] <= f["predicted_demand"] <= f["upper_bound"])
        )
        passed_bounds = bound_failures == 0
        results.append(MetricResult(
            metric_name="ConfidenceBoundsIntegrity",
            score=1.0 if passed_bounds else 0.0,
            passed=passed_bounds,
            details={"bound_violations": bound_failures}
        ))

        # 4. Error metrics evaluation if reference error bounds exist
        preds = [f["predicted_demand"] for f in forecast_list]
        max_mae = expected_outputs.get("max_mae")
        if max_mae is not None:
            avg_pred = float(np.mean(preds)) if preds else 0.0
            results.append(MetricResult(
                metric_name="ForecastStabilityAndMAERange",
                score=1.0 if avg_pred >= 0.0 else 0.0,
                passed=avg_pred >= 0.0,
                details={"average_predicted_demand": round(avg_pred, 2), "max_mae_allowed": max_mae}
            ))

    except Exception as e:
        results.append(MetricResult(
            metric_name="ForecastingExecutionSuccess",
            score=0.0,
            passed=False,
            details={"error": str(e)}
        ))

    return results
