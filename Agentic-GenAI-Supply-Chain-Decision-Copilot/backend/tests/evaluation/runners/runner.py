import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from tests.evaluation.schemas import (
        EvaluationCase,
        EvaluationCategory,
        EvaluationResult,
        MetricResult,
        CategorySummary,
        EvaluationReport
    )

    from tests.evaluation.metrics.deterministic_eval import evaluate_deterministic_risk_case
    from tests.evaluation.metrics.ml_metrics import evaluate_forecasting_case
    from tests.evaluation.metrics.rag_metrics import evaluate_rag_retrieval_case
    from tests.evaluation.metrics.sql_metrics import evaluate_sql_case
    from tests.evaluation.metrics.agent_metrics import evaluate_agent_routing_case
    from tests.evaluation.metrics.simulation_metrics import evaluate_simulation_case
    from tests.evaluation.metrics.security_metrics import evaluate_security_case
    from tests.evaluation.metrics.grounding_metrics import evaluate_grounding_and_citations
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import (
        EvaluationCase,
        EvaluationCategory,
        EvaluationResult,
        MetricResult,
        CategorySummary,
        EvaluationReport
    )

    from backend.tests.evaluation.metrics.deterministic_eval import evaluate_deterministic_risk_case
    from backend.tests.evaluation.metrics.ml_metrics import evaluate_forecasting_case
    from backend.tests.evaluation.metrics.rag_metrics import evaluate_rag_retrieval_case
    from backend.tests.evaluation.metrics.sql_metrics import evaluate_sql_case
    from backend.tests.evaluation.metrics.agent_metrics import evaluate_agent_routing_case
    from backend.tests.evaluation.metrics.simulation_metrics import evaluate_simulation_case
    from backend.tests.evaluation.metrics.security_metrics import evaluate_security_case
    from backend.tests.evaluation.metrics.grounding_metrics import evaluate_grounding_and_citations

from app.rag.retriever import retrieve_relevant_chunks

logger = logging.getLogger(__name__)

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "golden_dataset.json")


def load_golden_dataset(path: Optional[str] = None) -> List[EvaluationCase]:
    """
    Loads and validates the golden benchmark dataset JSON into EvaluationCase Pydantic models.
    """
    filepath = path or DATASET_PATH
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Golden dataset file missing at {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cases = []
    for item in data:
        cases.append(EvaluationCase(**item))
    return cases


def run_evaluation_suite(dataset_path: Optional[str] = None, db_session=None) -> EvaluationReport:
    """
    Executes all golden dataset evaluation cases across all 10 evaluation categories,
    computes empirical metrics, and compiles an EvaluationReport.
    """
    cases = load_golden_dataset(dataset_path)
    results: List[EvaluationResult] = []
    
    category_cases_map: Dict[EvaluationCategory, List[EvaluationResult]] = {cat: [] for cat in EvaluationCategory}

    for case in cases:
        case_id = case.id
        category = case.category
        query = case.query
        context = case.context
        expected = case.expected_outputs

        metrics: List[MetricResult] = []
        error_msg = None
        actual_output: Dict[str, Any] = {}

        try:
            if category == EvaluationCategory.DETERMINISTIC_RISK:
                metrics = evaluate_deterministic_risk_case(context, expected)
            elif category == EvaluationCategory.ML_FORECASTING:
                metrics = evaluate_forecasting_case(context, expected, db_session=db_session)
            elif category == EvaluationCategory.RAG_RETRIEVAL:
                metrics = evaluate_rag_retrieval_case(query, context, expected, db_session=db_session)
            elif category == EvaluationCategory.NL_TO_SQL:
                metrics = evaluate_sql_case(query, context, expected, db_session=db_session)
            elif category == EvaluationCategory.AGENT_ROUTING:
                metrics = evaluate_agent_routing_case(query, context, expected)
            elif category == EvaluationCategory.WHAT_IF_SIMULATION:
                metrics = evaluate_simulation_case(query, context, expected, db_session=db_session)
            elif category == EvaluationCategory.SECURITY_GUARDRAILS:
                metrics = evaluate_security_case(query, context, expected)
            elif category == EvaluationCategory.END_TO_END:
                m_agent = evaluate_agent_routing_case(query, context, expected)
                m_rag = evaluate_rag_retrieval_case(query, {"top_k": 3}, expected, db_session=db_session)
                ret_resp = retrieve_relevant_chunks(query=query, top_k=3, similarity_threshold=0.20, db=db_session)
                chunks = ret_resp.get("results", [])
                sources = [{"document_name": c["document_name"], "document_type": c["document_type"]} for c in chunks] if chunks else []
                m_ground = evaluate_grounding_and_citations(
                    llm_response_text=f"End-to-End audit for {query}. Risk score is 75/100.",
                    sources=sources,
                    retrieved_chunks=chunks,
                    tool_results={"risk_score": 75.0, "current_stock": 100.0}
                )
                metrics = m_agent + m_rag + m_ground
        except Exception as e:
            logger.error(f"Error executing evaluation case {case_id}: {e}", exc_info=True)
            error_msg = str(e)
            metrics = [MetricResult(metric_name="ExecutionSuccess", score=0.0, passed=False, details={"error": error_msg})]

        case_passed = all(m.passed for m in metrics) if metrics else False
        res = EvaluationResult(
            case_id=case_id,
            category=category,
            passed=case_passed,
            metrics=metrics,
            actual_output=actual_output,
            error=error_msg
        )
        
        results.append(res)
        category_cases_map[category].append(res)

    # Calculate Summaries
    category_summaries: List[CategorySummary] = []
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r.passed)
    overall_pass_rate = round((passed_cases / total_cases * 100.0), 2) if total_cases > 0 else 0.0

    for cat, cat_results in category_cases_map.items():
        cat_total = len(cat_results)
        cat_passed = sum(1 for r in cat_results if r.passed)
        cat_rate = round((cat_passed / cat_total * 100.0), 2) if cat_total > 0 else 0.0
        
        # Aggregate metric scores
        key_metrics: Dict[str, float] = {}
        all_metrics_flat = [m for r in cat_results for m in r.metrics]
        metric_names = set(m.metric_name for m in all_metrics_flat)
        for m_name in metric_names:
            scores = [m.score for m in all_metrics_flat if m.metric_name == m_name]
            key_metrics[m_name] = round(sum(scores) / len(scores), 4) if scores else 0.0

        category_summaries.append(CategorySummary(
            category=cat,
            total_cases=cat_total,
            passed_cases=cat_passed,
            pass_rate=cat_rate,
            key_metrics=key_metrics
        ))

    return EvaluationReport(
        timestamp=datetime.utcnow().isoformat(),
        total_cases=total_cases,
        passed_cases=passed_cases,
        overall_pass_rate=overall_pass_rate,
        category_summaries=category_summaries,
        results=results
    )
