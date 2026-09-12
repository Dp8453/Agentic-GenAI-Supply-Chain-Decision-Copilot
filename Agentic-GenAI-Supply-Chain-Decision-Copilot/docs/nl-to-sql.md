# Safe Natural-Language-to-SQL Tool Architecture (`docs/nl-to-sql.md`)

## Executive Overview

The **Safe Natural-Language-to-SQL Tool** allows users to ask analytical supply-chain questions in natural language (e.g., *"Which suppliers have an on-time delivery rate below 85%?"* or *"Show top 10 products by sales volume"*).

The tool translates natural-language prompts into PostgreSQL queries, subjects them to strict AST/regex read-only safety validation, executes valid queries safely with row limits and timeouts, and returns structured data alongside grounded LLM explanations.

---

## 1. End-to-End Pipeline Architecture

```text
User Question
      ↓
LLM SQL Generator (generator.py + prompts.py)
      ↓
Generated SQL Query
      ↓
SQL Safety Validator (validator.py + safety.py)
 ┌────┴─────────────────────────────┐
 │ Allowed = False?                 │ Allowed = True?
 ▼                                  ▼
BLOCK EXECUTION                 SQL Executor (executor.py)
Return Error Response                ↓ (3s Timeout, Max 50 Rows)
                                Structured Rows JSON
                                     ↓
                                LLM Result Explainer (service.py)
                                     ↓
                                Final SQLResponse
```

---

## 2. Strict Read-Only Safety & Security Guardrails

Security is enforced through **Defense-in-Depth**:

### A. Statement Type & Single-Statement Rules
- **Allowed Statements**: Only `SELECT` and `WITH` (Common Table Expressions / CTEs) are permitted.
- **Multi-Statement Defense**: Queries containing semicolons separating multiple commands (e.g. `SELECT * FROM suppliers; DROP TABLE suppliers;`) are immediately rejected.

### B. Forbidden Keywords Blacklist
The `SQLValidator` rejects any query containing DML, DDL, DCL, or administration operations:
`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, `MERGE`, `CALL`, `EXEC`, `COPY`, `DO`, `INTO`.

### C. System Catalog & Credential Protection
Blocks any access to PostgreSQL system catalogs or metadata views:
`pg_user`, `pg_shadow`, `pg_authid`, `information_schema`, `pg_catalog`, `pg_roles`.

### D. Table Allowlist
Queries are restricted strictly to approved analytical supply-chain tables:
- `suppliers`
- `products`
- `warehouses`
- `inventory`
- `sales`
- `purchase_orders`
- `supplier_performance`
- `document_chunks`

Attempted access to unapproved tables (e.g. `internal_passwords`, `user_accounts`) triggers an immediate rejection before database execution.

---

## 3. Defense-in-Depth Read-Only PostgreSQL Role

For production deployment, PostgreSQL is configured with a dedicated read-only role (`supplychain_readonly`):

```sql
-- Create dedicated read-only database user
CREATE ROLE supplychain_readonly WITH LOGIN PASSWORD 'supplychain_readonly_pass';
GRANT CONNECT ON DATABASE supplychain_db TO supplychain_readonly;
GRANT USAGE ON SCHEMA public TO supplychain_readonly;

-- Grant SELECT permission ONLY on approved tables
GRANT SELECT ON suppliers TO supplychain_readonly;
GRANT SELECT ON products TO supplychain_readonly;
GRANT SELECT ON warehouses TO supplychain_readonly;
GRANT SELECT ON inventory TO supplychain_readonly;
GRANT SELECT ON sales TO supplychain_readonly;
GRANT SELECT ON purchase_orders TO supplychain_readonly;
GRANT SELECT ON supplier_performance TO supplychain_readonly;
GRANT SELECT ON document_chunks TO supplychain_readonly;
```

---

## 4. Query Execution Controls & Timeouts

To prevent denial-of-service (DoS) or memory inflation from expensive queries:
- **Statement Timeout**: PostgreSQL queries execute with `SET LOCAL statement_timeout = '3000ms'` (3-second hard timeout).
- **Row Limit Normalization**: Queries without a `LIMIT` clause are automatically appended with `LIMIT 50`. Excessive limits above 500 are capped to `LIMIT 500`.
- **Latency Tracking**: Execution latency is tracked in `execution_time_ms`.

---

## 5. REST API Endpoint (`POST /api/v1/sql/query`)

- **Request Payload**:
  ```json
  {
    "question": "Which purchase orders are currently delayed?",
    "limit_override": 10
  }
  ```
- **Response Format (`SQLResponse`)**:
  ```json
  {
    "question": "Which purchase orders are currently delayed?",
    "generated_sql": "SELECT po.po_number, s.name, po.status FROM purchase_orders po JOIN suppliers s ON po.supplier_id = s.id WHERE po.status = 'DELAYED' LIMIT 10",
    "validation": {
      "allowed": true,
      "reason": "Query successfully passed read-only safety, single-statement, and table allowlist validation.",
      "normalized_sql": "SELECT po.po_number, s.name, po.status FROM purchase_orders po JOIN suppliers s ON po.supplier_id = s.id WHERE po.status = 'DELAYED' LIMIT 10",
      "warnings": []
    },
    "result": {
      "columns": ["po_number", "name", "status"],
      "rows": [
        {
          "po_number": "PO-10023",
          "name": "GlobalTech Components",
          "status": "DELAYED"
        }
      ],
      "row_count": 1,
      "truncated": false,
      "execution_time_ms": 1.45,
      "warnings": []
    },
    "explanation": "1 purchase order (PO-10023 from GlobalTech Components) is currently delayed.",
    "warnings": []
  }
  ```

---

## 6. Automated Testing & Security Regression

Tested via `backend/tests/test_sql.py` (10/10 tests passed):
- Valid `SELECT` & `WITH` CTE queries.
- Rejection of DML/DDL write keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, etc.).
- Rejection of multi-statement attacks (`SELECT ...; DROP TABLE ...;`).
- Rejection of system catalog queries (`pg_user`, `information_schema`).
- **Security Regression Test**: `test_malicious_llm_generated_sql_blocked_and_never_executed()` verifying that if an LLM returns `DROP TABLE suppliers;`, `SQLValidator` intercepts and blocks execution (`allowed=False`) and the database session is **NEVER** called.
