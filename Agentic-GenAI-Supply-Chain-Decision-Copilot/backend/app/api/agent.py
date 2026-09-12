from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.connection import get_db
from app.agents.schemas import AgentQueryRequest, AgentQueryResponse
from app.agents.service import AgentService
from app.agents.graph import get_graph_mermaid

router = APIRouter(prefix="/agent", tags=["Agent Orchestrator"])


@router.post("/query", response_model=AgentQueryResponse)
def run_agent_query(
    request: AgentQueryRequest,
    db: Session = Depends(get_db)
) -> AgentQueryResponse:
    """
    POST /api/v1/agent/query
    Executes the LangGraph Multi-Tool Agent Orchestrator pipeline.
    Orchestrates Planner Node -> Router -> SQL/RAG/Forecast/Risk Tools -> Decision -> Validation -> Structured Response.
    """
    try:
        agent_service = AgentService(provider_name=request.provider_override)
        response = agent_service.run_agent(
            question=request.question,
            supplier_filter=request.supplier_filter,
            top_k=request.top_k,
            db=db,
            provider_override=request.provider_override
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Agent Execution Error: {str(e)}")


@router.get("/graph", response_model=Dict[str, str])
def get_agent_graph_mermaid() -> Dict[str, str]:
    """
    GET /api/v1/agent/graph
    Returns the Mermaid visualization string representing the LangGraph workflow topology.
    """
    return {
        "format": "mermaid",
        "mermaid": get_graph_mermaid()
    }
