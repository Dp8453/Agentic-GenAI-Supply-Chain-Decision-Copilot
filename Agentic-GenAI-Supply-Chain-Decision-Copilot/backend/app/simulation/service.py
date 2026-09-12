import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.llm.provider import LLMProvider, get_llm_provider
from app.simulation.schemas import SimulationRequest, SimulationResponse, SimulationScenario, SimulationResult
from app.simulation.scenarios import parse_scenario_from_text
from app.simulation.engine import SimulationEngine

logger = logging.getLogger(__name__)

SIMULATION_EXPLANATION_PROMPT = """You are SupplyChain AI Lead What-If Analyst.
Your objective is to provide a clear, grounded natural-language explanation comparing the Baseline metrics against the Simulated scenario results provided below.

RULES FOR NUMERICAL GROUNDING:
1. State exact numbers from the context. Do not alter or round numbers differently.
2. Clearly distinguish BASELINE metrics vs SIMULATED scenario metrics.
3. Highlight the Risk Score change, days of inventory delta, stockout impact, and advisory recommendation.

SIMULATION CONTEXT:
Question / Prompt: {question}
Scenario Type: {scenario_type}
Target SKU: {sku}

Baseline Metrics:
- Current Stock: {b_stock} | Inventory Position: {b_pos}
- Average Daily Demand: {b_demand} units/day
- Lead Time: {b_lt} days | Reorder Point: {b_rop}
- Risk Score: {b_score}/100 ({b_level}) | Stockout: {b_stockout}

Simulated Metrics:
- Current Stock: {s_stock} | Inventory Position: {s_pos}
- Average Daily Demand: {s_demand} units/day
- Lead Time: {s_lt} days | Reorder Point: {s_rop}
- Risk Score: {s_score}/100 ({s_level}) | Stockout: {s_stockout} (Date: {s_stockout_date})

Impact Delta:
- Risk Score Delta: {risk_delta} pts
- Severity: {severity}
- Details: {details}

Advisory Recommendation:
- Action: {rec_action} ({rec_priority})
- Justification: {rec_justification}
"""


class SimulationService:
    """
    High-Level Service Interface for What-If Simulation.
    Orchestrates scenario parsing, deterministic simulation execution, and grounded explanation synthesis.
    """

    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name

    def run_simulation(
        self,
        question: Optional[str] = None,
        scenario: Optional[SimulationScenario] = None,
        db: Optional[Session] = None,
        provider_override: Optional[str] = None
    ) -> SimulationResponse:
        """
        Full End-to-End Simulation Service Pipeline:
        Prompt -> Scenario Parsing -> Validation -> Baseline -> Engine -> Grounded Explanation
        """
        provider = get_llm_provider(provider_override or self.provider_name)

        # 1. Parse or validate scenario
        if scenario is None:
            if not question or not question.strip():
                raise ValueError("Either question string or structured scenario must be provided.")
            scenario_obj = parse_scenario_from_text(question=question, provider=provider)
        else:
            scenario_obj = scenario

        effective_question = question or scenario_obj.description or f"What-if simulation for {scenario_obj.scenario_type.value}"

        # 2. Run deterministic simulation engine
        engine = SimulationEngine()
        sim_res: SimulationResult = engine.run_scenario(scenario=scenario_obj, db=db)

        b = sim_res.baseline
        s = sim_res.simulated
        imp = sim_res.impact
        rec = sim_res.recommendation

        # 3. Generate grounded LLM explanation
        prompt = SIMULATION_EXPLANATION_PROMPT.format(
            question=effective_question,
            scenario_type=scenario_obj.scenario_type.value,
            sku=s.sku,
            b_stock=b.current_stock, b_pos=b.inventory_position, b_demand=b.average_daily_demand, b_lt=b.lead_time_days, b_rop=b.reorder_point, b_score=b.risk_score, b_level=b.risk_level, b_stockout=b.projected_stockout,
            s_stock=s.current_stock, s_pos=s.inventory_position, s_demand=s.average_daily_demand, s_lt=s.lead_time_days, s_rop=s.reorder_point, s_score=s.risk_score, s_level=s.risk_level, s_stockout=s.projected_stockout, s_stockout_date=s.projected_stockout_date or "None",
            risk_delta=imp.risk_score_change,
            severity=imp.impact_severity,
            details="; ".join(imp.details),
            rec_action=rec.recommended_action,
            rec_priority=rec.priority,
            rec_justification=rec.justification
        )

        try:
            explanation = provider.generate(prompt=prompt, system_prompt="Synthesize grounded what-if simulation explanation using exact numbers.")
        except Exception as e:
            logger.warning(f"Simulation explanation generation fallback: {e}")
            explanation = f"What-If Simulation complete for {s.sku}. Risk score shifted from {b.risk_score} ({b.risk_level}) to {s.risk_score} ({s.risk_level}). Advisory Recommendation: {rec.recommended_action}."

        sources = [
            {"source_type": "Deterministic Simulation Engine", "name": "In-Memory What-If Calculator"},
            {"source_type": "Phase 4 Inventory Risk Engine", "name": "Baseline Risk Metrics"},
            {"source_type": "Phase 3 Forecast Model", "name": "XGBoost Demand Forecast"}
        ]

        return SimulationResponse(
            question=effective_question,
            scenario=scenario_obj,
            baseline=b,
            simulated=s,
            impact=imp,
            recommendation=rec,
            explanation=explanation,
            sources=sources,
            warnings=sim_res.warnings
        )
