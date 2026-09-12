"""
Phase 10 — Security Guardrails Sensitive Data Leakage & Secret Redaction Guard

Detects and redacts API keys, Bearer tokens, database connection strings, passwords,
and environment credentials from user queries and synthesized LLM responses.
"""

import re
import logging
from typing import Tuple
from app.guardrails.schemas import GuardrailResult, GuardrailViolation, ViolationCodeEnum, SecuritySeverityEnum

logger = logging.getLogger(__name__)

SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]"),
    (r"Bearer\s+[a-zA-Z0-9\.\-_]{20,}", "Bearer [REDACTED_TOKEN]"),
    (r"postgres(?:ql)?://[^:\s]+:[^@\s]+@[^\s]+", "postgresql://[REDACTED_DB_CREDENTIALS]"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "password='[REDACTED]'"),
    (r"secret_key\s*=\s*['\"][^'\"]+['\"]", "secret_key='[REDACTED]'"),
]


def detect_and_redact_sensitive_data(text: str) -> Tuple[GuardrailResult, str]:
    """
    Scans text for sensitive tokens and API keys. Redacts matching secrets.
    """
    if not text:
        return GuardrailResult(allowed=True, risk_level=SecuritySeverityEnum.LOW), text

    sanitized_text = text
    found_secrets = False
    violations = []

    for pattern, replacement in SECRET_PATTERNS:
        if re.search(pattern, sanitized_text, flags=re.IGNORECASE):
            found_secrets = True
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)

    if found_secrets:
        logger.warning("Sensitive data / secret leakage pattern detected and redacted.")
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.SENSITIVE_DATA_LEAK,
            message="Sensitive secret key, token, or connection string detected and redacted.",
            severity=SecuritySeverityEnum.HIGH
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.HIGH,
            violations=violations,
            sanitized_value=sanitized_text
        ), sanitized_text

    return GuardrailResult(
        allowed=True,
        risk_level=SecuritySeverityEnum.LOW,
        sanitized_value=text
    ), text
