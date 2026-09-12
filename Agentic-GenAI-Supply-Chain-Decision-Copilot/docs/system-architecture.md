# SupplyChain AI — System Architecture Documentation

## 1. Executive Summary
**SupplyChain AI** is an enterprise-oriented, modular monolithic Agentic GenAI Decision-Support Copilot. It integrates PostgreSQL/pgvector transactional & vector databases, XGBoost ML demand forecasting, a deterministic inventory risk engine, pgvector RAG retrieval, safe natural-language-to-SQL execution, a LangGraph multi-tool agent orchestrator, a counterfactual what-if simulation engine, and an HTTP security guardrail layer, presented through a responsive React 18 operational control tower.

---

## 2. End-to-End System Topology

```
+-------------------------------------------------------------------------------+
|                       REACT 18 CONTROL TOWER (Vite 5)                         |
|   Overview  |  Inventory  |  Forecast  |  Suppliers  | Copilot |  Simulation  |
+---------------------------------------+---------------------------------------+
                                        | HTTP / JSON (Axios Client, Timeout 45s)
                                        v
+-------------------------------------------------------------------------------+
|                       FASTAPI API GATEWAY (main.py)                           |
|   Observability (Correlation ID X-Request-ID) | Global Exception Masking          |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                  PHASE 10 SECURITY GUARDRAILS & VALIDATION                    |
|   Input Bounds | Prompt Injection Scanner | Tool Allowlist | Rate Limiter     |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                  LANGGRAPH MULTI-TOOL AGENT ORCHESTRATOR                      |
|                                                                               |
|   Planner Node  -----> Router -----> Tool Selection Execution Nodes            |
|                                         |  |  |  |  |                         |
|      +----------------------------------+  |  |  |  +---------------+        |
|      |               +---------------------+  |  +----------+       |        |
|      v               v                        v             v       v        |
|   SQL Tool       RAG Tool              Forecast Tool    Risk Tool Sim Tool   |
|      |               |                        |             |       |        |
+------|---------------|------------------------|-------------|-------|--------+
       |               |                        |             |       |
       v               v                        v             v       v
+--------------+ +--------------+        +--------------+ +---------------+
| PostgreSQL   | | pgvector     |        | XGBoost      | | Deterministic |
| Transactional| | RAG Vector   |        | Forecasting  | | Inventory Risk|
| RDBMS        | | Embeddings   |        | Models       | | & Sim Engine  |
+--------------+ +--------------+        +--------------+ +---------------+
       ^               ^                        ^             ^       ^
       |               |                        |             |       |
       +---------------+------------------------+-------------+-------+
                                        | Structured Data & Evidence
                                        v
+-------------------------------------------------------------------------------+
|                   OUTPUT VALIDATION & PROVENANCE GENERATOR                    |
|   Numerical Claim Verification (2.0% Tolerance) | RAG Citation Filtering      |
|   Sensitive Credential Redaction (sk-*, DB URIs) | Safe Fallback Formatting   |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       STRUCTURED RESPONSE TO REACT UI                         |
+-------------------------------------------------------------------------------+
```

---

## 3. Core Component Subsystems

### A. Database Subsystem (`backend/app/database/`)
- **PostgreSQL 16 + pgvector**: Relational storage for products, warehouses, inventory stock positions, purchase orders, sales transactions, and suppliers.
- **pgvector Vector Store**: Stores 384-dimensional embeddings (`all-MiniLM-L6-v2`) of chunked supply chain documents (supplier contracts, procurement policies, logistics SLAs).

### B. XGBoost Demand Forecasting Subsystem (`backend/app/ml/`)
- **Multi-Step Recursive ML Predictor**: Trained XGBoost regressor predicting daily SKU demand over horizons ($1\text{--}90$ days) with lower and upper $95\%$ confidence bounds.

### C. Inventory Intelligence & Risk Subsystem (`backend/app/decision/`)
- **Deterministic Risk Engine**: Calculates safety stock ($Z \times \sigma_L$), reorder points ($D_{\text{lead}} + \text{SS}$), stockout dates, inventory position ($S_{\text{onhand}} + S_{\text{incoming}} - S_{\text{reserved}}$), and risk severity levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### D. Safe NL-to-SQL Subsystem (`backend/app/sql/`)
- **SQLGlot AST Validator**: Parses natural-language generated SQL into Abstract Syntax Trees, guaranteeing `SELECT`-only execution, table allowlisting, single statement enforcement, and maximum row limits ($50$ rows).

### E. What-If Simulation Subsystem (`backend/app/simulation/`)
- **In-Memory Counterfactual Engine**: Evaluates hypothetical supplier delays, demand surges, lead-time changes, and inventory transfers in memory without mutating PostgreSQL data.

### F. Security & Validation Layer (`backend/app/guardrails/`)
- **Fail-Closed Security Service**: Multilayered defense enforcing input boundary checks, prompt injection pattern detection, RAG chunk untrusted data isolation, tool authorization allowlisting, numerical claim verification ($2.0\%$ tolerance), RAG citation verification, credential redaction, sliding-window rate limiting ($60$ req/min), and global exception masking.

---

## 4. Technology Stack Summary

- **Backend**: FastAPI 0.110+, Python 3.11, Pydantic v2, SQLAlchemy 2.0, psycopg2, Uvicorn.
- **Machine Learning & NLP**: XGBoost 2.0+, scikit-learn 1.4+, Sentence-Transformers, NumPy, Pandas.
- **RAG & LangGraph**: LangChain 0.1+, LangGraph 0.0.26+, pgvector, sqlglot.
- **Frontend**: React 18, Vite 5, Tailwind CSS 3, Recharts 2.12, Lucide React, Axios.
- **Containerization**: Docker, Docker Compose, Nginx 1.25.
