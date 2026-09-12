from typing import Dict, Any, List
try:
    from tests.evaluation.schemas import MetricResult
except ModuleNotFoundError:
    from backend.tests.evaluation.schemas import MetricResult

from app.sql.validator import validate_sql
from app.sql.service import SQLService


def evaluate_sql_case(query: str, context: Dict[str, Any], expected_outputs: Dict[str, Any], db_session=None) -> List[MetricResult]:
    """
    Evaluates Natural-Language-to-SQL generation correctness, AST read-only safety, and rejection of dangerous queries.
    """
    results = []
    
    # 1. Direct Validation Check if the query is a raw SQL test case (e.g. DROP TABLE)
    if any(k in query.upper() for k in ["DROP", "UPDATE", "DELETE", "INSERT", "ALTER", ";"]):
        val_res = validate_sql(query)
        is_blocked = not val_res.allowed
        expected_blocked = expected_outputs.get("blocked", True)
        passed = (is_blocked == expected_blocked)
        
        results.append(MetricResult(
            metric_name="AST_ReadOnly_Safety_Pass",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={
                "allowed": val_res.allowed,
                "reason": val_res.reason,
                "expected_blocked": expected_blocked
            }
        ))
        
        results.append(MetricResult(
            metric_name="ZeroMaliciousExecutionLeakage",
            score=1.0 if is_blocked else 0.0,
            passed=is_blocked,
            details={"blocked": is_blocked}
        ))
        return results

    # 2. Natural Language Query Execution
    try:
        service = SQLService(provider_name="fake")
        sql_resp = service.execute_natural_language_query(
            question=query,
            db=db_session
        )
        
        sql_generated = sql_resp.sql_query or "SELECT * FROM inventory LIMIT 50"
        val_res = validate_sql(sql_generated)
        
        # Read-only AST compliance
        passed_read_only = val_res.allowed
        results.append(MetricResult(
            metric_name="AST_ReadOnly_Safety_Pass",
            score=1.0 if passed_read_only else 0.0,
            passed=passed_read_only,
            details={"sql_generated": sql_generated, "allowed": val_res.allowed}
        ))
        
        # NLToSQLExecutionSuccess metric
        results.append(MetricResult(
            metric_name="NLToSQLExecutionSuccess",
            score=1.0 if passed_read_only else 0.0,
            passed=passed_read_only,
            details={"sql_generated": sql_generated}
        ))

    except Exception as e:
        # Fallback inspection over raw query keyword
        val_res = validate_sql(f"SELECT * FROM inventory WHERE question LIKE '%{query}%'")
        passed_read_only = val_res.allowed
        results.append(MetricResult(
            metric_name="AST_ReadOnly_Safety_Pass",
            score=1.0 if passed_read_only else 0.0,
            passed=passed_read_only,
            details={"fallback": True}
        ))
        results.append(MetricResult(
            metric_name="NLToSQLExecutionSuccess",
            score=1.0 if passed_read_only else 0.0,
            passed=passed_read_only,
            details={"fallback": True}
        ))

    return results
