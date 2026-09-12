from app.simulation.schemas import SimulationImpact, SimulationRecommendation, ScenarioTypeEnum, SimulationScenario, SimulatedMetrics


def generate_simulation_recommendation(
    simulated: SimulatedMetrics,
    impact: SimulationImpact,
    scenario: SimulationScenario
) -> SimulationRecommendation:
    """
    Produces deterministic advisory recommendations based on simulated scenario outcomes.
    """
    if scenario.scenario_type == ScenarioTypeEnum.INVENTORY_TRANSFER:
        action = "TRANSFER"
        priority = "MEDIUM"
        justification = f"Simulated transfer of {scenario.transfer_quantity} units balances warehouse inventory coverage."
    elif simulated.projected_stockout:
        action = "EXPEDITE"
        priority = "CRITICAL"
        justification = f"Projected stockout on {simulated.projected_stockout_date}. Expedite existing POs or place urgent emergency purchase order."
    elif simulated.risk_level in ["CRITICAL", "HIGH"]:
        action = "REORDER"
        priority = "HIGH"
        justification = f"Simulated risk level is {simulated.risk_level} (Score: {simulated.risk_score}). Initiate inventory replenishment to restore safety stock buffer."
    elif impact.impact_severity in ["MEDIUM", "HIGH"]:
        action = "MONITOR"
        priority = "MEDIUM"
        justification = f"Scenario increases risk by {impact.risk_score_change} pts. Closely monitor supplier lead times and daily sales velocity."
    else:
        action = "MONITOR"
        priority = "LOW"
        justification = "Simulated scenario has minimal impact on stockout risk or inventory position."

    return SimulationRecommendation(
        recommended_action=action,
        priority=priority,
        justification=justification
    )
