"""
Phase 10 — Security Guardrails Output Validation Guard

Validates final synthesized responses against length limits, schema compliance, prompt leakage,
and provides safe fallback outputs when validation fails.
"""

import re
import logging
from typing import Optional, Dict, Any
from app.guardrails.schemas import (
    GuardrailResult,
    GuardrailViolation,
    ViolationCodeEnum,
    SecuritySeverityEnum
)
from app.guardrails.policy import security_policy

logger = logging.getLogger(__name__)

SAFE_FALLBACK_RESPONSE = (
    "The requested query or synthesized response could not be verified by the Security Guardrails Layer. "
    "To ensure system data safety and accuracy, the response has been safely redacted."
)


def validate_output(
    response_text: Optional[str],
    max_length: Optional[int] = None
) -> GuardrailResult:
    """
    Validates output text against structural, security, and prompt non-leakage rules.
    """
    max_len = max_length or security_policy.max_output_length
    violations = []

    if response_text is None or not isinstance(response_text, str) or not response_text.strip():
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.OUTPUT_VALIDATION_FAILED,
            message="LLM output is null, non-string, or empty.",
            severity=SecuritySeverityEnum.HIGH
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.HIGH,
            violations=violations,
            sanitized_value=SAFE_FALLBACK_RESPONSE
        )

    clean_text = response_text.strip()

    # Output length boundary check
    if len(clean_text) > max_len:
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.OUTPUT_VALIDATION_FAILED,
            message=f"Output length ({len(clean_text)}) exceeds policy limit of {max_len} characters.",
            severity=SecuritySeverityEnum.MEDIUM
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.MEDIUM,
            violations=violations,
            sanitized_value=clean_text[:max_len] + "\n...[Output Truncated by Security Policy]"
        )

    # Check for system prompt leakage in output
    if ("you are supplychain ai" in clean_text.lower() or "rules for grounding" in clean_text.lower() or "lead copilot" in clean_text.lower()) and "system" in clean_text.lower():
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.SECRET_EXTRACTION_ATTEMPT,
            message="Synthesized response contains internal system prompt instructions.",
            severity=SecuritySeverityEnum.HIGH
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.HIGH,
            violations=violations,
            sanitized_value=SAFE_FALLBACK_RESPONSE
        )

    return GuardrailResult(
        allowed=True,
        risk_level=SecuritySeverityEnum.LOW,
        violations=[],
        sanitized_value=clean_text
    )
