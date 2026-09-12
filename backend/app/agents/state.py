from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """
    Strongly typed shared state for the LangGraph Multi-Tool Agent Orchestrator.
    Passed sequentially across nodes (Planner -> Router -> Tools -> Decision -> Validation -> Response).
    """
    question: str
    intent: str
    entities: Dict[str, Any]
    selected_tools: List[str]
    plan_reasoning: str
    tool_results: Dict[str, Any]
    sql_result: Optional[Dict[str, Any]]
    rag_result: Optional[Dict[str, Any]]
    forecast_result: Optional[Dict[str, Any]]
    risk_result: Optional[Dict[str, Any]]
    simulation_result: Optional[Dict[str, Any]]
    decision: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    final_response: Optional[Dict[str, Any]]
    warnings: List[str]
    errors: List[str]
    sources: List[Dict[str, Any]]
    tool_trace: List[Dict[str, Any]]
