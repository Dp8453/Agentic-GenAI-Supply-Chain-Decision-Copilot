from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.simulation.service import SimulationService


def evaluate_simulation_case(query: str, context: Dict[str, Any], expected_outputs: Dict[str, Any], db_session=None) -> List[MetricResult]:
    """
    Evaluates what-if simulation counterfactual correctness and verifies zero database mutations.
    """
    results = []
    
    try:
        service = SimulationService(provider_name="fake")
        sim_resp = service.run_simulation(question=query, db=db_session)
        
        baseline = sim_resp.baseline
        simulated = sim_resp.simulated
        impact = sim_resp.impact

        # 1. Counterfactual Property Delta Verification
        demand_mult = context.get("demand_multiplier", 1.0)
        lt_added = context.get("lead_time_added_days", 0)

        counterfactual_valid = True
        if demand_mult > 1.0:
            counterfactual_valid = counterfactual_valid and (simulated.average_daily_demand >= baseline.average_daily_demand)
        if lt_added > 0:
            counterfactual_valid = counterfactual_valid and (simulated.lead_time_days >= baseline.lead_time_days)

        results.append(MetricResult(
            metric_name="CounterfactualPropertyDeltaValid",
            score=1.0 if counterfactual_valid else 0.0,
            passed=counterfactual_valid,
            details={
                "baseline_demand": baseline.average_daily_demand,
                "simulated_demand": simulated.average_daily_demand,
                "baseline_lt": baseline.lead_time_days,
                "simulated_lt": simulated.lead_time_days,
                "risk_score_change": impact.risk_score_change
            }
        ))

        # 2. Database Immutability Check (0 DB mutations)
        zero_mutations = True
        if db_session is not None and hasattr(db_session, "is_dirty"):
            zero_mutations = not db_session.is_dirty and len(db_session.new) == 0 and len(db_session.deleted) == 0

        results.append(MetricResult(
            metric_name="ZeroDatabaseMutationsCheck",
            score=1.0 if zero_mutations else 0.0,
            passed=zero_mutations,
            details={"zero_mutations": zero_mutations}
        ))

    except Exception as e:
        results.append(MetricResult(
            metric_name="SimulationExecutionSuccess",
            score=0.0,
            passed=False,
            details={"error": str(e)}
        ))

    return results
