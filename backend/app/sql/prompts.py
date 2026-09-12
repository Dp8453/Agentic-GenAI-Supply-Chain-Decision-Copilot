DATABASE_SCHEMA_PROMPT_CONTEXT = """
POSTGRESQL DATABASE SCHEMA (APPROVED ANALYTICAL TABLES ONLY):

1. suppliers:
   - id (INTEGER, Primary Key)
   - supplier_code (VARCHAR(50), Unique, e.g. 'SUP-001')
   - name (VARCHAR(200), e.g. 'ABC Industrial Supplies')
   - location (VARCHAR(100), e.g. 'Chicago, IL')
   - reliability_score (FLOAT, 0.0 to 100.0)
   - average_lead_time_days (FLOAT)
   - contract_status (VARCHAR(50), e.g. 'ACTIVE', 'UNDER_REVIEW')

2. products:
   - id (INTEGER, Primary Key)
   - sku (VARCHAR(50), Unique, e.g. 'SKU-001')
   - name (VARCHAR(200), e.g. 'Microcontroller Unit')
   - category (VARCHAR(100), e.g. 'Electronics', 'Raw Materials')
   - unit_cost (FLOAT)
   - selling_price (FLOAT)
   - lead_time_days (INTEGER)
   - minimum_order_quantity (INTEGER, e.g. 50)
   - supplier_id (INTEGER, Foreign Key -> suppliers.id)

3. warehouses:
   - id (INTEGER, Primary Key)
   - warehouse_code (VARCHAR(50), Unique, e.g. 'WH-01')
   - name (VARCHAR(200), e.g. 'Main Central Warehouse')
   - location (VARCHAR(100), e.g. 'Dallas, TX')
   - capacity (INTEGER)

4. inventory:
   - id (INTEGER, Primary Key)
   - product_id (INTEGER, Foreign Key -> products.id)
   - warehouse_id (INTEGER, Foreign Key -> warehouses.id)
   - current_stock (INTEGER)
   - reserved_stock (INTEGER)
   - safety_stock (INTEGER)
   - reorder_point (INTEGER)

5. sales:
   - id (INTEGER, Primary Key)
   - product_id (INTEGER, Foreign Key -> products.id)
   - warehouse_id (INTEGER, Foreign Key -> warehouses.id)
   - sale_date (DATE)
   - quantity (INTEGER)
   - revenue (FLOAT)

6. purchase_orders:
   - id (INTEGER, Primary Key)
   - po_number (VARCHAR(50), Unique, e.g. 'PO-10023')
   - supplier_id (INTEGER, Foreign Key -> suppliers.id)
   - product_id (INTEGER, Foreign Key -> products.id)
   - warehouse_id (INTEGER, Foreign Key -> warehouses.id)
   - order_date (DATE)
   - expected_date (DATE)
   - actual_delivery_date (DATE, Nullable)
   - quantity (INTEGER)
   - received_quantity (INTEGER)
   - status (VARCHAR(30), e.g. 'PENDING', 'IN_TRANSIT', 'RECEIVED', 'DELAYED')

7. supplier_performance:
   - id (INTEGER, Primary Key)
   - supplier_id (INTEGER, Foreign Key -> suppliers.id)
   - date (DATE)
   - promised_lead_time (INTEGER)
   - actual_lead_time (INTEGER)
   - delay_days (INTEGER)
   - quality_score (FLOAT, 0.0 to 100.0)
   - on_time (BOOLEAN, True/False)

8. document_chunks:
   - id (INTEGER, Primary Key)
   - document_name (VARCHAR(255))
   - document_type (VARCHAR(100))
   - chunk_index (INTEGER)
   - content (TEXT)
"""

PROMPT_SQL_GENERATION = """
You are an expert PostgreSQL Data Analyst for SupplyChain AI.
Your task is to convert the following natural-language supply-chain question into a safe, valid PostgreSQL SELECT query.

CRITICAL RULES:
1. ONLY READ-ONLY SELECT / WITH STATEMENTS: Do NOT generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE statements.
2. ONLY APPROVED TABLES: Use ONLY the tables listed in the schema (suppliers, products, warehouses, inventory, sales, purchase_orders, supplier_performance, document_chunks).
3. PROPER JOIN CONDITIONS: Use foreign key relationships (e.g. products.supplier_id = suppliers.id, inventory.product_id = products.id).
4. SINGLE STATEMENT: Generate exactly ONE valid SQL query ending without a semicolon or multi-statement code block.
5. DEFAULT LIMIT: Append 'LIMIT 50' unless specified otherwise.

USER QUESTION:
"{question}"

DATABASE SCHEMA:
{schema_context}

Return your output matching the required JSON schema with 'sql' and 'explanation' fields.
"""

PROMPT_SQL_EXPLANATION = """
Explain the following returned SQL query results to a supply chain manager in clean, natural language.

USER QUESTION:
"{question}"

EXECUTED SQL QUERY:
```sql
{sql_query}
```

RETURNED DATA ROWS (JSON):
{rows_json}

INSTRUCTIONS:
1. Summarize the findings clearly.
2. Use ONLY the exact numbers returned in the rows data. Do NOT alter, round, or invent numerical figures.
3. If no rows were returned (empty result set), state clearly that no matching records were found in the database.
"""
