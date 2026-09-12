# SupplyChain AI — System Reliability & Resilience Architecture

## 1. Overview
System reliability in **SupplyChain AI** ensures that the application remains operational, responsive, and secure under network latency, LLM provider downtime, database disconnects, or malformed user prompts.

---

## 2. Resilience Strategies Matrix

| Subsystem / Dependency | Failure Mode | Resilience Strategy | Outcome / UX Behavior |
| :--- | :--- | :--- | :--- |
| **PostgreSQL Database** | Temporarily offline / starting up | Connection pool ping (`pool_pre_ping=True`), instant fallback to offline synthetic mode | Process remains alive, `/health` reports `disconnected`, UI displays offline banner |
| **LLM Provider (Ollama / OpenAI)** | Rate limited, API key invalid, or offline | `LLMProvider` catches HTTP/API exceptions and defaults to `FakeLLMProvider` deterministic fallbacks | Return grounded structured response with warning notice |
| **LangGraph Agent Tools** | Individual tool execution failure | Node catch block records step failure in `tool_trace` and continues execution using remaining tools | Partial result returned with explicit tool warning; zero fabricated data |
| **XGBoost ML Models** | Model artifact missing or corrupted | Fallback to historical daily demand moving average calculation | Returns demand prediction marked `moving_average_fallback` |
| **pgvector RAG Search** | Embeddings model or vector index unavailable | Returns empty chunk list without fabricating citations | System answers using transactional SQL/risk rules, stating document evidence is unavailable |
| **FastAPI Gateway** | Unhandled internal exception | Centralized `@app.exception_handler(Exception)` catches error, logs correlation ID, masks stack trace | Returns clean HTTP 500 JSON `{"error": {"code": "INTERNAL_SERVER_ERROR", ...}}` |
| **API Traffic Surge** | DoS / Client rate limit exceedance | `SlidingWindowRateLimiter` tracks IP requests ($60$ req/min limit) | Returns HTTP 429 `RATE_LIMIT_EXCEEDED`; Axios interceptor displays cooldown message |

---

## 3. Request Correlation & Observability

Every incoming HTTP request is assigned a unique UUID correlation ID (`X-Request-ID`):

```text
User Request -> Header X-Request-ID: e8f57912-3a81-4b10-8b42-89492167d41f
                 │
                 ├── Log: 2026-09-13 [INFO] main.py (e8f57912-...): POST /api/v1/agent/query status=200 duration=1240ms
                 └── Response Header -> X-Request-ID: e8f57912-3a81-4b10-8b42-89492167d41f
```

---

## 4. Timeouts & Boundary Limits

- **Axios HTTP Timeout**: $45\text{ seconds}$ (configured centrally in `frontend/src/api/client.js`).
- **FastAPI SQL Timeout**: $3.0\text{ seconds}$ statement execution timeout on PostgreSQL queries.
- **Max Agent Loop Iterations**: $5$ tool calls max (`MAX_TOOL_CALLS = 5`) per agent query.
- **Max Graph Recursion Depth**: $15$ steps max in LangGraph workflow.
