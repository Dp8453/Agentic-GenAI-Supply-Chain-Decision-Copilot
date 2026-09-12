from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SQLQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language analytical question")
    limit_override: Optional[int] = Field(None, ge=1, le=500, description="Max rows to return (default 50)")
    provider_override: Optional[str] = Field(None, description="Override LLM provider (fake, ollama, openai)")


class SQLQuery(BaseModel):
    sql: str = Field(..., description="Generated PostgreSQL SELECT statement")
    explanation: str = Field(..., description="LLM explanation of how the SQL query was constructed")


class SQLValidationResult(BaseModel):
    allowed: bool = Field(..., description="True if query passes all read-only & security checks")
    reason: str = Field(..., description="Reason for validation result or rejection")
    normalized_sql: Optional[str] = Field(None, description="Cleaned & limit-normalized SQL query")
    warnings: List[str] = Field(default_factory=list, description="Validation notices or warnings")


class SQLQueryResult(BaseModel):
    columns: List[str] = Field(default_factory=list, description="List of returned column names")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="List of row dicts")
    row_count: int = Field(0, description="Number of rows returned")
    truncated: bool = Field(False, description="True if results were capped by max row limit")
    execution_time_ms: float = Field(0.0, description="Query execution latency in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Execution notices or warnings")


class SQLResponse(BaseModel):
    question: str = Field(..., description="Original user question")
    generated_sql: str = Field(..., description="LLM-generated SQL query")
    validation: SQLValidationResult = Field(..., description="SQL safety validation result")
    result: SQLQueryResult = Field(..., description="Executed query results")
    explanation: str = Field(..., description="Grounded natural-language explanation of returned data")
    warnings: List[str] = Field(default_factory=list, description="Application warnings and boundaries")
