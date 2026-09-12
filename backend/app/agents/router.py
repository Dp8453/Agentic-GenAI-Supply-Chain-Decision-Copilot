import logging
from typing import Literal
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def route_next_step(state: AgentState) -> Literal["sql_tool_node", "rag_tool_node", "forecast_tool_node", "risk_tool_node", "simulation_tool_node", "decision_node"]:
    """
    LangGraph Conditional Router Function.
    Evaluates selected tools against executed tool results to determine the next graph node.
    Supports sequential multi-tool workflows.
    """
    selected = state.get("selected_tools", [])
    results = state.get("tool_results", {})

    for tool in selected:
        tool_upper = str(tool).upper()
        if tool_upper == "SQL" and "SQL" not in results:
            return "sql_tool_node"
        if tool_upper == "RAG" and "RAG" not in results:
            return "rag_tool_node"
        if tool_upper == "FORECAST" and "FORECAST" not in results:
            return "forecast_tool_node"
        if tool_upper == "RISK" and "RISK" not in results:
            return "risk_tool_node"
        if tool_upper == "SIMULATION" and "SIMULATION" not in results:
            return "simulation_tool_node"

    # All requested tools have executed -> proceed to decision node
    return "decision_node"
