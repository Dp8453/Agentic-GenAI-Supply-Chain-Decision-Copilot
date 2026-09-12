from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.guardrails.numerical_guard import validate_numerical_claims
from app.guardrails.citation_guard import validate_citations


def evaluate_grounding_and_citations(
    llm_response_text: str,
    sources: List[Dict[str, Any]],
    retrieved_chunks: List[Dict[str, Any]],
    tool_results: Dict[str, Any]
) -> List[MetricResult]:
    """
    Evaluates numerical grounding alignment (2.0% tolerance) and RAG citation validity.
    """
    results = []

    # 1. Numerical Grounding
    num_res = validate_numerical_claims(llm_response_text, tool_results)
    passed_grounding = num_res.allowed
    results.append(MetricResult(
        metric_name="NumericalGroundingPass",
        score=1.0 if passed_grounding else 0.0,
        passed=passed_grounding,
        details={"tolerance_threshold_pct": 2.0, "violations_count": len(num_res.violations)}
    ))

    # 2. Citation Validity
    from app.llm.schemas import Source
    proposed_sources = []
    for s in sources:
        if isinstance(s, dict):
            proposed_sources.append(Source(
                document_name=s.get("document_name", s.get("name", "Unknown")),
                document_type=s.get("document_type", s.get("source_type")),
                section=s.get("section")
            ))
    
    cit_res, verified_sources = validate_citations(proposed_sources, retrieved_chunks)
    passed_citations = cit_res.allowed or len(proposed_sources) == 0
    results.append(MetricResult(
        metric_name="CitationValidityPass",
        score=1.0 if passed_citations else 0.0,
        passed=passed_citations,
        details={
            "proposed_count": len(proposed_sources),
            "verified_count": len(verified_sources)
        }
    ))

    return results
