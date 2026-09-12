"""
Phase 10 — Security Guardrails Centralized Security Policy

Defines system security boundaries, tool allowlists, numerical tolerance thresholds,
and input/output character limits.
"""

from pydantic import BaseModel, Field
from typing import Set, List


class SecurityPolicy(BaseModel):
    """
    Centralized Security Policy Configuration.
    """
    max_input_length: int = Field(2000, description="Maximum allowed input character length")
    max_output_length: int = Field(4000, description="Maximum allowed output character length")
    max_tool_calls: int = Field(5, description="Maximum tool invocations per agent query")
    max_sql_length: int = Field(1000, description="Maximum allowed SQL query string length")
    max_sql_rows: int = Field(50, description="Maximum rows returned by SQL query")
    max_simulation_horizon: int = Field(90, description="Maximum simulation forecast horizon in days")
    max_transfer_quantity: int = Field(10000, description="Maximum allowed inventory transfer quantity")

    allowed_tools: Set[str] = Field(
        default_factory=lambda: {"SQL", "RAG", "FORECAST", "RISK", "SIMULATION"},
        description="Explicit allowlist of authorized execution tools"
    )

    read_only_allowed_intents: Set[str] = Field(
        default_factory=lambda: {
            "SUPPLIER_PERFORMANCE", "INVENTORY_RISK", "DEMAND_FORECAST",
            "DOCUMENT_RAG", "SQL_ANALYTICS", "WHAT_IF_SIMULATION", "GENERAL_SUPPLY_CHAIN", "UNKNOWN"
        },
        description="Supported read-only advisory intents"
    )

    rate_limit_requests: int = Field(60, description="Max requests allowed per rate limit window")
    rate_limit_window_seconds: int = Field(60, description="Sliding window duration in seconds")

    numerical_tolerance_percent: float = Field(2.0, description="Tolerance percentage for numerical validation matching")


# Global Security Policy Instance
security_policy = SecurityPolicy()
