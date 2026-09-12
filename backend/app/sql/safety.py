from typing import Set

# Approved application tables for analytical read-only access
APPROVED_TABLES: Set[str] = {
    "suppliers",
    "products",
    "warehouses",
    "inventory",
    "sales",
    "purchase_orders",
    "supplier_performance",
    "document_chunks"
}

# Strictly forbidden DML, DDL, DCL, and administration operations
FORBIDDEN_KEYWORDS: Set[str] = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "MERGE", "CALL", "EXEC", "COPY",
    "DO", "INTO"
}

# Forbidden system catalog tables and views
SYSTEM_CATALOG_KEYWORDS: Set[str] = {
    "PG_USER", "PG_SHADOW", "PG_AUTHID", "INFORMATION_SCHEMA",
    "PG_CATALOG", "PG_ROLES", "PG_STAT_ACTIVITY"
}

# PostgreSQL Defense-in-Depth Read-Only Role Creation Script for Documentation
READONLY_USER_SETUP_SQL: str = """
-- 1. Create a dedicated read-only database user
CREATE ROLE supplychain_readonly WITH LOGIN PASSWORD 'supplychain_readonly_pass';

-- 2. Grant connection & usage permissions
GRANT CONNECT ON DATABASE supplychain_db TO supplychain_readonly;
GRANT USAGE ON SCHEMA public TO supplychain_readonly;

-- 3. Grant SELECT permission ONLY on approved application tables
GRANT SELECT ON suppliers TO supplychain_readonly;
GRANT SELECT ON products TO supplychain_readonly;
GRANT SELECT ON warehouses TO supplychain_readonly;
GRANT SELECT ON inventory TO supplychain_readonly;
GRANT SELECT ON sales TO supplychain_readonly;
GRANT SELECT ON purchase_orders TO supplychain_readonly;
GRANT SELECT ON supplier_performance TO supplychain_readonly;
GRANT SELECT ON document_chunks TO supplychain_readonly;

-- 4. Alter default privileges to prevent write access on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO supplychain_readonly;
"""
