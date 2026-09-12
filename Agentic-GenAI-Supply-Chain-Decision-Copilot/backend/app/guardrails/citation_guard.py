"""
Phase 10 — Security Guardrails Citation & Source Provenance Guard

Verifies that all citations and document sources cited in LLM outputs correspond
to real retrieved RAG chunks. Rejects or filters fabricated source identifiers.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from app.guardrails.schemas import GuardrailResult, GuardrailViolation, ViolationCodeEnum, SecuritySeverityEnum
from app.llm.schemas import Source

logger = logging.getLogger(__name__)


def validate_citations(
    proposed_sources: List[Source],
    retrieved_rag_chunks: List[Dict[str, Any]]
) -> Tuple[GuardrailResult, List[Source]]:
    """
    Ensures every source item in proposed_sources exists in retrieved_rag_chunks.
    Returns GuardrailResult and filtered list of verified sources.
    """
    valid_source_ids: Set[str] = set()
    valid_doc_titles: Set[str] = set()

    for chunk in retrieved_rag_chunks:
        meta = chunk.get("metadata", {})
        doc_id = str(chunk.get("id", chunk.get("chunk_id", meta.get("document_id", ""))))
        doc_title = str(meta.get("title", meta.get("document_title", chunk.get("document_name", "")))).strip().lower()
        doc_name = str(chunk.get("document_name", "")).strip().lower()
        if doc_id:
            valid_source_ids.add(doc_id)
        if doc_title:
            valid_doc_titles.add(doc_title)
        if doc_name:
            valid_doc_titles.add(doc_name)

    verified_sources: List[Source] = []
    fabricated_sources: List[str] = []

    for src in proposed_sources:
        src_name = str(getattr(src, "document_name", "")).strip().lower()

        # Match against valid IDs or doc titles
        if any(src_name in title for title in valid_doc_titles) or src_name in valid_source_ids or not retrieved_rag_chunks:
            verified_sources.append(src)
        else:
            fabricated_sources.append(getattr(src, "document_name", "unknown_source"))

    violations = []
    if fabricated_sources:
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.CITATION_FABRICATION,
            message=f"LLM cited fabricated or unretrieved document sources: {fabricated_sources}",
            severity=SecuritySeverityEnum.MEDIUM,
            details={"fabricated_sources": fabricated_sources}
        ))
        logger.warning(f"Citation Validation Warning: Fabricated sources detected: {fabricated_sources}")
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.MEDIUM,
            violations=violations,
            sanitized_value=verified_sources
        ), verified_sources

    return GuardrailResult(
        allowed=True,
        risk_level=SecuritySeverityEnum.LOW,
        sanitized_value=verified_sources
    ), verified_sources


# Type alias helper for tuple result
Tuple_Guardrail_Result = tuple
