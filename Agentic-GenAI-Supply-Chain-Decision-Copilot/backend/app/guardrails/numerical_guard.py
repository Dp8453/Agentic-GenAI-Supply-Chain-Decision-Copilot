"""
Phase 10 — Security Guardrails Numerical Hallucination Guard

Verifies that numerical metrics mentioned in LLM synthesized responses match
actual numbers produced by trusted deterministic application engines (Risk Engine,
XGBoost Forecast, Safe SQL, What-If Simulation Engine).
"""

import re
import logging
from typing import Dict, Any, List, Set, Tuple
from app.guardrails.schemas import GuardrailResult, GuardrailViolation, ViolationCodeEnum, SecuritySeverityEnum
from app.guardrails.policy import security_policy

logger = logging.getLogger(__name__)


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extracts numerical values (integers and floats) from natural language text.
    Filters out common dates (YYYY-MM-DD) or SKU index numbers.
    """
    # Remove ISO dates first to avoid treating 2026 as a quantity
    clean_text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", text)
    matches = re.findall(r"\b\d+(?:\.\d+)?\b", clean_text)
    numbers = []
    for m in matches:
        val = float(m)
        numbers.append(val)
    return numbers


def extract_trusted_numbers_from_facts(tool_results: Dict[str, Any]) -> Set[float]:
    """
    Extracts all authoritative numerical values from trusted deterministic tool execution results.
    """
    trusted_numbers: Set[float] = set()

    def _traverse_dict(obj: Any):
        if isinstance(obj, (int, float)):
            trusted_numbers.add(float(obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k not in ["product_id", "supplier_id", "warehouse_id", "step_index", "line_number"]:
                    _traverse_dict(v)
        elif isinstance(obj, list):
            for item in obj:
                _traverse_dict(item)

    _traverse_dict(tool_results)
    return trusted_numbers


def validate_numerical_claims(
    llm_response_text: str,
    tool_results: Dict[str, Any]
) -> GuardrailResult:
    """
    Validates numerical claims in LLM output against trusted tool execution results.
    """
    if not tool_results:
        return GuardrailResult(allowed=True, risk_level=SecuritySeverityEnum.LOW)

    response_numbers = extract_numbers_from_text(llm_response_text)
    trusted_numbers = extract_trusted_numbers_from_facts(tool_results)

    if not response_numbers or not trusted_numbers:
        return GuardrailResult(allowed=True, risk_level=SecuritySeverityEnum.LOW)

    violations = []
    tolerance = security_policy.numerical_tolerance_percent / 100.0

    unmatched_claims = []
    for num in response_numbers:
        # Ignore small numbers 0, 1, 2, 3, 5, 10 or standard dates
        if num in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 14.0, 30.0]:
            continue

        matched = False
        for t_num in trusted_numbers:
            if t_num == 0:
                if num == 0:
                    matched = True
                    break
            elif abs(num - t_num) / abs(t_num) <= tolerance:
                matched = True
                break

        if not matched:
            unmatched_claims.append(num)

    # Flag violation if multiple numbers in LLM text do not match any trusted tool metric
    if len(unmatched_claims) >= 2:
        violations.append(GuardrailViolation(
            code=ViolationCodeEnum.NUMERICAL_HALLUCINATION,
            message=f"LLM output contains hallucinated numerical claims: {unmatched_claims}",
            severity=SecuritySeverityEnum.HIGH,
            details={"unmatched_numbers": unmatched_claims, "trusted_pool_sample": list(trusted_numbers)[:10]}
        ))
        return GuardrailResult(
            allowed=False,
            risk_level=SecuritySeverityEnum.HIGH,
            violations=violations
        )

    return GuardrailResult(allowed=True, risk_level=SecuritySeverityEnum.LOW)
