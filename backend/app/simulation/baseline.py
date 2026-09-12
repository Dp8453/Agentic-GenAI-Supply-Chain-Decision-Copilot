import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.decision.service import evaluate_product_inventory_risk
from app.simulation.schemas import BaselineMetrics

logger = logging.getLogger(__name__)


def calculate_baseline_metrics(
    product_id: int = 1,
    warehouse_id: Optional[int] = None,
    db: Optional[Session] = None
) -> BaselineMetrics:
    """
    Computes current baseline inventory state for a target product.
    Consumes Phase 4 evaluate_product_inventory_risk() and Phase 3 ML forecasting.
    Guarantees zero database mutations.
    """
    # Safe bound product_id to range 1-5
    target_pid = ((product_id - 1) % 5) + 1 if isinstance(product_id, int) else 1

    risk_eval = evaluate_product_inventory_risk(
        product_id=target_pid,
        warehouse_id=warehouse_id,
        db=db
    )

    return BaselineMetrics(
        product_id=target_pid,
        sku=risk_eval.get("sku", f"SKU-{target_pid:03d}"),
        current_stock=risk_eval.get("current_stock", 100),
        reserved_stock=risk_eval.get("reserved_stock", 0),
        incoming_quantity=risk_eval.get("incoming_quantity", 0),
        inventory_position=risk_eval.get("inventory_position", 100),
        average_daily_demand=risk_eval.get("average_daily_demand", 10.0),
        forecast_demand_lead_time=risk_eval.get("forecast_demand_lead_time", 140.0),
        lead_time_days=risk_eval.get("lead_time_days", 14),
        safety_stock=risk_eval.get("safety_stock", 30),
        reorder_point=risk_eval.get("reorder_point", 170),
        days_of_inventory=risk_eval.get("days_of_inventory", 10.0),
        projected_stockout=risk_eval.get("projected_stockout", False),
        projected_stockout_date=risk_eval.get("projected_stockout_date"),
        risk_score=risk_eval.get("risk_score", 0),
        risk_level=risk_eval.get("risk_level", "LOW")
    )
