import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.simulation.schemas import ScenarioTypeEnum, SimulationScenario, SimulationResult
from app.simulation.scenarios import validate_scenario
from app.simulation.baseline import calculate_baseline_metrics
from app.simulation.calculations import (
    simulate_supplier_delay, simulate_demand_change, simulate_lead_time_change, simulate_inventory_transfer
)
from app.simulation.impact import calculate_simulation_impact
from app.simulation.recommendations import generate_simulation_recommendation

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Core Deterministic Simulation Engine.
    Executes what-if scenario modeling without mutating database state.
    """

    def run_scenario(
        self,
        scenario: SimulationScenario,
        db: Optional[Session] = None
    ) -> SimulationResult:
        """
        Executes end-to-end deterministic simulation pipeline.
        Pipeline: Scenario Validation -> Baseline Loading -> In-Memory Simulation -> Impact Analysis -> Recommendation
        """
        # 1. Validate scenario parameters
        is_valid, err_msg = validate_scenario(scenario)
        if not is_valid:
            raise ValueError(f"Invalid Simulation Scenario: {err_msg}")

        # 2. Calculate baseline metrics (Non-mutating read from Phase 4 & Phase 3)
        baseline = calculate_baseline_metrics(
            product_id=scenario.product_id or 1,
            warehouse_id=scenario.warehouse_id,
            db=db
        )

        warnings = []

        # 3. Route to deterministic scenario calculation routines
        st = scenario.scenario_type
        if st == ScenarioTypeEnum.SUPPLIER_DELAY:
            simulated = simulate_supplier_delay(baseline, scenario, db=db)
        elif st in [ScenarioTypeEnum.DEMAND_INCREASE, ScenarioTypeEnum.DEMAND_DECREASE]:
            simulated = simulate_demand_change(baseline, scenario, db=db)
        elif st in [ScenarioTypeEnum.LEAD_TIME_INCREASE, ScenarioTypeEnum.LEAD_TIME_DECREASE]:
            simulated = simulate_lead_time_change(baseline, scenario, db=db)
        elif st == ScenarioTypeEnum.INVENTORY_TRANSFER:
            simulated = simulate_inventory_transfer(baseline, scenario, db=db)
        elif st == ScenarioTypeEnum.WAREHOUSE_CAPACITY_CHANGE:
            # Capacity change Proxy modeling
            simulated = simulate_demand_change(baseline, scenario, db=db)
            warnings.append("Warehouse capacity simulation evaluated against unit throughput proxy.")
        else:
            simulated = simulate_supplier_delay(baseline, scenario, db=db)

        # 4. Comparative Impact Delta Analysis
        impact = calculate_simulation_impact(baseline, simulated, scenario)

        # 5. Deterministic Advisory Recommendation
        recommendation = generate_simulation_recommendation(simulated, impact, scenario)

        warnings.append("Simulation results are for decision-support modeling; database records remain unmodified.")

        return SimulationResult(
            scenario=scenario,
            baseline=baseline,
            simulated=simulated,
            impact=impact,
            recommendation=recommendation,
            warnings=warnings
        )
