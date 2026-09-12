import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.agents.schemas import AgentQueryRequest, AgentQueryResponse
from app.agents.state import AgentState
from app.agents.graph import build_agent_graph

logger = logging.getLogger(__name__)


class AgentService:
    """
    High-Level Service Interface for the LangGraph Multi-Tool Agent Orchestrator.
    Handles graph initialization, input state preparation, graph invocation, and output response formatting.
    """

    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name

    def run_agent(
        self,
        question: str,
        supplier_filter: Optional[str] = None,
        top_k: int = 5,
        db: Optional[Session] = None,
        provider_override: Optional[str] = None
    ) -> AgentQueryResponse:
        """
        Executes the full LangGraph Agent Workflow.
        """
        target_provider = provider_override or self.provider_name

        # 1. Run Input Guardrail & Prompt Injection Defense
        from app.guardrails.service import guardrail_service
        in_guard_res = guardrail_service.validate_user_input(question)
        if not in_guard_res.allowed:
            v_msg = in_guard_res.violations[0].message if in_guard_res.violations else "Security policy violation."
            return AgentQueryResponse(
                question=question or "",
                summary="Request blocked by Security Guardrails Layer.",
                intent="BLOCKED",
                answer=f"The query could not be processed safely: {v_msg}",
                risk_level="HIGH",
                affected_products=[],
                recommended_actions=[],
                explanation="Input guardrails blocked request execution to preserve system security.",
                confidence=0.0,
                sources=[],
                data_used=[],
                warnings=[v_msg],
                tool_trace=[{
                    "step": "input_guard",
                    "status": "blocked",
                    "timestamp": "",
                    "detail": v_msg
                }]
            )

        sanitized_question = in_guard_res.sanitized_value or question

        # Build and compile graph
        app = build_agent_graph(db=db, provider_name=target_provider)

        # Initial state
        initial_state: AgentState = {
            "question": sanitized_question,
            "intent": "UNKNOWN",
            "entities": {"supplier": supplier_filter},
            "selected_tools": [],
            "plan_reasoning": "",
            "tool_results": {},
            "warnings": list(in_guard_res.warnings),
            "errors": [],
            "sources": [],
            "tool_trace": [{
                "step": "input_guard",
                "status": "completed",
                "timestamp": "",
                "detail": "Input validation and prompt injection defense passed."
            }]
        }

        # Invoke graph execution with step recursion limit safety
        final_state = app.invoke(
            initial_state,
            config={"recursion_limit": 15}
        )

        final_resp_dict = final_state.get("final_response")
        if not final_resp_dict:
            raise RuntimeError("LangGraph execution completed without producing a final response.")

        return AgentQueryResponse(**final_resp_dict)
