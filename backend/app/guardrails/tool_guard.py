"""
Phase 10 — Security Guardrails Tool Authorization & Parameter Guardrail

Enforces tool allowlists, validates tool parameter boundaries (SQL length, forecast horizons,
simulation parameters), and prevents runaway tool call counts.
"""

import logging
from typing import Dict, Any, List, Optional
from app.guardrails.schemas import ToolAuthorizationResult
from app.guardrails.policy import security_policy
from app.simulation.scenarios import validate_scenario, SimulationScenario
from app.sql.validator import validate_sql

logger = logging.getLogger(__name__)


def authorize_tool_execution(
    tool_name: str,
    raw_args: Dict[str, Any],
    current_tool_call_count: int = 0
) -> ToolAuthorizationResult:
    """
    Validates whether proposed tool execution is authorized and parameter-safe.
    """
    # 1. Allowlist verification
    tool_upper = tool_name.upper()
    if tool_upper not in security_policy.allowed_tools:
        logger.warning(f"Unauthorized tool proposed: {tool_name}")
        return ToolAuthorizationResult(
            authorized=False,
            tool_name=tool_name,
            reason=f"Tool '{tool_name}' is not in the authorized tool allowlist."
        )

    # 2. Maximum tool calls limit check
    if current_tool_call_count >= security_policy.max_tool_calls:
        logger.warning(f"Tool execution limit exceeded: {current_tool_call_count} >= {security_policy.max_tool_calls}")
        return ToolAuthorizationResult(
            authorized=False,
            tool_name=tool_name,
            reason=f"Tool execution limit of {security_policy.max_tool_calls} calls exceeded."
        )

    # 3. Tool-Specific Parameter Validation
    validated_args = dict(raw_args)

    if tool_upper == "SQL":
        sql_query = validated_args.get("sql_query") or validated_args.get("question", "")
        if isinstance(sql_query, str) and len(sql_query) > security_policy.max_sql_length:
            return ToolAuthorizationResult(
                authorized=False,
                tool_name=tool_name,
                reason=f"SQL query exceeds maximum character length of {security_policy.max_sql_length}."
            )
        if isinstance(sql_query, str) and ("INSERT" in sql_query.upper() or "UPDATE" in sql_query.upper() or "DELETE" in sql_query.upper()):
            return ToolAuthorizationResult(
                authorized=False,
                tool_name=tool_name,
                reason="SQL statement contains prohibited mutating keywords."
            )
        if isinstance(sql_query, str) and sql_query.strip().upper().startswith("SELECT"):
            sql_val_res = validate_sql(sql_query)
            if not sql_val_res.allowed:
                return ToolAuthorizationResult(
                    authorized=False,
                    tool_name=tool_name,
                    reason=f"SQL validation failed: {sql_val_res.reason}"
                )

    elif tool_upper == "SIMULATION":
        scenario_obj = validated_args.get("scenario")
        if isinstance(scenario_obj, SimulationScenario):
            is_valid, err = validate_scenario(scenario_obj)
            if not is_valid:
                return ToolAuthorizationResult(
                    authorized=False,
                    tool_name=tool_name,
                    reason=f"Simulation parameter validation failed: {err}"
                )
            if scenario_obj.transfer_quantity and scenario_obj.transfer_quantity > security_policy.max_transfer_quantity:
                return ToolAuthorizationResult(
                    authorized=False,
                    tool_name=tool_name,
                    reason=f"Transfer quantity {scenario_obj.transfer_quantity} exceeds policy maximum of {security_policy.max_transfer_quantity}."
                )

    elif tool_upper == "FORECAST":
        horizon = validated_args.get("horizon_days", 14)
        if isinstance(horizon, int) and (horizon < 1 or horizon > security_policy.max_simulation_horizon):
            return ToolAuthorizationResult(
                authorized=False,
                tool_name=tool_name,
                reason=f"Forecast horizon {horizon} days is outside allowed bounds (1-{security_policy.max_simulation_horizon})."
            )

    return ToolAuthorizationResult(
        authorized=True,
        tool_name=tool_name,
        validated_args=validated_args,
        reason="Tool execution authorized."
    )
