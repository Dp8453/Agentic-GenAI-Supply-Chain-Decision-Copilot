import json
import logging
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.llm.provider import LLMProvider, get_llm_provider
from app.sql.schemas import SQLQueryRequest, SQLResponse, SQLQueryResult, SQLValidationResult
from app.sql.generator import generate_sql
from app.sql.validator import validate_sql
from app.sql.executor import execute_sql
from app.sql.prompts import PROMPT_SQL_EXPLANATION

logger = logging.getLogger(__name__)


class SQLService:
    """
    Core Natural-Language-to-SQL Service.
    Orchestrates NL-to-SQL generation, read-only safety validation,
    parameterized execution, and grounded explanation.
    """

    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name

    def explain_results(
        self,
        question: str,
        sql_query: str,
        result: SQLQueryResult,
        provider: LLMProvider
    ) -> str:
        """
        Synthesizes returned query rows into a grounded natural-language explanation.
        Uses ONLY the exact numbers returned in the rows.
        """
        if not result.rows:
            return "No matching records were found in the database for the query."

        rows_json = json.dumps(result.rows[:10], indent=2)
        prompt = PROMPT_SQL_EXPLANATION.format(
            question=question,
            sql_query=sql_query,
            rows_json=rows_json
        )

        try:
            explanation = provider.generate(prompt=prompt, system_prompt="Explain SQL query results based strictly on the provided data rows.")
            return explanation
        except Exception as e:
            logger.warning(f"SQL result explanation generation failed: {e}")
            return f"Returned {result.row_count} records matching your query criteria."

    def execute_natural_language_query(
        self,
        question: str,
        db: Optional[Session] = None,
        limit_override: Optional[int] = None,
        provider_override: Optional[str] = None
    ) -> SQLResponse:
        """
        Full End-to-End Pipeline:
        Question -> LLM SQL Generator -> SQL Safety Validator -> Read-Only Executor -> LLM Explanation
        """
        target_provider_name = provider_override or self.provider_name
        provider = get_llm_provider(target_provider_name)
        max_limit = limit_override or 50

        # 1. LLM SQL Generation
        sql_obj = generate_sql(question=question, provider=provider)

        # 2. Safety & Read-Only Validation
        val_res = validate_sql(sql_str=sql_obj.sql, max_limit=max_limit)

        # 3. Security Guardrail: Reject Execution if Validation Failed
        if not val_res.allowed:
            logger.warning(f"SQL Query blocked by safety validator: {val_res.reason}")
            empty_result = SQLQueryResult(
                columns=[],
                rows=[],
                row_count=0,
                truncated=False,
                execution_time_ms=0.0,
                warnings=val_res.warnings + [f"Query Blocked: {val_res.reason}"]
            )
            return SQLResponse(
                question=question,
                generated_sql=sql_obj.sql,
                validation=val_res,
                result=empty_result,
                explanation=f"Query execution was blocked due to safety policy: {val_res.reason}",
                warnings=val_res.warnings + ["Security Guardrail Triggered: Execution Aborted"]
            )

        # 4. Read-Only Query Execution
        query_result = execute_sql(
            validated_sql=val_res.normalized_sql,
            db=db,
            max_rows=max_limit
        )

        # 5. Natural-Language Explanation
        explanation = self.explain_results(
            question=question,
            sql_query=val_res.normalized_sql,
            result=query_result,
            provider=provider
        )

        combined_warnings = val_res.warnings + query_result.warnings

        return SQLResponse(
            question=question,
            generated_sql=val_res.normalized_sql,
            validation=val_res,
            result=query_result,
            explanation=explanation,
            warnings=combined_warnings
        )
