import re
from typing import Optional, List
from app.sql.schemas import SQLValidationResult
from app.sql.safety import APPROVED_TABLES, FORBIDDEN_KEYWORDS, SYSTEM_CATALOG_KEYWORDS


def validate_sql(sql_str: str, max_limit: int = 50) -> SQLValidationResult:
    """
    Validates SQL query for strict read-only safety, single-statement execution,
    table allowlisting, system catalog protection, and LIMIT normalization.
    """
    warnings: List[str] = []

    if not sql_str or not sql_str.strip():
        return SQLValidationResult(
            allowed=False,
            reason="SQL query cannot be empty.",
            warnings=warnings
        )

    raw_sql = sql_str.strip()

    # 1. Max Length Check (prevent memory inflation attacks)
    if len(raw_sql) > 2000:
        return SQLValidationResult(
            allowed=False,
            reason="SQL query exceeds maximum allowed length of 2000 characters.",
            warnings=warnings
        )

    # 2. Multi-Statement Detection (reject semicolons separating multiple commands)
    # Remove trailing semicolons first
    trimmed_semis = raw_sql.rstrip(";").strip()
    if ";" in trimmed_semis:
        return SQLValidationResult(
            allowed=False,
            reason="Multi-statement query detected. Only a single SELECT or WITH query is permitted.",
            warnings=warnings
        )

    # 3. Strip SQL comments (-- comment and /* comment */) before analysis
    no_comments = re.sub(r"--.*$", "", trimmed_semis, flags=re.MULTILINE)
    no_comments = re.sub(r"/\*.*?\*/", "", no_comments, flags=re.DOTALL).strip()

    # 4. Statement Type Check (Must start with SELECT or WITH)
    first_word = no_comments.split()[0].upper() if no_comments.split() else ""
    if first_word not in ["SELECT", "WITH"]:
        return SQLValidationResult(
            allowed=False,
            reason=f"Forbidden statement type '{first_word}'. Only SELECT and WITH queries are permitted.",
            warnings=warnings
        )

    # 5. Forbidden DML / DDL / DCL Keywords Inspection
    upper_sql = no_comments.upper()
    for forbidden in FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + forbidden + r"\b", upper_sql):
            return SQLValidationResult(
                allowed=False,
                reason=f"Forbidden SQL operation '{forbidden}' detected. Read-only safety policy violated.",
                warnings=warnings
            )

    # 6. System Catalog Protection
    for sys_keyword in SYSTEM_CATALOG_KEYWORDS:
        if re.search(r"\b" + sys_keyword + r"\b", upper_sql):
            return SQLValidationResult(
                allowed=False,
                reason=f"Access to system catalog/view '{sys_keyword}' is strictly prohibited.",
                warnings=warnings
            )

    # 7. Table Allowlist Inspection
    # Extract table names following FROM and JOIN keywords
    table_matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z0-9_\.\"\']+)", no_comments, re.IGNORECASE)
    referenced_tables = set()

    for tm in table_matches:
        # Clean quotes, schema prefixes (e.g. public.suppliers -> suppliers), and aliases
        clean_tbl = tm.strip().strip("\"'").split(".")[-1].lower()

        # Skip CTE names defined in WITH clause if any
        if clean_tbl and clean_tbl not in referenced_tables:
            referenced_tables.add(clean_tbl)

    for tbl in referenced_tables:
        # If table is not in APPROVED_TABLES and not a subquery/CTE identifier, verify approval
        # Note: Subquery aliases might be detected, so check if any unapproved non-cte table exists
        if tbl not in APPROVED_TABLES:
            # Check if CTE definition exists in WITH clause
            with_ctes = set(re.findall(r"([a-zA-Z0-9_]+)\s+AS\s*\(", no_comments, re.IGNORECASE))
            with_ctes_lower = {c.lower() for c in with_ctes}
            if tbl not in with_ctes_lower:
                return SQLValidationResult(
                    allowed=False,
                    reason=f"Access to unapproved table '{tbl}' is prohibited. Only approved supply-chain tables are accessible.",
                    warnings=warnings
                )

    # 8. LIMIT Clause Normalization
    normalized_sql = trimmed_semis
    limit_match = re.search(r"\bLIMIT\s+(\d+)", upper_sql)
    if limit_match:
        current_limit = int(limit_match.group(1))
        if current_limit > 500:
            warnings.append(f"Requested LIMIT {current_limit} capped to maximum 500 rows.")
            normalized_sql = re.sub(r"\bLIMIT\s+\d+", "LIMIT 500", normalized_sql, flags=re.IGNORECASE)
    else:
        warnings.append(f"No explicit LIMIT clause found; automatically appended LIMIT {max_limit}.")
        normalized_sql = f"{normalized_sql} LIMIT {max_limit}"

    return SQLValidationResult(
        allowed=True,
        reason="Query successfully passed read-only safety, single-statement, and table allowlist validation.",
        normalized_sql=normalized_sql,
        warnings=warnings
    )
