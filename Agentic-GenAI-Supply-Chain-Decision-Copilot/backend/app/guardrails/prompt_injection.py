"""
Phase 10 — Security Guardrails Layered Prompt Injection Defense

Detects direct instruction overrides, system prompt extraction, jailbreak patterns,
and unauthorized execution commands in user queries and retrieved documents.
"""

import re
import logging
from typing import Tuple
from app.guardrails.schemas import (
    GuardrailResult,
    GuardrailViolation,
    ViolationCodeEnum,
    SecuritySeverityEnum
)

logger = logging.getLogger(__name__)

# Pattern sets for multi-layer prompt injection detection
INSTRUCTION_OVERRIDE_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|system|developer|above|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|system|developer|above|prior)\s+instructions",
    r"forget\s+(all\s+)?(previous|system|developer|above|prior)\s+instructions",
    r"override\s+(system|safety|security)\s+(rules|prompt|instructions)",
    r"disable\s+(all\s+)?(safety|security|guardrails|checks|validators)",
    r"bypass\s+(safety|security|sql|tool)\s+(restrictions|filters|checks)",
    r"pretend\s+you\s+are\s+(an?\s+)?unrestricted",
    r"act\s+as\s+(an?\s+)?unrestricted",
    r"you\s+are\s+now\s+in\s+jailbreak\s+mode",
    r"dan\s+mode\s+enabled",
]

SECRET_EXTRACTION_PATTERNS = [
    r"reveal\s+(your\s+)?(system|developer|hidden)\s+prompt",
    r"show\s+(me\s+)?(your\s+)?(system|developer|hidden)\s+prompt",
    r"print\s+(your\s+)?(system|developer|hidden)\s+prompt",
    r"what\s+is\s+your\s+(system|developer|hidden)\s+prompt",
    r"show\s+(me\s+)?(the\s+)?api\s+key",
    r"reveal\s+(the\s+)?api\s+key",
    r"show\s+(me\s+)?(the\s+)?database\s+(password|url|credentials)",
    r"reveal\s+(the\s+)?database\s+(password|url|credentials)",
    r"print\s+env\s+variables",
]

UNAUTHORIZED_MUTATION_PATTERNS = [
    r"execute\s+(delete|drop|truncate|update|insert)\s+",
    r"delete\s+(all\s+)?(inventory|products|suppliers|records|tables)",
    r"drop\s+table",
    r"truncate\s+table",
    r"create\s+a?\s*purchase\s+order\s+now",
    r"place\s+an?\s*emergency\s+order\s+now",
    r"send\s+email\s+to\s+supplier",
]


def detect_prompt_injection(text: str) -> GuardrailResult:
    """
    Scans query text for prompt injection, jailbreak attempts, and instruction overrides.
    """
    violations = []
    text_lower = text.lower()

    # 1. Instruction Override Check
    for pattern in INSTRUCTION_OVERRIDE_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(GuardrailViolation(
                code=ViolationCodeEnum.PROMPT_INJECTION,
                message="Potential instruction override or jailbreak attempt detected.",
                severity=SecuritySeverityEnum.HIGH,
                details={"matched_pattern": pattern}
            ))
            break

    # 2. Secret Extraction Check
    for pattern in SECRET_EXTRACTION_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(GuardrailViolation(
                code=ViolationCodeEnum.SECRET_EXTRACTION_ATTEMPT,
                message="Attempt to extract system prompt or API credentials detected.",
                severity=SecuritySeverityEnum.HIGH,
                details={"matched_pattern": pattern}
            ))
            break

    # 3. Database Mutation / Execution Request Check
    for pattern in UNAUTHORIZED_MUTATION_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(GuardrailViolation(
                code=ViolationCodeEnum.DATABASE_WRITE_ATTEMPT,
                message="Request contains unauthorized database mutation or execution commands.",
                severity=SecuritySeverityEnum.CRITICAL,
                details={"matched_pattern": pattern}
            ))
            break

    if violations:
        max_severity = max(v.severity for v in violations)
        return GuardrailResult(
            allowed=False,
            risk_level=max_severity,
            violations=violations,
            sanitized_value=text
        )

    return GuardrailResult(
        allowed=True,
        risk_level=SecuritySeverityEnum.LOW,
        violations=[],
        sanitized_value=text
    )


def is_rag_chunk_safe(chunk_content: str) -> bool:
    """
    Treats retrieved RAG document content as UNTRUSTED data.
    Ensures retrieved document chunks do not contain prompt injection overrides.
    """
    content_lower = chunk_content.lower()
    for pattern in INSTRUCTION_OVERRIDE_PATTERNS + SECRET_EXTRACTION_PATTERNS:
        if re.search(pattern, content_lower):
            logger.warning(f"RAG Chunk security violation blocked: matched '{pattern}'")
            return False
    return True
