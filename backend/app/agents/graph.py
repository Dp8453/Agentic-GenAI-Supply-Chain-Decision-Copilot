import logging
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, START, END
from app.llm.provider import LLMProvider, get_llm_provider
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.router import route_next_step
from app.agents.nodes import (
    sql_tool_node, rag_tool_node, forecast_tool_node, risk_tool_node, simulation_tool_node,
    decision_node, validation_node, response_node
)

logger = logging.getLogger(__name__)


def build_agent_graph(
    db: Optional[Session] = None,
    provider_name: Optional[str] = None
) -> Any:
    """
    Constructs and compiles the LangGraph Multi-Tool Agent StateGraph.
    """
    provider = get_llm_provider(provider_name)
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("planner", lambda state: planner_node(state, provider=provider))
    workflow.add_node("sql_tool_node", lambda state: sql_tool_node(state, db=db, provider_override=provider_name))
    workflow.add_node("rag_tool_node", lambda state: rag_tool_node(state, db=db))
    workflow.add_node("forecast_tool_node", lambda state: forecast_tool_node(state, db=db))
    workflow.add_node("risk_tool_node", lambda state: risk_tool_node(state, db=db))
    workflow.add_node("simulation_tool_node", lambda state: simulation_tool_node(state, db=db, provider_override=provider_name))
    workflow.add_node("decision_node", decision_node)
    workflow.add_node("validation_node", validation_node)
    workflow.add_node("response_node", lambda state: response_node(state, provider=provider))

    # 2. Set Entry Point
    workflow.add_edge(START, "planner")

    tool_routing_dict = {
        "sql_tool_node": "sql_tool_node",
        "rag_tool_node": "rag_tool_node",
        "forecast_tool_node": "forecast_tool_node",
        "risk_tool_node": "risk_tool_node",
        "simulation_tool_node": "simulation_tool_node",
        "decision_node": "decision_node"
    }

    # 3. Add Conditional Routing from Planner & Tool Nodes
    workflow.add_conditional_edges("planner", route_next_step, tool_routing_dict)
    workflow.add_conditional_edges("sql_tool_node", route_next_step, tool_routing_dict)
    workflow.add_conditional_edges("rag_tool_node", route_next_step, tool_routing_dict)
    workflow.add_conditional_edges("forecast_tool_node", route_next_step, tool_routing_dict)
    workflow.add_conditional_edges("risk_tool_node", route_next_step, tool_routing_dict)
    workflow.add_conditional_edges("simulation_tool_node", route_next_step, tool_routing_dict)

    # 4. Add Linear Edges from Decision -> Validation -> Response -> END
    workflow.add_edge("decision_node", "validation_node")
    workflow.add_edge("validation_node", "response_node")
    workflow.add_edge("response_node", END)

    # 5. Compile Graph with bounded step limit
    compiled_app = workflow.compile()
    return compiled_app


def get_graph_mermaid() -> str:
    """
    Returns Mermaid diagram string representation of the LangGraph orchestrator graph.
    """
    return """graph TD
    START([START]) --> Planner[Planner Node]
    Planner --> Router{Conditional Router}
    Router -->|SQL selected| SQL[SQL Tool Node]
    Router -->|RAG selected| RAG[RAG Tool Node]
    Router -->|Forecast selected| Forecast[Forecast Tool Node]
    Router -->|Risk selected| Risk[Risk Tool Node]
    SQL --> Router
    RAG --> Router
    Forecast --> Router
    Risk --> Router
    Router -->|All tools done| Decision[Decision Synthesis Node]
    Decision --> Validation[Grounding Validation Node]
    Validation --> Response[Response Generation Node]
    Response --> END([END])
"""
