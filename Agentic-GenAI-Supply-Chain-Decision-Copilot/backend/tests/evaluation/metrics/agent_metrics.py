from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.agents.planner import _heuristic_fallback_planner, planner_node
from app.llm.fake_provider import FakeLLMProvider


def evaluate_agent_routing_case(query: str, context: Dict[str, Any], expected_outputs: Dict[str, Any]) -> List[MetricResult]:
    """
    Evaluates agent multi-tool routing precision, tool selection accuracy, and execution step bounds.
    """
    results = []
    
    # 1. Planner routing precision
    plan_obj = _heuristic_fallback_planner(query)
    tools_selected = [t.value for t in plan_obj.tools]
    
    expected_tools = expected_outputs.get("expected_tools", [])
    if expected_tools:
        normalized_selected = {t.lower().replace("_tool", "") for t in tools_selected}
        normalized_expected = {t.lower().replace("_tool", "") for t in expected_tools}
        
        overlap = normalized_selected.intersection(normalized_expected)
        precision = len(overlap) / len(normalized_expected) if normalized_expected else 1.0
        passed_precision = precision >= 0.5
        
        results.append(MetricResult(
            metric_name="ToolRoutingPrecision",
            score=round(precision, 4),
            passed=passed_precision,
            details={
                "tools_selected": tools_selected,
                "expected_tools": expected_tools,
                "overlap": list(overlap)
            }
        ))
    
    # 2. Step Bounds Compliance (step count <= 5)
    max_steps = expected_outputs.get("max_steps", 5)
    actual_steps = len(tools_selected) + 2  # planner + tools + decision node
    passed_steps = actual_steps <= max_steps
    
    results.append(MetricResult(
        metric_name="AgentIterationStepBoundsPass",
        score=1.0 if passed_steps else 0.0,
        passed=passed_steps,
        details={"actual_steps": actual_steps, "max_steps_allowed": max_steps}
    ))

    return results
