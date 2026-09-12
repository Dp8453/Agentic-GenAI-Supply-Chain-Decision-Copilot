import math
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.decision.inventory import (
    calculate_inventory_position, calculate_safety_stock, calculate_reorder_point, calculate_days_of_inventory
)
from app.decision.risk import calculate_risk_score, project_inventory_timeline
from app.ml.predict import forecast_product
from app.simulation.schemas import BaselineMetrics, SimulatedMetrics, SimulationScenario

logger = logging.getLogger(__name__)


def simulate_supplier_delay(
    baseline: BaselineMetrics,
    scenario: SimulationScenario,
    db: Optional[Session] = None
) -> SimulatedMetrics:
    """
    Simulates the impact of a supplier delivery delay (delay_days).
    Incoming orders are pushed back by delay_days in the projected inventory timeline.
    """
    delay_days = scenario.delay_days or 7
    effective_lead_time = baseline.lead_time_days + delay_days

    # Fetch daily forecast items
    try:
        fc_res = forecast_product(
            product_id=baseline.product_id,
            horizon_days=scenario.horizon_days,
            db=db
        )
        forecast_items = fc_res.get("forecast", [])
    except Exception:
        forecast_items = []

    # Shift incoming PO expected dates by delay_days
    shifted_incoming_orders = []
    if baseline.incoming_quantity > 0:
        base_date = datetime.utcnow() + timedelta(days=delay_days)
        exp_date_str = base_date.strftime("%Y-%m-%d")
        shifted_incoming_orders.append({
            "expected_date": exp_date_str,
            "quantity": baseline.incoming_quantity
        })

    # Run inventory timeline projection with delayed PO timing
    has_stockout, stockout_date, min_stock, _ = project_inventory_timeline(
        current_stock=baseline.current_stock,
        incoming_orders=shifted_incoming_orders,
        forecast_items=forecast_items
    )

    avg_demand = baseline.average_daily_demand
    sim_forecast_demand = round(avg_demand * effective_lead_time, 2)
    sim_safety_stock = calculate_safety_stock(avg_demand, avg_demand * 0.2, float(effective_lead_time), 2.0)
    sim_reorder_point = calculate_reorder_point(sim_forecast_demand, sim_safety_stock)
    sim_inv_pos = calculate_inventory_position(baseline.current_stock, baseline.incoming_quantity, baseline.reserved_stock)
    sim_days_inv = calculate_days_of_inventory(baseline.current_stock, avg_demand)

    sim_score, sim_level = calculate_risk_score(
        inventory_position=sim_inv_pos,
        reorder_point=sim_reorder_point,
        safety_stock=sim_safety_stock,
        has_stockout=has_stockout,
        days_of_inventory=sim_days_inv,
        lead_time_days=effective_lead_time
    )

    return SimulatedMetrics(
        product_id=baseline.product_id,
        sku=baseline.sku,
        current_stock=baseline.current_stock,
        incoming_quantity=baseline.incoming_quantity,
        inventory_position=sim_inv_pos,
        average_daily_demand=avg_demand,
        forecast_demand_lead_time=sim_forecast_demand,
        lead_time_days=effective_lead_time,
        safety_stock=sim_safety_stock,
        reorder_point=sim_reorder_point,
        days_of_inventory=sim_days_inv,
        projected_stockout=has_stockout,
        projected_stockout_date=stockout_date,
        risk_score=sim_score,
        risk_level=sim_level
    )


def simulate_demand_change(
    baseline: BaselineMetrics,
    scenario: SimulationScenario,
    db: Optional[Session] = None
) -> SimulatedMetrics:
    """
    Simulates a percentage change in daily demand (+X% or -X%).
    """
    pct_change = scenario.demand_change_percent or 20.0
    multiplier = 1.0 + (pct_change / 100.0)
    sim_avg_demand = round(max(0.1, baseline.average_daily_demand * multiplier), 2)

    # Scale daily forecast items by multiplier
    try:
        fc_res = forecast_product(
            product_id=baseline.product_id,
            horizon_days=scenario.horizon_days,
            db=db
        )
        forecast_items = fc_res.get("forecast", [])
        scaled_forecast = [{
            "date": item["date"],
            "predicted_demand": round(item["predicted_demand"] * multiplier, 2)
        } for item in forecast_items]
    except Exception:
        scaled_forecast = []

    incoming_orders = []
    if baseline.incoming_quantity > 0:
        incoming_orders.append({
            "expected_date": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "quantity": baseline.incoming_quantity
        })

    has_stockout, stockout_date, _, _ = project_inventory_timeline(
        current_stock=baseline.current_stock,
        incoming_orders=incoming_orders,
        forecast_items=scaled_forecast
    )

    sim_forecast_demand = round(sim_avg_demand * baseline.lead_time_days, 2)
    sim_safety_stock = calculate_safety_stock(sim_avg_demand, sim_avg_demand * 0.2, float(baseline.lead_time_days), 2.0)
    sim_reorder_point = calculate_reorder_point(sim_forecast_demand, sim_safety_stock)
    sim_inv_pos = calculate_inventory_position(baseline.current_stock, baseline.incoming_quantity, baseline.reserved_stock)
    sim_days_inv = calculate_days_of_inventory(baseline.current_stock, sim_avg_demand)

    sim_score, sim_level = calculate_risk_score(
        inventory_position=sim_inv_pos,
        reorder_point=sim_reorder_point,
        safety_stock=sim_safety_stock,
        has_stockout=has_stockout,
        days_of_inventory=sim_days_inv,
        lead_time_days=baseline.lead_time_days
    )

    return SimulatedMetrics(
        product_id=baseline.product_id,
        sku=baseline.sku,
        current_stock=baseline.current_stock,
        incoming_quantity=baseline.incoming_quantity,
        inventory_position=sim_inv_pos,
        average_daily_demand=sim_avg_demand,
        forecast_demand_lead_time=sim_forecast_demand,
        lead_time_days=baseline.lead_time_days,
        safety_stock=sim_safety_stock,
        reorder_point=sim_reorder_point,
        days_of_inventory=sim_days_inv,
        projected_stockout=has_stockout,
        projected_stockout_date=stockout_date,
        risk_score=sim_score,
        risk_level=sim_level
    )


def simulate_lead_time_change(
    baseline: BaselineMetrics,
    scenario: SimulationScenario,
    db: Optional[Session] = None
) -> SimulatedMetrics:
    """
    Simulates a change in supplier lead-time duration (+X days or -X days).
    """
    lt_change = scenario.lead_time_change_days or 10
    sim_lead_time = max(1, baseline.lead_time_days + lt_change)

    sim_forecast_demand = round(baseline.average_daily_demand * sim_lead_time, 2)
    sim_safety_stock = calculate_safety_stock(baseline.average_daily_demand, baseline.average_daily_demand * 0.2, float(sim_lead_time), 2.0)
    sim_reorder_point = calculate_reorder_point(sim_forecast_demand, sim_safety_stock)
    sim_inv_pos = calculate_inventory_position(baseline.current_stock, baseline.incoming_quantity, baseline.reserved_stock)
    sim_days_inv = calculate_days_of_inventory(baseline.current_stock, baseline.average_daily_demand)

    has_stockout = sim_days_inv < sim_lead_time
    stockout_date = (datetime.utcnow() + timedelta(days=int(sim_days_inv))).strftime("%Y-%m-%d") if has_stockout and sim_days_inv is not None else None

    sim_score, sim_level = calculate_risk_score(
        inventory_position=sim_inv_pos,
        reorder_point=sim_reorder_point,
        safety_stock=sim_safety_stock,
        has_stockout=has_stockout,
        days_of_inventory=sim_days_inv,
        lead_time_days=sim_lead_time
    )

    return SimulatedMetrics(
        product_id=baseline.product_id,
        sku=baseline.sku,
        current_stock=baseline.current_stock,
        incoming_quantity=baseline.incoming_quantity,
        inventory_position=sim_inv_pos,
        average_daily_demand=baseline.average_daily_demand,
        forecast_demand_lead_time=sim_forecast_demand,
        lead_time_days=sim_lead_time,
        safety_stock=sim_safety_stock,
        reorder_point=sim_reorder_point,
        days_of_inventory=sim_days_inv,
        projected_stockout=has_stockout,
        projected_stockout_date=stockout_date,
        risk_score=sim_score,
        risk_level=sim_level
    )


def simulate_inventory_transfer(
    baseline: BaselineMetrics,
    scenario: SimulationScenario,
    db: Optional[Session] = None
) -> SimulatedMetrics:
    """
    Simulates transferring inventory quantity into or out of the target product stock.
    Demonstrates total inventory conservation across locations.
    """
    transfer_qty = scenario.transfer_quantity or 500
    sim_stock = max(0, baseline.current_stock + transfer_qty)
    sim_inv_pos = calculate_inventory_position(sim_stock, baseline.incoming_quantity, baseline.reserved_stock)
    sim_days_inv = calculate_days_of_inventory(sim_stock, baseline.average_daily_demand)

    has_stockout = sim_days_inv < baseline.lead_time_days if sim_days_inv is not None else False
    stockout_date = (datetime.utcnow() + timedelta(days=int(sim_days_inv))).strftime("%Y-%m-%d") if has_stockout and sim_days_inv is not None else None

    sim_score, sim_level = calculate_risk_score(
        inventory_position=sim_inv_pos,
        reorder_point=baseline.reorder_point,
        safety_stock=baseline.safety_stock,
        has_stockout=has_stockout,
        days_of_inventory=sim_days_inv,
        lead_time_days=baseline.lead_time_days
    )

    return SimulatedMetrics(
        product_id=baseline.product_id,
        sku=baseline.sku,
        current_stock=sim_stock,
        incoming_quantity=baseline.incoming_quantity,
        inventory_position=sim_inv_pos,
        average_daily_demand=baseline.average_daily_demand,
        forecast_demand_lead_time=baseline.forecast_demand_lead_time,
        lead_time_days=baseline.lead_time_days,
        safety_stock=baseline.safety_stock,
        reorder_point=baseline.reorder_point,
        days_of_inventory=sim_days_inv,
        projected_stockout=has_stockout,
        projected_stockout_date=stockout_date,
        risk_score=sim_score,
        risk_level=sim_level
    )
