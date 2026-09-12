import math
from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.decision.inventory import (
    calculate_inventory_position,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_days_of_inventory
)
from app.decision.risk import calculate_risk_score


def evaluate_deterministic_risk_case(context: Dict[str, Any], expected_outputs: Dict[str, Any]) -> List[MetricResult]:
    """
    Evaluates inventory risk metrics and formula accuracy for a given evaluation case context.
    """
    results = []
    
    avg_demand = float(context.get("avg_daily_demand", 0.0))
    lead_time = float(context.get("lead_time_days", 0.0))
    std_demand = float(context.get("std_demand", 0.0))
    service_level_z = float(context.get("service_level_z", 1.65))
    current_stock = int(context.get("current_stock", 0))
    on_order = int(context.get("on_order", 0))
    std_lead_time = float(context.get("std_lead_time", 1.5))
    
    # 1. Inventory Position
    inv_pos = calculate_inventory_position(current_stock, on_order, 0)
    exp_inv_pos = expected_outputs.get("inventory_position")
    if exp_inv_pos is not None:
        passed = (inv_pos == int(exp_inv_pos))
        results.append(MetricResult(
            metric_name="InventoryPositionMatch",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"computed": inv_pos, "expected": exp_inv_pos}
        ))

    # 2. Safety Stock Formula Verification
    ss = calculate_safety_stock(avg_demand, std_demand, lead_time, std_lead_time, service_level_z)
    exp_ss = expected_outputs.get("safety_stock")
    if exp_ss is not None:
        # SS can be rounded or within 5 units tolerance due to ceil vs continuous Z
        diff = abs(ss - float(exp_ss))
        passed = diff <= 5.0
        results.append(MetricResult(
            metric_name="SafetyStockFormulaAccuracy",
            score=max(0.0, 1.0 - (diff / max(1.0, float(exp_ss)))),
            passed=passed,
            details={"computed_ss": ss, "expected_ss": exp_ss, "diff": diff}
        ))

    # 3. Reorder Point Formula Verification
    expected_demand_during_lt = avg_demand * lead_time
    rop = calculate_reorder_point(expected_demand_during_lt, ss)
    exp_rop = expected_outputs.get("reorder_point")
    if exp_rop is not None:
        diff = abs(rop - float(exp_rop))
        passed = diff <= 5.0
        results.append(MetricResult(
            metric_name="ReorderPointFormulaAccuracy",
            score=max(0.0, 1.0 - (diff / max(1.0, float(exp_rop)))),
            passed=passed,
            details={"computed_rop": rop, "expected_rop": exp_rop, "diff": diff}
        ))

    # 4. Risk Level Score Classification
    days_inv = calculate_days_of_inventory(current_stock, avg_demand)
    has_stockout = expected_outputs.get("stockout_risk", False)
    score, risk_level = calculate_risk_score(
        inventory_position=inv_pos,
        reorder_point=rop,
        safety_stock=ss,
        has_stockout=has_stockout,
        days_of_inventory=days_inv,
        lead_time_days=int(lead_time)
    )
    
    exp_risk_level = expected_outputs.get("risk_level")
    if exp_risk_level:
        passed = (risk_level == exp_risk_level)
        results.append(MetricResult(
            metric_name="RiskLevelClassificationAccuracy",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"computed_level": risk_level, "expected_level": exp_risk_level, "risk_score": score}
        ))

    return results
