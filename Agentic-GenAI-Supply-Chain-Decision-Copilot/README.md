# Agentic GenAI Supply Chain Decision Copilot (SupplyChain AI)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Build & Tests](https://img.shields.io/badge/Backend%20Tests-82%2F82%20PASSED-brightgreen.svg)]()

An enterprise-ready agentic GenAI decision-support control tower combining LLM reasoning, pgvector RAG, natural-language SQL, XGBoost machine-learning forecasting, deterministic inventory risk calculation, what-if counterfactual simulation, and HTTP security guardrails into an operational React web dashboard.

---

## 📌 Executive Summary & Architecture

SupplyChain AI bridges operational supply chain management and generative AI by keeping **numerical logic in deterministic Python engines** while using **LLMs for planning, reasoning, and synthesis**:

- **Deterministic Truth**: Safety stock ($Z \times \sigma_L$), reorder points ($D_{\text{lead}} + \text{SS}$), XGBoost demand predictions, stockout dates, and what-if simulation deltas are calculated strictly by verified Python services.
- **LangGraph Multi-Tool Agent**: Supervisor Planner graph dynamically routing natural-language queries across SQL DB, pgvector RAG, ML Forecast, Risk Engine, and Simulation Sandbox tools.
- **Security Guardrails**: Multilayered defense enforcing input bounds ($2000$ chars), instruction override pattern matching, AST SQL `SELECT`-only execution, numerical claim verification ($2.0\%$ tolerance), RAG citation filtering, credential redaction, and sliding-window rate limiting ($60$ req/min).
- **Advisory UI**: React control tower providing visual dashboards, filterable risk matrices, interactive forecast curves, conversational copilot streams, and scenario comparison cards without automated purchasing execution buttons.

```
                  ┌───────────────────────┐
                  │   React Control Tower │ (Overview, Inventory, Forecast, Copilot)
                  └───────────┬───────────┘
                              │ HTTP / JSON (Axios Client, Timeout 45s)
                              ▼
                  ┌───────────────────────┐
                  │   FastAPI Gateway     │ (Observability X-Request-ID, Health/Ready)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Security Guardrails  │ (Prompt Injection, AST SQL, Rate Limit)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   LangGraph Agent     │ (Planner -> SQL / RAG / ML / Sim Tools)
                  └───────────┬───────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          SQL/RDBMS          RAG              ML
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │ Decision & Risk Engine│ (Safety Stock, Reorder Point, Stockouts)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  What-If Simulation   │ (Counterfactual In-Memory Sandbox)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Output Validation     │ (Numerical Claim Check, Citation Audit)
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ React UI Presentation │
                  └───────────────────────┘
```

---

## 🚀 Tech Stack

- **Frontend**: React 18, Vite 5, Tailwind CSS 3, Recharts 2.12, Lucide Icons, Axios.
- **Backend**: Python 3.11, FastAPI 0.110+, Pydantic v2, SQLAlchemy 2.0, Uvicorn.
- **AI & Agentic Orchestration**: LangGraph 0.0.26+, LangChain 0.1+, Ollama / OpenAI / Fake Providers.
- **Database & Vector Store**: PostgreSQL 16 + `pgvector` 0.2+.
- **Machine Learning & NLP**: XGBoost 2.0+, Scikit-Learn 1.4+, Pandas, NumPy, Sentence-Transformers.
- **Containerization**: Docker, Docker Compose, Nginx 1.25.

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 2. Environment Configuration
Copy `.env.example` to `.env` in the `backend/` directory:
```bash
cp backend/.env.example backend/.env
```

### 3. Database Container Startup
Start PostgreSQL with the pgvector extension:
```bash
docker-compose up -d postgres
```

### 4. Synthetic Data & Database Initialization
Populate PostgreSQL schema and synthetic supply chain records:
```bash
cd backend
python -m app.database.synthetic_generator
```

### 5. Backend Service Startup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Liveness Endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- API Readiness Endpoint: [http://localhost:8000/api/v1/ready](http://localhost:8000/api/v1/ready)
- Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Frontend Web Dashboard Startup
```bash
cd frontend
npm install
npm run dev
```
- Web Application Interface: [http://localhost:5173](http://localhost:5173)

---

## 🐳 Docker Production Quick Start

To launch the full containerized stack (PostgreSQL + FastAPI + Nginx React Frontend):
```bash
docker compose up --build -d
```
- Web Dashboard: [http://localhost:3000](http://localhost:3000)
- Backend REST API: [http://localhost:8000](http://localhost:8000)

---

## 🧪 Automated Testing

Execute the complete backend unit and integration test suite:
```bash
python -m pytest backend/tests -v
```

Execute frontend production build verification:
```bash
cd frontend
npm run build
```

---

## 📋 Development Roadmap

- [x] **Phase 1: Project Foundation** (FastAPI, React/Vite, Tailwind, Docker Compose, Health Check)
- [x] **Phase 2: Database Schema & Synthetic Supply Chain Data Generator**
- [x] **Phase 3: Machine Learning Demand Forecasting Module**
- [x] **Phase 4: Inventory Intelligence & Risk Engine**
- [x] **Phase 5: RAG Pipeline with pgvector**
- [x] **Phase 6: Structured LLM Output Schemas & Response Generator**
- [x] **Phase 7: Safe Natural-Language-to-SQL Tool**
- [x] **Phase 8: LangGraph Multi-Tool Agent Orchestrator**
- [x] **Phase 9: What-If Simulation Sandbox**
- [x] **Phase 10: Security Guardrails & Human-in-the-Loop Controls**
- [x] **Phase 11: Rich UI Dashboard & AI Copilot Interface**
- [x] **Phase 12: End-to-End System Integration, Reliability & Production-Readiness**
- [x] **Phase 13: Automated & GenAI Evaluation Suite** (62 Golden Benchmark Cases, 10 Evaluation Categories, 100% Offline Repeatability)
- [ ] **Phase 14: Documentation & Interview Defense Guide**

---

## 📊 Evaluation & AI Quality Validation

SupplyChain AI includes an automated, offline, reproducible **Evaluation Framework & AI Quality Validation Suite** (`backend/tests/evaluation/`):

- **62 Golden Benchmark Cases**: Across 8 functional categories (Deterministic Risk, ML Forecasting, RAG Retrieval, NL-to-SQL, Agent Routing, What-If Simulation, Security Guardrails, and End-to-End Scenarios).
- **10 Evaluation Dimensions**:
  1. *Deterministic Risk*: Formula accuracy ($Z \times \sigma_L$, $D_{\text{lead}} + \text{SS}$) & risk score classification.
  2. *ML Forecasting*: MAE, RMSE, sMAPE, WAPE, non-negative demand, confidence bounds.
  3. *RAG Retrieval*: Hit@1, Hit@3, Hit@5, MRR, chunk grounding.
  4. *NL-to-SQL*: Read-only AST compliance, single-statement enforcement, 0 malicious executions.
  5. *Agent Routing*: Tool selection precision & step bounds ($\le 5$).
  6. *What-If Simulation*: Counterfactual deltas & **0 PostgreSQL database state mutations**.
  7. *Security Guardrails*: 0 bypasses across prompt injection, jailbreaks, secret extraction, malicious SQL, rate limits.
  8. *Numerical Grounding*: Claim verification against Python truth within $2.0\%$ tolerance.
  9. *Citation Validity*: Citation source verification against retrieved chunks.
  10. *End-to-End*: Offline user journey verification.

Run the evaluation suite:
```powershell
python -m pytest backend/tests/evaluation -v
```

Generated reports:
- `evaluation-report.json`: Machine-readable evaluation report
- `evaluation-report.md`: Markdown summary table of pass rates and key metrics

---

## 🛡️ License & Advisory Disclaimer
MIT License. **SupplyChain AI** is an advisory decision-support system. All outputs, risk scores, forecasts, and recommendations are provided for analytical guidance only and do not execute automated purchase orders or physical inventory transfers.
