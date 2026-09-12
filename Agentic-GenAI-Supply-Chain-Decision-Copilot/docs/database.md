# Database Design & Architecture Guide — SupplyChain AI

## 1. Overview & Technology Rationale

The database layer for **SupplyChain AI** is built on **PostgreSQL 16** with the **`pgvector`** extension. It serves as the single source of transactional truth for inventory levels, supplier reliability records, purchase order status, historical sales, and vector embeddings for contract RAG retrieval.

### Key Architectural Choices
- **PostgreSQL 16**: Industry-standard ACID-compliant relational database providing transactional guarantees, foreign key cascade safety, and powerful query optimization.
- **pgvector Extension**: Enables vector similarity search directly inside PostgreSQL using standard SQL (`<->` L2 distance, `<=>` cosine distance). Eliminates the operational overhead of a separate vector database (e.g., Pinecone/Weaviate).
- **SQLAlchemy 2.0 ORM**: Type-safe Python object-relational mapping providing explicit constraint validation, relationship management, and repository pattern encapsulation.

---

## 2. Entity Relationship Schema

```
[Supplier] 1 ──── N [Product] 1 ──── N [Inventory] N ──── 1 [Warehouse]
    │                 │                    │                     │
    ├─ 1 ── N [PO] ◄──┴──────── 1 ── N [PO] ◄────────────────────┘
    │                 │
    └─ 1 ── N [Perf]  └─ 1 ── N [Sale] ── N ── 1 [Warehouse]
```

---

## 3. Tables & Schema Specifications

### `suppliers`
Tracks primary vendor information, contractual agreements, and baseline lead times.
- `id` (INT, PK): Unique primary key.
- `supplier_code` (VARCHAR(50), UNIQUE, INDEX): Human-readable code (e.g., `SUP-001`).
- `name` (VARCHAR(200)): Supplier business name.
- `location` (VARCHAR(100)): City/Country location.
- `reliability_score` (FLOAT): Score between 0.0 and 100.0 based on historical delivery performance.
- `average_lead_time_days` (FLOAT): Baseline promised lead time in days (>0).
- `contract_status` (VARCHAR(50)): `ACTIVE`, `UNDER_REVIEW`, `SUSPENDED`.

### `products`
Catalog of all managed SKUs.
- `id` (INT, PK): Primary key.
- `sku` (VARCHAR(50), UNIQUE, INDEX): Stock Keeping Unit code (e.g., `SKU-102`).
- `name` (VARCHAR(200)): Product description.
- `category` (VARCHAR(100), INDEX): Category (`Electronics`, `Industrial Components`, etc.).
- `unit_cost` (FLOAT): Procurement cost per unit (>0).
- `selling_price` (FLOAT): Customer price per unit (>0).
- `lead_time_days` (INT): Default reorder lead time in days.
- `minimum_order_quantity` (INT): Supplier MOQ (>0).
- `supplier_id` (INT, FK -> `suppliers.id`, INDEX): Primary vendor.

### `warehouses`
Physical fulfillment and storage facilities.
- `id` (INT, PK): Primary key.
- `warehouse_code` (VARCHAR(50), UNIQUE, INDEX): Code (e.g., `WH-EAST`).
- `name` (VARCHAR(200)): Warehouse name.
- `location` (VARCHAR(100)): Physical location.
- `capacity` (INT): Total storage capacity in units (>0).

### `inventory`
Real-time snapshot of stock levels across product-warehouse pairs.
- `id` (INT, PK): Primary key.
- `product_id` (INT, FK -> `products.id`, INDEX).
- `warehouse_id` (INT, FK -> `warehouses.id`, INDEX).
- `current_stock` (INT): Physical units on hand (>=0).
- `reserved_stock` (INT): Units committed to pending orders (>=0).
- `safety_stock` (INT): Minimum buffer stock threshold (>=0).
- `reorder_point` (INT): Stock level that triggers reorder (>=0).
- *Constraints*: `UNIQUE(product_id, warehouse_id)`.

### `sales`
Historical sales transactions used by the ML forecasting module.
- `id` (INT, PK): Primary key.
- `product_id` (INT, FK -> `products.id`, INDEX).
- `warehouse_id` (INT, FK -> `warehouses.id`, INDEX).
- `sale_date` (DATE, INDEX): Date of transaction.
- `quantity` (INT): Units sold (>=0).
- `revenue` (FLOAT): Total transaction revenue (>=0).
- *Indexes*: `idx_sales_product_date(product_id, sale_date)`.

### `purchase_orders`
Tracks outbound replenishment orders to vendors.
- `id` (INT, PK): Primary key.
- `po_number` (VARCHAR(50), UNIQUE, INDEX): PO identifier (e.g., `PO-2024001`).
- `supplier_id` (INT, FK -> `suppliers.id`, INDEX).
- `product_id` (INT, FK -> `products.id`, INDEX).
- `warehouse_id` (INT, FK -> `warehouses.id`, INDEX).
- `order_date` (DATE): Date order was placed.
- `expected_date` (DATE, INDEX): Promised arrival date.
- `actual_delivery_date` (DATE, NULLABLE): Realized arrival date.
- `quantity` (INT): Units ordered (>0).
- `received_quantity` (INT): Units received (>=0).
- `status` (VARCHAR(30), INDEX): `PENDING`, `IN_TRANSIT`, `DELIVERED`, `DELAYED`, `CANCELLED`.

### `supplier_performance`
Periodic historical evaluations for vendor risk scoring.
- `id` (INT, PK): Primary key.
- `supplier_id` (INT, FK -> `suppliers.id`, INDEX).
- `date` (DATE, INDEX): Monthly evaluation date.
- `promised_lead_time` (INT): Lead time promised.
- `actual_lead_time` (INT): Actual lead time experienced.
- `delay_days` (INT): Days overdue (>=0).
- `quality_score` (FLOAT): 0-100 score.
- `on_time` (BOOLEAN): Delivery punctuality flag.

### `document_chunks`
Vector store table for procurement policies and supplier contract RAG.
- `id` (INT, PK): Primary key.
- `document_name` (VARCHAR(255), INDEX): File name (e.g., `supplier_abc_contract.pdf`).
- `document_type` (VARCHAR(100), INDEX): Category (`contract`, `policy`, `logistics`).
- `chunk_index` (INT): Sequential chunk position.
- `content` (TEXT): Text content of document chunk.
- `metadata` (JSONB): Structured metadata (page number, clause title, dates).
- `embedding` (VECTOR(384)): 384-dimensional dense vector embeddings generated by `all-MiniLM-L6-v2`.

---

## 4. Index Optimization Strategy

1. **`idx_sales_product_date(product_id, sale_date)`**: Speeds up time-series data extractions for the ML XGBoost forecaster when fetching product sales histories.
2. **`products.sku` & `suppliers.supplier_code`**: Enables instant lookup for natural language SQL queries referencing specific SKUs or supplier codes.
3. **`purchase_orders.status` & `expected_date`**: Optimizes inventory risk queries looking for delayed incoming replenishment.
