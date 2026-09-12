import logging
from typing import Optional, List, Dict, Any

from app.llm.provider import LLMProvider, get_llm_provider
from app.llm.schemas import (
    CopilotResponse, IntentClassificationResult, IntentEnum, ExtractedEntities, Source
)
from app.llm.prompts import (
    SYSTEM_COPILOT_ROLE, PROMPT_INTENT_CLASSIFICATION, PROMPT_GROUNDED_RESPONSE
)
from app.llm.context import LLMContext, build_copilot_context

logger = logging.getLogger(__name__)


def validate_and_sanitize_sources(
    response: CopilotResponse,
    retrieved_chunks: List[Dict[str, Any]]
) -> CopilotResponse:
    """
    Strict Citation Validation:
    Ensures every source cited in response matches an actual RAG document retrieved.
    Strips hallucinated citations and populates authoritative document metadata & similarity scores.
    """
    if not retrieved_chunks:
        response.sources = []
        return response

    valid_chunk_map = {c.get("document_name", "").lower(): c for c in retrieved_chunks}
    sanitized_sources = []

    for src in response.sources:
        s_name_lower = src.document_name.lower().strip()
        matched_chunk = None

        # Match exact document name or substring match
        for chunk_name, chunk in valid_chunk_map.items():
            if chunk_name in s_name_lower or s_name_lower in chunk_name:
                matched_chunk = chunk
                break

        if matched_chunk:
            sanitized_sources.append(Source(
                document_name=matched_chunk.get("document_name"),
                document_type=matched_chunk.get("document_type"),
                section=matched_chunk.get("metadata", {}).get("section", src.section or "General"),
                similarity=matched_chunk.get("similarity", src.similarity or 0.0)
            ))

    # If LLM generated no valid matching sources, populate top retrieved RAG chunks as authoritative sources
    if not sanitized_sources and retrieved_chunks:
        for chunk in retrieved_chunks[:3]:
            sanitized_sources.append(Source(
                document_name=chunk.get("document_name"),
                document_type=chunk.get("document_type"),
                section=chunk.get("metadata", {}).get("section", "General"),
                similarity=chunk.get("similarity", 0.0)
            ))

    response.sources = sanitized_sources
    return response


class LLMService:
    """
    Core Service exposing intent classification, context assembly, grounded synthesis, and citation validation.
    """

    def __init__(self, provider_name: Optional[str] = None):
        self.provider: LLMProvider = get_llm_provider(provider_name)

    def classify_intent(self, question: str) -> IntentClassificationResult:
        """
        Classifies user prompt intent and extracts entity parameters.
        """
        prompt = PROMPT_INTENT_CLASSIFICATION.format(question=question)
        try:
            return self.provider.generate_structured(
                prompt=prompt,
                response_schema=IntentClassificationResult,
                system_prompt=SYSTEM_COPILOT_ROLE
            )
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}. Falling back to default.")
            return IntentClassificationResult(
                intent=IntentEnum.GENERAL_SUPPLY_CHAIN,
                confidence=0.5,
                entities=ExtractedEntities(),
                reasoning=f"Intent classification fallback due to provider error: {str(e)}"
            )

    def generate_grounded_response(
        self,
        question: str,
        context: LLMContext
    ) -> CopilotResponse:
        """
        Synthesizes grounded natural-language answer matching CopilotResponse Pydantic schema.
        """
        context_text = context.to_markdown()
        prompt = PROMPT_GROUNDED_RESPONSE.format(
            question=question,
            intent=context.intent,
            context_text=context_text
        )

        try:
            response = self.provider.generate_structured(
                prompt=prompt,
                response_schema=CopilotResponse,
                system_prompt=SYSTEM_COPILOT_ROLE
            )
        except Exception as e:
            logger.error(f"Grounded response generation failed: {e}")
            # Construct clear fallback response on provider error
            response = CopilotResponse(
                summary="System copilot synthesis fallback.",
                intent=context.intent,
                answer=f"Unable to generate full LLM response: {str(e)}. However, trusted metrics remain available.",
                risk_level=context.risk_facts.get("risk_level"),
                explanation="The LLM provider experienced an error or timeout.",
                confidence=0.5,
                sources=[],
                data_used=["Deterministic Application Tools"],
                warnings=context.warnings + [f"LLM Provider error: {str(e)}"]
            )

        # Enforce Grounding Citation Validation
        response = validate_and_sanitize_sources(response, context.retrieved_chunks)

        # Append system warnings
        if context.warnings:
            existing = set(response.warnings)
            for w in context.warnings:
                if w not in existing:
                    response.warnings.append(w)

        return response

    def process_query(
        self,
        question: str,
        supplier_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
        top_k: int = 5,
        provider_override: Optional[str] = None,
        db: Any = None
    ) -> CopilotResponse:
        """
        Full End-to-End Copilot Pipeline:
        Question -> Intent & Entities -> Context Assembly (RAG + Risk + Forecast) -> LLM Synthesis -> Source Validation
        """
        if provider_override:
            active_provider = get_llm_provider(provider_override)
        else:
            active_provider = self.provider

        # 1. Intent Classification
        intent_res = self.classify_intent(question)

        # 2. Context Assembly
        context = build_copilot_context(
            question=question,
            intent_result=intent_res,
            supplier_filter=supplier_filter,
            doc_type_filter=doc_type_filter,
            top_k=top_k,
            db=db
        )

        # 3. Grounded Synthesis
        self.provider = active_provider
        copilot_response = self.generate_grounded_response(question, context)

        return copilot_response
