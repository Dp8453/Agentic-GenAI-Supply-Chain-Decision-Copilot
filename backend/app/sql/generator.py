import logging
from typing import Optional

from app.llm.provider import LLMProvider, get_llm_provider
from app.sql.schemas import SQLQuery
from app.sql.prompts import PROMPT_SQL_GENERATION, DATABASE_SCHEMA_PROMPT_CONTEXT

logger = logging.getLogger(__name__)


def generate_sql(
    question: str,
    provider: Optional[LLMProvider] = None,
    provider_name: Optional[str] = None
) -> SQLQuery:
    """
    Translates a natural language supply-chain question into a PostgreSQL SELECT query using LLM.
    Reuses the Phase 6 LLM Provider abstraction.
    """
    active_provider = provider or get_llm_provider(provider_name)
    prompt = PROMPT_SQL_GENERATION.format(
        question=question,
        schema_context=DATABASE_SCHEMA_PROMPT_CONTEXT
    )

    try:
        sql_obj = active_provider.generate_structured(
            prompt=prompt,
            response_schema=SQLQuery,
            system_prompt="You are a safe PostgreSQL NL-to-SQL query generator for SupplyChain AI."
        )
        return sql_obj
    except Exception as e:
        logger.warning(f"LLM SQL generation failed: {e}. Returning safe fallback SQL.")
        return SQLQuery(
            sql="SELECT * FROM suppliers LIMIT 50",
            explanation=f"Fallback SQL generated due to LLM provider error: {str(e)}"
        )
