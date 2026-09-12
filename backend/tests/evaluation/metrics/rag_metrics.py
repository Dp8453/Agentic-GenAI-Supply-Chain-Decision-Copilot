from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.rag.retriever import retrieve_relevant_chunks


def calculate_mrr(retrieved_chunks: List[Dict[str, Any]], target_keywords: List[str]) -> float:
    """
    Calculates Reciprocal Rank (RR) for a single query result.
    First rank (1-indexed) containing any target keyword yields 1 / rank.
    """
    if not retrieved_chunks or not target_keywords:
        return 0.0

    lower_keywords = [k.lower() for k in target_keywords]
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        content = chunk.get("content", "").lower()
        doc_name = chunk.get("document_name", "").lower()
        if any(k in content or k in doc_name for k in lower_keywords):
            return 1.0 / idx
    return 0.0


def evaluate_rag_retrieval_case(query: str, context: Dict[str, Any], expected_outputs: Dict[str, Any], db_session=None) -> List[MetricResult]:
    """
    Evaluates vector retrieval precision (Hit@1, Hit@3, Hit@5), MRR, and grounding relevance.
    """
    results = []
    top_k = context.get("top_k", 5)
    supplier_filter = context.get("supplier_filter")
    doc_type_filter = context.get("doc_type_filter")

    ret_resp = retrieve_relevant_chunks(
        query=query,
        top_k=top_k,
        similarity_threshold=0.20,
        supplier_filter=supplier_filter,
        doc_type_filter=doc_type_filter,
        db=db_session
    )
    
    chunks = ret_resp.get("results", [])
    target_keywords = expected_outputs.get("target_keywords", [])
    target_doc_types = expected_outputs.get("target_doc_types", [])

    def is_relevant(chunk: Dict[str, Any]) -> bool:
        c_text = chunk.get("content", "").lower()
        doc_type = chunk.get("document_type", "")
        doc_name = chunk.get("document_name", "").lower()
        
        if target_doc_types and doc_type in target_doc_types:
            return True
        if target_keywords and any(k.lower() in c_text or k.lower() in doc_name for k in target_keywords):
            return True
        if not target_keywords and not target_doc_types:
            return True
        return False

    hits = [is_relevant(c) for c in chunks]

    # Hit@1
    hit_1 = 1.0 if (len(hits) >= 1 and hits[0]) else 0.0
    results.append(MetricResult(
        metric_name="Hit@1",
        score=hit_1,
        passed=hit_1 >= expected_outputs.get("min_hit_at_1", 0.0),
        details={"hit_at_1": hit_1}
    ))

    # Hit@3
    hit_3 = 1.0 if any(hits[:3]) else 0.0
    results.append(MetricResult(
        metric_name="Hit@3",
        score=hit_3,
        passed=hit_3 >= expected_outputs.get("min_hit_at_3", 0.0),
        details={"hit_at_3": hit_3}
    ))

    # Hit@5
    hit_5 = 1.0 if any(hits[:5]) else 0.0
    results.append(MetricResult(
        metric_name="Hit@5",
        score=hit_5,
        passed=hit_5 >= expected_outputs.get("min_hit_at_5", 1.0 if (target_keywords or target_doc_types) else 0.0),
        details={"hit_at_5": hit_5, "total_chunks": len(chunks)}
    ))

    # MRR
    rr = calculate_mrr(chunks, target_keywords if target_keywords else [query.split()[0]])
    results.append(MetricResult(
        metric_name="ReciprocalRank",
        score=round(rr, 4),
        passed=rr > 0.0 if (target_keywords or target_doc_types) else True,
        details={"mrr": round(rr, 4)}
    ))

    return results
