import time
import datetime
import decimal
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.sql.schemas import SQLQueryResult

logger = logging.getLogger(__name__)


def serialize_value(val: Any) -> Any:
    """
    Converts database cell values (Date, DateTime, Decimal, Bytes) into JSON-serializable types.
    """
    if val is None:
        return None
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (bytes, bytearray)):
        return val.decode("utf-8", errors="ignore")
    return val


def execute_sql(
    validated_sql: str,
    db: Optional[Session] = None,
    timeout_seconds: float = 3.0,
    max_rows: int = 50
) -> SQLQueryResult:
    """
    Executes a validated read-only SQL query against the database with safety controls,
    statement timeout, row limits, and latency tracking.
    """
    warnings: List[str] = []
    start_time = time.time()

    if not db:
        return SQLQueryResult(
            columns=[],
            rows=[],
            row_count=0,
            truncated=False,
            execution_time_ms=0.0,
            warnings=["Database session unavailable; query execution skipped."]
        )

    try:
        # 1. Apply Statement Timeout for PostgreSQL if applicable
        try:
            db.execute(text(f"SET LOCAL statement_timeout = '{int(timeout_seconds * 1000)}ms'"))
        except Exception:
            pass  # SQLite does not support SET LOCAL statement_timeout

        # 2. Execute Query
        res = db.execute(text(validated_sql))
        columns = list(res.keys()) if hasattr(res, "keys") else []

        # 3. Fetch Rows with Max Row Cap
        raw_rows = res.fetchmany(max_rows + 1)
        truncated = len(raw_rows) > max_rows
        target_rows = raw_rows[:max_rows]

        formatted_rows = []
        for r in target_rows:
            row_dict = {}
            for col_name, val in zip(columns, r):
                row_dict[col_name] = serialize_value(val)
            formatted_rows.append(row_dict)

        if truncated:
            warnings.append(f"Result set exceeded max limit of {max_rows} rows; output was truncated.")

        exec_ms = round((time.time() - start_time) * 1000, 2)

        return SQLQueryResult(
            columns=columns,
            rows=formatted_rows,
            row_count=len(formatted_rows),
            truncated=truncated,
            execution_time_ms=exec_ms,
            warnings=warnings
        )

    except Exception as e:
        exec_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"SQL Execution Error: {e}")
        return SQLQueryResult(
            columns=[],
            rows=[],
            row_count=0,
            truncated=False,
            execution_time_ms=exec_ms,
            warnings=[f"SQL Execution Error: {str(e)}"]
        )
