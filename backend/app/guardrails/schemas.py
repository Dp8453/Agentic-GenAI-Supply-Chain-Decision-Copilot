"""
Phase 10 — Security Guardrails & Validation Layer Schemas

Defines Pydantic models for security evaluation results, violation details,
tool authorization, output validation, and security audit logging.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class SecuritySeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ViolationCodeEnum(str, Enum):
    EMPTY_INPUT = "EMPTY_INPUT"
    OVERSIZED_INPUT = "OVERSIZED_INPUT"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    SECRET_EXTRACTION_ATTEMPT = "SECRET_EXTRACTION_ATTEMPT"
    SYSTEM_PROMPT_EXTRACTION_ATTEMPT = "SYSTEM_PROMPT_EXTRACTION_ATTEMPT"
    UNAUTHORIZED_TOOL = "UNAUTHORIZED_TOOL"
    INVALID_TOOL_ARGUMENT = "INVALID_TOOL_ARGUMENT"
    UNSAFE_SQL_BLOCKED = "UNSAFE_SQL_BLOCKED"
    NUMERICAL_HALLUCINATION = "NUMERICAL_HALLUCINATION"
    CITATION_FABRICATION = "CITATION_FABRICATION"
    SENSITIVE_DATA_LEAK = "SENSITIVE_DATA_LEAK"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"
    DATABASE_WRITE_ATTEMPT = "DATABASE_WRITE_ATTEMPT"
    TOO_MANY_TOOL_CALLS = "TOO_MANY_TOOL_CALLS"


class GuardrailViolation(BaseModel):
    """
    Individual security or validation policy violation item.
    """
    code: ViolationCodeEnum = Field(..., description="Structured violation classification code")
    message: str = Field(..., description="Human-readable violation description")
    severity: SecuritySeverityEnum = Field(..., description="Security severity rating")
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with violation")


class GuardrailResult(BaseModel):
    """
    Evaluation result produced by an individual guardrail module.
    """
    allowed: bool = Field(..., description="Whether the request/action/output is allowed to proceed")
    risk_level: SecuritySeverityEnum = Field(SecuritySeverityEnum.LOW, description="Overall risk severity rating")
    violations: List[GuardrailViolation] = Field(default_factory=list, description="List of detected policy violations")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warning messages")
    sanitized_value: Optional[Any] = Field(None, description="Sanitized version of input/output if modified")


class ToolAuthorizationResult(BaseModel):
    """
    Evaluation result for tool execution authorization.
    """
    authorized: bool = Field(..., description="Whether tool execution is authorized")
    tool_name: str = Field(..., description="Name of proposed tool")
    validated_args: Dict[str, Any] = Field(default_factory=dict, description="Validated and bounded tool arguments")
    reason: str = Field("", description="Justification or blocking error message")


class SecurityEvent(BaseModel):
    """
    Structured security audit log event entry.
    """
    event_type: str = Field(..., description="Security event type identifier")
    severity: SecuritySeverityEnum = Field(..., description="Event severity rating")
    client_id: Optional[str] = Field(None, description="Client IP or request correlation identifier")
    tool_name: Optional[str] = Field(None, description="Target tool name if applicable")
    allowed: bool = Field(..., description="Whether action was permitted")
    reason_code: Optional[str] = Field(None, description="Violation code if blocked")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
