from typing import List, Optional
from app.simulation.schemas import BaselineMetrics, SimulatedMetrics, SimulationImpact, ScenarioTypeEnum, SimulationScenario


def calculate_simulation_impact(
    baseline: BaselineMetrics,
    simulated: SimulatedMetrics,
    scenario: SimulationScenario
) -> SimulationImpact:
    """
    Computes comparative impact metrics (Baseline vs Simulated).
    Classifies impact severity (LOW, MEDIUM, HIGH, CRITICAL).
    """
    risk_score_change = simulated.risk_score - baseline.risk_score

    days_change = None
    if simulated.days_of_inventory is not None and baseline.days_of_inventory is not None:
        days_change = round(simulated.days_of_inventory - baseline.days_of_inventory, 2)

    stockout_shift = None
    if simulated.projected_stockout and not baseline.projected_stockout:
        stockout_shift = f"New stockout projected on {simulated.projected_stockout_date}"
    elif simulated.projected_stockout and baseline.projected_stockout:
        if simulated.projected_stockout_date != baseline.projected_stockout_date:
            stockout_shift = f"Stockout accelerated from {baseline.projected_stockout_date} to {simulated.projected_stockout_date}"
        else:
            stockout_shift = f"Stockout confirmed on {simulated.projected_stockout_date}"

    # Determine Severity Classification
    if simulated.projected_stockout and risk_score_change >= 20:
        severity = "CRITICAL"
    elif simulated.projected_stockout or risk_score_change >= 15:
        severity = "HIGH"
    elif risk_score_change >= 5 or (days_change is not None and days_change < -2.0):
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Specific deterministic statements
    details = []
    details.append(f"Risk Score shifted from {baseline.risk_score} ({baseline.risk_level}) to {simulated.risk_score} ({simulated.risk_level}) [Delta: +{risk_score_change} pts].")

    if days_change is not None:
        details.append(f"Stock coverage shifted from {baseline.days_of_inventory:.1f} days to {simulated.days_of_inventory:.1f} days [Delta: {days_change:+.1f} days].")

    if stockout_shift:
        details.append(stockout_shift)

    if scenario.scenario_type == ScenarioTypeEnum.SUPPLIER_DELAY:
        details.append(f"Simulated supplier delay of {scenario.delay_days} days extended effective lead time to {simulated.lead_time_days} days.")
    elif scenario.scenario_type in [ScenarioTypeEnum.DEMAND_INCREASE, ScenarioTypeEnum.DEMAND_DECREASE]:
        details.append(f"Simulated demand change of {scenario.demand_change_percent}% adjusted daily demand rate to {simulated.average_daily_demand} units/day.")
    elif scenario.scenario_type == ScenarioTypeEnum.INVENTORY_TRANSFER:
        details.append(f"Simulated transfer of {scenario.transfer_quantity} units adjusted available stock from {baseline.current_stock} to {simulated.current_stock} units.")

    return SimulationImpact(
        risk_score_change=risk_score_change,
        days_of_inventory_change=days_change,
        stockout_date_change=stockout_shift,
        impact_severity=severity,
        details=details
    )
