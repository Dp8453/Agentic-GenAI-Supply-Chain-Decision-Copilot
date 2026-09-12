import re
import logging
from typing import Dict, Any, Optional, Tuple

from app.llm.provider import LLMProvider
from app.simulation.schemas import ScenarioTypeEnum, SimulationScenario

logger = logging.getLogger(__name__)

SCENARIO_PARSER_PROMPT = """You are the Lead What-If Scenario Parser for SupplyChain AI.
Your objective is to analyze a natural language what-if question and extract a structured SimulationScenario JSON object.

SUPPORTED SCENARIO TYPES:
1. SUPPLIER_DELAY: "What if Supplier ABC is delayed by 7 days?"
2. DEMAND_INCREASE: "What if demand increases by 20% for SKU-102?"
3. DEMAND_DECREASE: "What if sales drop by 15%?"
4. LEAD_TIME_INCREASE: "What if Supplier ABC's lead time increases by 10 days?"
5. LEAD_TIME_DECREASE: "What if supplier lead time drops by 3 days?"
6. WAREHOUSE_CAPACITY_CHANGE: "What if WH-EAST capacity decreases by 15%?"
7. INVENTORY_TRANSFER: "What if we transfer 500 units from WH-WEST to WH-EAST?"

RULES:
- If a specific SKU or product ID is mentioned, extract it. (Default product_id=1 if unspecified).
- Convert percentages to float values (e.g. 20.0 for 20% increase, -15.0 for 15% decrease).
- Ensure delay_days and transfer_quantity are non-negative integers.

Respond STRICTLY with valid JSON conforming to the SimulationScenario schema:
{
  "scenario_type": "SUPPLIER_DELAY" | "DEMAND_INCREASE" | "DEMAND_DECREASE" | "LEAD_TIME_INCREASE" | "LEAD_TIME_DECREASE" | "WAREHOUSE_CAPACITY_CHANGE" | "INVENTORY_TRANSFER" | "UNKNOWN",
  "product_id": integer or null,
  "sku": string or null,
  "supplier_code": string or null,
  "warehouse_code": string or null,
  "source_warehouse": string or null,
  "destination_warehouse": string or null,
  "delay_days": integer or null,
  "demand_change_percent": float or null,
  "lead_time_change_days": integer or null,
  "capacity_change_percent": float or null,
  "transfer_quantity": integer or null,
  "horizon_days": 14,
  "description": "Short explanation of the scenario"
}
"""


def _heuristic_parse_scenario(question: str) -> SimulationScenario:
    """
    Deterministic rule-based fallback scenario parser using regex keyword patterns.
    Guarantees robust parsing offline or if LLM fails.
    """
    q_lower = question.lower()

    # Extract Product / SKU
    prod_id = 1
    sku_str = "SKU-001"
    sku_match = re.search(r"sku[-_]?(\d+)", q_lower)
    if sku_match:
        raw_num = int(sku_match.group(1))
        prod_id = ((raw_num - 1) % 5) + 1
        sku_str = f"SKU-{prod_id:03d}"
    else:
        prod_match = re.search(r"product\s+(\d+)", q_lower)
        if prod_match:
            raw_num = int(prod_match.group(1))
            prod_id = ((raw_num - 1) % 5) + 1
            sku_str = f"SKU-{prod_id:03d}"

    # Extract Numbers
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", q_lower)
    pct_val = float(pct_match.group(1)) if pct_match else 20.0

    days_match = re.search(r"(\d+)\s*days?", q_lower)
    days_val = int(days_match.group(1)) if days_match else 7

    qty_match = re.search(r"(\d+)\s*units?", q_lower)
    qty_val = int(qty_match.group(1)) if qty_match else 500

    # Determine Scenario Type
    if "transfer" in q_lower:
        wh_matches = re.findall(r"wh[-_]?[a-z0-9]+", q_lower)
        src_wh = wh_matches[0].upper() if len(wh_matches) > 0 else "WH-WEST"
        dst_wh = wh_matches[1].upper() if len(wh_matches) > 1 else "WH-EAST"
        return SimulationScenario(
            scenario_type=ScenarioTypeEnum.INVENTORY_TRANSFER,
            product_id=prod_id,
            sku=sku_str,
            source_warehouse=src_wh,
            destination_warehouse=dst_wh,
            transfer_quantity=qty_val,
            description=f"Transfer {qty_val} units of {sku_str} from {src_wh} to {dst_wh}"
        )
    elif "delay" in q_lower:
        return SimulationScenario(
            scenario_type=ScenarioTypeEnum.SUPPLIER_DELAY,
            product_id=prod_id,
            sku=sku_str,
            supplier_code="SUP-001",
            delay_days=days_val,
            description=f"Supplier delay of {days_val} days for {sku_str}"
        )
    elif "demand" in q_lower or "sale" in q_lower:
        if "decrease" in q_lower or "drop" in q_lower or "fall" in q_lower:
            return SimulationScenario(
                scenario_type=ScenarioTypeEnum.DEMAND_DECREASE,
                product_id=prod_id,
                sku=sku_str,
                demand_change_percent=-abs(pct_val),
                description=f"Demand decrease of {pct_val}% for {sku_str}"
            )
        else:
            return SimulationScenario(
                scenario_type=ScenarioTypeEnum.DEMAND_INCREASE,
                product_id=prod_id,
                sku=sku_str,
                demand_change_percent=abs(pct_val),
                description=f"Demand increase of {pct_val}% for {sku_str}"
            )
    elif "lead time" in q_lower or "lead-time" in q_lower:
        if "decrease" in q_lower or "drop" in q_lower:
            return SimulationScenario(
                scenario_type=ScenarioTypeEnum.LEAD_TIME_DECREASE,
                product_id=prod_id,
                sku=sku_str,
                lead_time_change_days=-abs(days_val),
                description=f"Lead time decrease of {days_val} days for {sku_str}"
            )
        else:
            return SimulationScenario(
                scenario_type=ScenarioTypeEnum.LEAD_TIME_INCREASE,
                product_id=prod_id,
                sku=sku_str,
                lead_time_change_days=abs(days_val),
                description=f"Lead time increase of {days_val} days for {sku_str}"
            )
    elif "capacity" in q_lower or "warehouse" in q_lower:
        return SimulationScenario(
            scenario_type=ScenarioTypeEnum.WAREHOUSE_CAPACITY_CHANGE,
            product_id=prod_id,
            sku=sku_str,
            warehouse_code="WH-EAST",
            capacity_change_percent=-abs(pct_val) if "decrease" in q_lower or "drop" in q_lower else abs(pct_val),
            description=f"Warehouse capacity change of {pct_val}% for WH-EAST"
        )
    else:
        return SimulationScenario(
            scenario_type=ScenarioTypeEnum.SUPPLIER_DELAY,
            product_id=prod_id,
            sku=sku_str,
            delay_days=7,
            description=f"Simulated 7-day supplier delay for {sku_str}"
        )


def parse_scenario_from_text(question: str, provider: LLMProvider) -> SimulationScenario:
    """
    Parses a natural language query into a structured SimulationScenario.
    """
    try:
        scenario = provider.generate_structured(
            prompt=f"User Scenario Question: {question}",
            response_schema=SimulationScenario,
            system_prompt=SCENARIO_PARSER_PROMPT
        )
        # Ensure default product_id
        if not scenario.product_id:
            scenario.product_id = 1
            scenario.sku = "SKU-001"
        return scenario
    except Exception as e:
        logger.warning(f"LLM Scenario Parser fallback triggered: {e}")
        return _heuristic_parse_scenario(question)


def validate_scenario(scenario: SimulationScenario) -> Tuple[bool, Optional[str]]:
    """
    Validates scenario parameters for domain constraints and non-negative bounds.
    Returns: (is_valid: bool, error_message: Optional[str])
    """
    if scenario.scenario_type == ScenarioTypeEnum.UNKNOWN:
        return False, "Unrecognized or unsupported scenario type."

    if scenario.delay_days is not None and scenario.delay_days < 0:
        return False, "delay_days must be non-negative."

    if scenario.transfer_quantity is not None and scenario.transfer_quantity < 0:
        return False, "transfer_quantity must be non-negative."

    if scenario.demand_change_percent is not None and scenario.demand_change_percent < -90.0:
        return False, "demand_change_percent cannot be less than -90%."

    if scenario.horizon_days <= 0 or scenario.horizon_days > 90:
        return False, "horizon_days must be between 1 and 90."

    # Map product_id safely (1-5)
    if scenario.product_id:
        scenario.product_id = ((scenario.product_id - 1) % 5) + 1
        scenario.sku = f"SKU-{scenario.product_id:03d}"
    else:
        scenario.product_id = 1
        scenario.sku = "SKU-001"

    return True, None
