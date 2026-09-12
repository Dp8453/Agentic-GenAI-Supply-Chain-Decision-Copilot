"""
Phase 10 — Security Guardrails Central Service Orchestrator

Exposes GuardrailService to coordinate input guardrails, prompt injection defense,
tool authorization, tool argument validation, numerical claim validation, citation verification,
sensitive secret redaction, rate limiting, and output validation across SupplyChain AI.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from app.guardrails.schemas import (
    GuardrailResult,
    ToolAuthorizationResult,
    SecurityEvent,
    SecuritySeverityEnum,
    ViolationCodeEnum
)
from app.guardrails.input_guard import validate_input
from app.guardrails.prompt_injection import detect_prompt_injection, is_rag_chunk_safe
from app.guardrails.tool_guard import authorize_tool_execution
from app.guardrails.numerical_guard import validate_numerical_claims
from app.guardrails.citation_guard import validate_citations
from app.guardrails.sensitive_data import detect_and_redact_sensitive_data
from app.guardrails.rate_limit import rate_limiter
from app.guardrails.output_guard import validate_output, SAFE_FALLBACK_RESPONSE
from app.llm.schemas import Source

logger = logging.getLogger(__name__)


class GuardrailService:
    """
    Central Security Guardrails & Validation Service.
    Coordinates input, tool, output, numerical, citation, and secret safety checks.
    """

    def __init__(self):
        self.security_events: List[SecurityEvent] = []

    def validate_user_input(self, text: Optional[str], client_id: Optional[str] = None) -> GuardrailResult:
        """
        Runs Rate Limiting, Input Validation, Prompt Injection Defense, and Secret Detection on user prompt.
        """
        # 1. Rate Limiting Check
        if client_id:
            is_limited, rl_result = rate_limiter.is_rate_limited(client_id)
            if is_limited:
                self._log_event("RATE_LIMIT_EXCEEDED", SecuritySeverityEnum.MEDIUM, client_id, False, "RATE_LIMIT_EXCEEDED")
                return rl_result

        # 2. Input Structure & Boundary Check
        in_result = validate_input(text)
        if not in_result.allowed:
            code = in_result.violations[0].code.value if in_result.violations else "INVALID_INPUT"
            self._log_event("INPUT_VALIDATION_FAILED", in_result.risk_level, client_id, False, code)
            return in_result

        query_text = in_result.sanitized_value

        # 3. Prompt Injection Defense
        pi_result = detect_prompt_injection(query_text)
        if not pi_result.allowed:
            code = pi_result.violations[0].code.value if pi_result.violations else "PROMPT_INJECTION"
            self._log_event("PROMPT_INJECTION_BLOCKED", pi_result.risk_level, client_id, False, code)
            return pi_result

        # 4. Sensitive Secret Check
        sd_result, sanitized_text = detect_and_redact_sensitive_data(query_text)
        if not sd_result.allowed:
            self._log_event("SENSITIVE_DATA_REDACTED", sd_result.risk_level, client_id, True, "SENSITIVE_DATA_LEAK")

        return GuardrailResult(
            allowed=True,
            risk_level=SecuritySeverityEnum.LOW,
            violations=[],
            warnings=in_result.warnings + sd_result.warnings,
            sanitized_value=sanitized_text
        )

    def authorize_tool(
        self,
        tool_name: str,
        raw_args: Dict[str, Any],
        current_tool_call_count: int = 0,
        client_id: Optional[str] = None
    ) -> ToolAuthorizationResult:
        """
        Validates proposed tool against tool allowlist, call limits, and parameter boundaries.
        """
        auth_result = authorize_tool_execution(tool_name, raw_args, current_tool_call_count)
        if not auth_result.authorized:
            self._log_event(
                "UNAUTHORIZED_TOOL_BLOCKED",
                SecuritySeverityEnum.HIGH,
                client_id,
                False,
                "UNAUTHORIZED_TOOL",
                tool_name=tool_name
            )
        else:
            self._log_event(
                "TOOL_AUTHORIZED",
                SecuritySeverityEnum.LOW,
                client_id,
                True,
                tool_name=tool_name
            )
        return auth_result

    def validate_agent_output(
        self,
        response_text: str,
        proposed_sources: List[Source],
        retrieved_rag_chunks: List[Dict[str, Any]],
        tool_results: Dict[str, Any],
        client_id: Optional[str] = None
    ) -> Tuple[GuardrailResult, str, List[Source]]:
        """
        Validates final LLM response text, numerical claims, citations, and sensitive secrets.
        Returns: (GuardrailResult, sanitized_response_text, verified_sources)
        """
        # 1. Output structure & prompt leakage check
        out_result = validate_output(response_text)
        if not out_result.allowed:
            self._log_event("OUTPUT_VALIDATION_FAILED", out_result.risk_level, client_id, False, "OUTPUT_VALIDATION_FAILED")
            return out_result, out_result.sanitized_value or SAFE_FALLBACK_RESPONSE, []

        text = out_result.sanitized_value

        # 2. Secret Redaction
        sd_result, sanitized_text = detect_and_redact_sensitive_data(text)
        if not sd_result.allowed:
            self._log_event("OUTPUT_SECRET_REDACTED", sd_result.risk_level, client_id, True, "SENSITIVE_DATA_LEAK")

        # 3. Citation Verification
        cit_result, verified_sources = validate_citations(proposed_sources, retrieved_rag_chunks)
        if not cit_result.allowed:
            self._log_event("CITATION_FABRICATION_FILTERED", cit_result.risk_level, client_id, True, "CITATION_FABRICATION")

        # 4. Numerical Claim Validation
        num_result = validate_numerical_claims(sanitized_text, tool_results)
        if not num_result.allowed:
            self._log_event("NUMERICAL_HALLUCINATION_BLOCKED", num_result.risk_level, client_id, False, "NUMERICAL_HALLUCINATION")
            return num_result, (
                "The synthesized explanation contained numerical claims that could not be verified against "
                "authoritative application data. Please refer to the verified tool metrics provided in context."
            ), verified_sources

        return GuardrailResult(
            allowed=True,
            risk_level=SecuritySeverityEnum.LOW,
            violations=[],
            warnings=out_result.warnings + sd_result.warnings + cit_result.warnings
        ), sanitized_text, verified_sources

    def _log_event(
        self,
        event_type: str,
        severity: SecuritySeverityEnum,
        client_id: Optional[str],
        allowed: bool,
        reason_code: Optional[str] = None,
        tool_name: Optional[str] = None
    ):
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            client_id=client_id or "anonymous",
            tool_name=tool_name,
            allowed=allowed,
            reason_code=reason_code,
            timestamp=datetime.utcnow().isoformat()
        )
        self.security_events.append(event)
        logger.info(f"Security Audit Event: [{severity.value}] {event_type} - Allowed: {allowed} - Reason: {reason_code}")


# Global Guardrail Service Instance
guardrail_service = GuardrailService()
