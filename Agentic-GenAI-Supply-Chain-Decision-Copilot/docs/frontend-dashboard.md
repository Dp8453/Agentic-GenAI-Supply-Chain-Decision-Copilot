# Phase 11 — Frontend Dashboard & AI Copilot UI Documentation

## 1. Overview
The **SupplyChain AI Frontend** is a modern, responsive, portfolio-quality React 18 web dashboard designed as an **advisory decision-support control tower**. It connects directly to the completed FastAPI backend (Phases 1–10) to display supply chain health, inventory risks, demand forecasts, supplier performance, conversational AI decisions, and what-if simulation deltas.

---

## 2. Architecture & Data Flow

```
React 18 User Interface (Vite 5 + Tailwind CSS + Recharts)
   │
   ▼
Centralized Axios API Client (`frontend/src/api/client.js`)
   │  - Timeout: 45s
   │  - Global Error Interceptor (HTTP 429, 500, Network Error)
   │  - Environment Base URL (`VITE_API_BASE_URL`)
   ▼
FastAPI REST Gateway (`http://localhost:8000/api/v1`)
   │
   ▼
Security Guardrails & Validation Layer (Phase 10)
   │
   ▼
LangGraph Multi-Tool Agent Orchestrator & Deterministic Engines
   │
   ▼
Structured API Responses
   │
   ▼
React UI Visualizations & Data Tables
```

---

## 3. Application Structure & Pages

| Route / Tab | Component | Description / API Integration |
| :--- | :--- | :--- |
| **Overview (`/`)** | `pages/Overview.jsx` | Operations control tower displaying high-level KPIs, risk distribution charts (Recharts PieChart), urgent procurement recommendations, and critical risk items table (`GET /api/v1/risk`, `GET /api/v1/recommendations`). |
| **Inventory (`/inventory`)** | `pages/Inventory.jsx` | Filterable inventory table (search SKU/name, risk level filters) with product detail modal showing safety stock, reorder points, stockout dates, and risk explanations (`GET /api/v1/risk`). |
| **Forecast (`/forecast`)** | `pages/Forecast.jsx` | XGBoost ML forecast viewer with interactive Recharts daily demand curves, 95% confidence bounds, horizon controls (7-90 days), and daily forecast breakdown table (`POST /api/v1/forecast`). |
| **Suppliers (`/suppliers`)** | `pages/Suppliers.jsx` | Supplier performance matrix displaying lead times, reliability scores, on-time delivery rates, and quality metrics (`POST /api/v1/sql/query` querying `suppliers` table). |
| **AI Copilot (`/copilot`)** | `pages/Copilot.jsx` | Conversational interface with starter question chips, structured message streams, advisory recommendations, trusted RAG sources, execution trace timeline, and guardrail block alert UX (`POST /api/v1/agent/query`). |
| **What-If Analysis (`/simulation`)** | `pages/Simulation.jsx` | Counterfactual scenario simulator supporting natural-language prompts and structured forms. Renders baseline vs scenario metrics, risk score deltas, and advisory recommendations (`POST /api/v1/simulation/query`, `POST /api/v1/simulation/run`). |

---

## 4. Strict Advisory UX & Safety Principles

1. **Zero Autonomous Execution**: The UI contains **zero execution buttons** (e.g. no "Execute Order", "Buy Now", or "Transfer Stock"). All actions (`REORDER`, `EXPEDITE`, `TRANSFER`, `MONITOR`, `ESCALATE`) are explicitly labeled as **Advisory Decisions Only**.
2. **Backend as Source of Truth**: React does not contain business formulas or calculations (safety stock, risk scores, forecast models, or scenario deltas are computed exclusively in Python).
3. **No Secret Disclosure**: LLM API keys and database credentials are excluded from frontend bundles.
4. **Security Block UX**: Requests blocked by Phase 10 input/prompt injection guardrails render clean, non-revealing alert notices.

---

## 5. Environment & Setup

### Environment Variables (`frontend/.env.example`)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Running Development Server
```powershell
cd frontend
npm run dev
```

### Production Build
```powershell
cd frontend
npm run build
```
