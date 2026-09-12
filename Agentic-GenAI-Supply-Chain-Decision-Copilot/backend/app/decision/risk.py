from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


def project_inventory_timeline(
    current_stock: int,
    incoming_orders: List[Dict[str, Any]],
    forecast_items: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str], float, List[Dict[str, Any]]]:
    """
    Simulates inventory trajectory over the forecast horizon.
    Returns: (projected_stockout: bool, projected_stockout_date: Optional[str], min_projected_stock: float, timeline: List)
    """
    sim_stock = float(current_stock)
    stockout_date = None
    has_stockout = False
    min_stock = sim_stock

    # Map incoming PO quantities by expected_date
    incoming_by_date = {}
    for po in incoming_orders:
        exp_dt = po.get("expected_date")
        if exp_dt:
            incoming_by_date[exp_dt] = incoming_by_date.get(exp_dt, 0) + po.get("quantity", 0)

    timeline = []

    for item in forecast_items:
        dt_str = item["date"]
        demand = float(item["predicted_demand"])
        incoming = float(incoming_by_date.get(dt_str, 0))

        sim_stock = sim_stock + incoming - demand
        if sim_stock < min_stock:
            min_stock = sim_stock

        if sim_stock <= 0 and not has_stockout:
            has_stockout = True
            stockout_date = dt_str

        timeline.append({
            "date": dt_str,
            "incoming": incoming,
            "demand": demand,
            "projected_stock": round(sim_stock, 1)
        })

    return has_stockout, stockout_date, round(min_stock, 1), timeline


def calculate_risk_score(
    inventory_position: int,
    reorder_point: int,
    safety_stock: int,
    has_stockout: bool,
    days_of_inventory: Optional[float],
    lead_time_days: int
) -> Tuple[int, str]:
    """
    Calculates transparent risk score (0-100) and maps to risk level.
    
    Scoring components:
    - Projected Stockout occurs within horizon: +35 pts
    - Inventory Position <= Safety Stock: +30 pts
    - Inventory Position <= Reorder Point: +20 pts
    - Days of Inventory < Supplier Lead Time: +15 pts
    """
    score = 0

    if has_stockout:
        score += 35

    if inventory_position <= safety_stock:
        score += 30
    elif inventory_position <= reorder_point:
        score += 20

    if days_of_inventory is not None and days_of_inventory < lead_time_days:
        score += 15

    score = min(100, max(0, score))

    if score >= 75:
        level = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level


def generate_deterministic_reasons(
    inventory_position: int,
    reorder_point: int,
    safety_stock: int,
    days_of_inventory: Optional[float],
    lead_time_days: int,
    has_stockout: bool,
    stockout_date: Optional[str]
) -> List[str]:
    """
    Generates structured factual evidence statements for the risk assessment.
    """
    reasons = []

    if has_stockout and stockout_date:
        reasons.append(f"Projected stockout detected on {stockout_date} before replenishment arrival.")

    if inventory_position <= safety_stock:
        reasons.append(f"Inventory position ({inventory_position} units) has breached safety stock threshold ({safety_stock} units).")
    elif inventory_position <= reorder_point:
        reasons.append(f"Inventory position ({inventory_position} units) is below reorder point ({reorder_point} units).")

    if days_of_inventory is not None and days_of_inventory < lead_time_days:
        reasons.append(f"Days of inventory coverage ({days_of_inventory} days) is less than supplier lead time ({lead_time_days} days).")

    if not reasons:
        reasons.append("Inventory levels are healthy and exceed reorder thresholds.")

    return reasons
