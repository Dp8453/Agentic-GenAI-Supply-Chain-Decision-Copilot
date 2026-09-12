"""
Phase 10 — Security Guardrails Input Validation Guard

Validates incoming user questions for existence, string type, non-emptiness, character length,
control character sanitization, and excessive repetition.
"""

import re
import logging
from typing import Optional
from app.guardrails.schemas import (
    GuardrailResult,
    GuardrailViolation,
    ViolationCodeEnum,
    SecuritySeverityEnum
)
from app.guardrails.policy import security_policy

logger = logging.getLogger(__name__)


def validate_input(text: Optional[str]) -> GuardrailResult:
    """
    Validates user query input against length, structural, and repetition bounds.
    """
    violations = []
    warnings = []

    if text is None or not isinstance(text, str) or not text.strip():
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.EMPTY_INPUT,
            message="User query is empty or non-string.",
            severity=SecuritySeverityEnum.HIGH
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.HIGH,
            violations=violations,
            sanitized_value=""
        )

    clean_text = text.strip()

    # Length boundary check
    if len(clean_text) > security_policy.max_input_length:
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.OVERSIZED_INPUT,
            message=f"User input length ({len(clean_text)}) exceeds maximum limit of {security_policy.max_input_length} characters.",
            severity=SecuritySeverityEnum.MEDIUM,
            details={"input_length": len(clean_text), "max_limit": security_policy.max_input_length}
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.MEDIUM,
            violations=violations,
            sanitized_value=clean_text[:security_policy.max_input_length]
        )

    # Control characters sanitization (strip non-printable control chars except newlines/tabs)
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", clean_text)
    if sanitized != clean_text:
        warnings.append("Stripped unprintable control characters from input.")

    # Excessive character repetition check (e.g. "aaaaa..." 50 times)
    if re.search(r"(.)\1{49,}", sanitized):
        warnings.append("Excessive character repetition detected.")

    return GuardrailResult(
        allowed=True,
        risk_level=SecuritySeverityEnum.LOW,
        violations=[],
        warnings=warnings,
        sanitized_value=sanitized
    )
