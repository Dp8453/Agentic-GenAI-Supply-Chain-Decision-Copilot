import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.llm.provider import LLMProvider
from app.llm.schemas import IntentEnum, ExtractedEntities
from app.agents.state import AgentState
from app.agents.schemas import PlannerOutput, ToolEnum

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the Lead Strategic Planner for SupplyChain AI.
Your task is to analyze the user's natural language supply chain question, determine the intent, extract parameters, and select the exact tool(s) required to answer the question accurately and authoritatively.

AVAILABLE TOOLS:
1. SQL: Use when the question asks about database records, aggregations, supplier performance statistics, product lists, active purchase orders, inventory levels across tables, or structured tabular data.
2. RAG: Use when the question asks about written documents, procurement policies, supplier contracts, return rules, delivery SLA clauses, or guidelines.
3. FORECAST: Use when the question asks for future demand predictions, projected sales for a product, or multi-day demand trends.
4. RISK: Use when the question asks about stockout risk, safety stock calculations, reorder points, inventory depletion timelines, or reorder quantity recommendations.
5. SIMULATION: Use when the question asks a hypothetical what-if scenario (e.g. "What happens if Supplier ABC is delayed by 7 days?", "What if demand increases by 20%?", "What if we transfer 500 units from WH-WEST to WH-EAST?").

RULES FOR MULTI-TOOL SELECTION:
- If a question asks a what-if hypothetical scenario, select SIMULATION (and optionally RISK/FORECAST if detailed background metrics are requested).
- If a question asks "Why is SKU X at risk?", select both RISK and FORECAST.
- If a question asks about supplier delay impacts on inventory and contract terms, select SQL, RAG, and RISK (or SIMULATION if hypothetical).
- If only policy information is needed, select RAG.
- If only a SQL query is needed, select SQL.

You MUST respond strictly with valid JSON conforming to the PlannerOutput schema:
{
  "intent": "INVENTORY_RISK" | "FORECAST" | "SUPPLIER_INFORMATION" | "POLICY_QUESTION" | "CONTRACT_QUESTION" | "GENERAL_SUPPLY_CHAIN" | "UNKNOWN",
  "entities": {
    "product_id": integer or null,
    "sku": string or null,
    "supplier": string or null,
    "warehouse_id": integer or null,
    "horizon_days": integer or null
  },
  "tools": ["SQL" | "RAG" | "FORECAST" | "RISK" | "SIMULATION"],
  "reason": "Detailed justification for tool choices."
}
"""


def _heuristic_fallback_planner(question: str) -> PlannerOutput:
    """
    Deterministic rule-based fallback planner used if LLM tool selection fails.
    Prevents API failure or graph crashes.
    """
    q_lower = question.lower()
    tools: List[ToolEnum] = []
    intent = IntentEnum.GENERAL_SUPPLY_CHAIN
    entities = ExtractedEntities()

    # Extract product ID or SKU if present
    import re
    sku_match = re.search(r"sku[-_]?(\d+)", q_lower)
    if sku_match:
        prod_num = int(sku_match.group(1))
        entities.product_id = prod_num
        entities.sku = f"SKU-{prod_num:03d}"
    else:
        prod_match = re.search(r"product\s+(\d+)", q_lower)
        if prod_match:
            prod_num = int(prod_match.group(1))
            entities.product_id = prod_num
            entities.sku = f"SKU-{prod_num:03d}"

    # Determine intent & tools based on keywords
    if "what if" in q_lower or "what happens if" in q_lower or "simulate" in q_lower or "transfer" in q_lower:
        intent = IntentEnum.INVENTORY_RISK
        tools.append(ToolEnum.SIMULATION)

    if "contract" in q_lower or "policy" in q_lower or "clause" in q_lower or "sla" in q_lower or "late deliver" in q_lower:
        if "contract" in q_lower or "clause" in q_lower:
            intent = IntentEnum.CONTRACT_QUESTION
        else:
            intent = IntentEnum.POLICY_QUESTION
        tools.append(ToolEnum.RAG)

    if "risk" in q_lower or "stockout" in q_lower or "reorder" in q_lower or "safety stock" in q_lower:
        if intent == IntentEnum.GENERAL_SUPPLY_CHAIN:
            intent = IntentEnum.INVENTORY_RISK
        if ToolEnum.RISK not in tools and ToolEnum.SIMULATION not in tools:
            tools.append(ToolEnum.RISK)

    if "forecast" in q_lower or "predict" in q_lower or "demand" in q_lower or "future" in q_lower:
        if intent == IntentEnum.GENERAL_SUPPLY_CHAIN:
            intent = IntentEnum.FORECAST
        if ToolEnum.FORECAST not in tools and ToolEnum.SIMULATION not in tools:
            tools.append(ToolEnum.FORECAST)

    if "supplier" in q_lower or "on-time" in q_lower or "which" in q_lower or "how many" in q_lower or "list" in q_lower or "table" in q_lower or "performance" in q_lower:
        if intent == IntentEnum.GENERAL_SUPPLY_CHAIN:
            intent = IntentEnum.SUPPLIER_INFORMATION
        if ToolEnum.SQL not in tools:
            tools.append(ToolEnum.SQL)

    if not tools:
        tools = [ToolEnum.RAG, ToolEnum.SQL]
        intent = IntentEnum.GENERAL_SUPPLY_CHAIN

    return PlannerOutput(
        intent=intent,
        entities=entities,
        tools=tools,
        reason="Heuristic keyword fallback planner applied."
    )


def planner_node(state: AgentState, provider: LLMProvider) -> Dict[str, Any]:
    """
    Planner Node implementation for LangGraph.
    Analyzes user question and returns updated state fields.
    """
    question = state.get("question", "")
    trace = list(state.get("tool_trace", []))
    warnings = list(state.get("warnings", []))

    plan_obj: PlannerOutput
    try:
        plan_obj = provider.generate_structured(
            prompt=f"User Question: {question}",
            response_schema=PlannerOutput,
            system_prompt=PLANNER_SYSTEM_PROMPT
        )
    except Exception as e:
        logger.warning(f"Planner LLM generation failed, switching to heuristic fallback: {e}")
        plan_obj = _heuristic_fallback_planner(question)
        warnings.append(f"Planner LLM fallback triggered: {e}")

    # Convert tool enums to list of strings and authorize against allowlist
    proposed_tools_str = [t.value if isinstance(t, ToolEnum) else str(t) for t in plan_obj.tools]
    
    from app.guardrails.service import guardrail_service
    authorized_tools: List[str] = []
    for tool_name in proposed_tools_str:
        auth_res = guardrail_service.authorize_tool(tool_name, raw_args={"question": question}, current_tool_call_count=len(authorized_tools))
        if auth_res.authorized:
            authorized_tools.append(tool_name)
        else:
            msg = f"Tool authorization blocked execution of proposed tool '{tool_name}': {auth_res.reason}"
            warnings.append(msg)
            logger.warning(msg)

    # Fallback to RAG if all proposed tools were blocked
    if not authorized_tools:
        authorized_tools = ["RAG"]

    trace.append({
        "step": "planner",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "detail": f"Selected tools: {authorized_tools} | Intent: {plan_obj.intent.value}"
    })

    return {
        "intent": plan_obj.intent.value,
        "entities": plan_obj.entities.model_dump(),
        "selected_tools": authorized_tools,
        "plan_reasoning": plan_obj.reason,
        "tool_trace": trace,
        "warnings": warnings
    }
