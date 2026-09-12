# LLM Layer & Structured Response System Architecture (`docs/llm.md`)

## Executive Overview

The **LLM Layer & Structured Response System** serves as the intelligence synthesis layer of **SupplyChain AI**. It sits on top of trusted deterministic tools (PostgreSQL Database, ML Forecasting Model, Inventory Risk Engine, and RAG Knowledge Base Retrieval) to translate raw quantitative metrics and unstructured document evidence into clear, actionable, natural-language answers.

---

## 1. Core Architectural Separation

SupplyChain AI maintains a strict separation between **LLM reasoning** and **deterministic computations**:

| Responsible Engine | Scope & Capabilities |
| :--- | :--- |
| **Deterministic Engines (Phase 1–5)** | Numerical calculations (Safety Stock, Reorder Point, Risk Scores 0-100, MOQ rounding), demand forecasting (XGBoost), vector similarity searching (384-dim dense embeddings + pgvector). **Source of Truth for numbers**. |
| **LLM Layer (Phase 6)** | Intent classification, entity parameter extraction, synthesizing retrieved RAG document chunks, explaining deterministic calculations, structuring JSON output responses, and citation validation. |

> [!IMPORTANT]
> The LLM is **never** permitted to calculate inventory metrics, invent stockout dates, fabricate supplier performance rates, or create fake document citations. All numerical facts originate from trusted application tools.

---

## 2. Provider Abstraction Architecture

To avoid tight vendor lock-in, the LLM layer is built on a clean `LLMProvider` interface:

```text
                  ┌──────────────────────┐
                  │     LLMProvider      │
                  │ (Abstract Base Class)│
                  └──────────┬───────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│OllamaProvider│     │OpenAIProvider│     │FakeLLMProvider │
│(Local / Free)│     │(Cloud / API) │     │ (Offline Test) │
└──────────────┘     └──────────────┘     └────────────────┘
```

### Supported Providers:
1. **`ollama` (Local / Free Path)**: Connects to local Ollama daemon via HTTP (`http://localhost:11434`), supporting local models like `llama3:latest` or `mistral`.
2. **`openai` (Cloud Path)**: Connects to OpenAI or OpenAI-compatible Chat Completions endpoints using structured JSON mode (`response_format={"type": "json_object"}`). Reads credentials securely from `LLM_API_KEY` or `OPENAI_API_KEY`.
3. **`fake` (Offline / Test Path)**: A 100% deterministic, zero-network mock provider that enables automated CI/CD test suites (`pytest backend/tests`) to execute instantly without requiring external LLM servers or API keys.

---

## 3. Intent Classification & Entity Extraction

User queries are analyzed by `LLMService.classify_intent()` to classify question intent into one of 7 categories and extract entity parameters:

```text
User Question: "Which SKU-001 products are at risk of stockout in the next 14 days?"
      ↓
Intent: INVENTORY_RISK
Extracted Entities: { sku: "SKU-001", horizon_days: 14 }
```

### Supported Intents:
- `INVENTORY_RISK`: Stockouts, safety stock, reorder points, risk scores.
- `FORECAST`: Predictive demand predictions and future sales trends.
- `SUPPLIER_INFORMATION`: Supplier reliability scores, on-time rates, lead times.
- `POLICY_QUESTION`: Internal procurement rules, reorder policies, emergency guidelines.
- `CONTRACT_QUESTION`: Supplier contract terms, penalty rates, delivery delay fees.
- `GENERAL_SUPPLY_CHAIN`: Broad supply chain concepts and definitions.
- `UNKNOWN`: Out-of-scope or ambiguous questions.

---

## 4. Context Assembly (`LLMContext`)

The `LLMContext` container aggregates trusted context before invoking the LLM:
- **RAG Evidence**: Top-$K$ retrieved document chunks with source metadata and similarity scores.
- **Risk Metrics**: Phase 4 Deterministic Risk Engine outputs (current stock, ROP, safety stock, risk score, stockout projection).
- **Forecast Metrics**: Phase 3 ML XGBoost predictions.
- **Application Warnings**: System boundaries or data gaps.

---

## 5. Groundedness & Citation Validation

To eliminate hallucinations:
1. **Strict System Prompt Instructions**: System prompts instruct the model to answer using *only* supplied facts.
2. **Post-Processing Citation Validation**: The `validate_and_sanitize_sources()` function inspects the LLM's returned `sources` list. If the model cites a document that was not retrieved in RAG evidence, the citation is stripped to guarantee 100% citation accuracy.

---

## 6. Machine-Readable Response Schema (`CopilotResponse`)

All LLM output is validated against the `CopilotResponse` Pydantic schema:

```json
{
  "summary": "Concise executive summary",
  "intent": "INVENTORY_RISK",
  "answer": "Grounded natural-language answer explaining metrics and policies",
  "risk_level": "HIGH",
  "affected_products": [
    {
      "sku": "SKU-001",
      "product_name": "Microcontroller Unit",
      "reason": "Inventory position below reorder point"
    }
  ],
  "recommended_actions": [
    {
      "action": "REORDER",
      "priority": "HIGH",
      "reason": "Replenish stock to cover 14-day forecast demand"
    }
  ],
  "explanation": "Analytical breakdown of metrics",
  "confidence": 0.92,
  "sources": [
    {
      "document_name": "supplier_globaltech_contract.md",
      "document_type": "Supplier Contract",
      "section": "2. Delay Terms & Escalation",
      "similarity": 0.8542
    }
  ],
  "data_used": ["PostgreSQL Database", "ML Forecast Model", "Risk Engine", "RAG Knowledge Base"],
  "warnings": ["Recommendation for decision support; purchasing execution requires confirmation."]
}
```

---

## 7. Failure & Graceful Degradation Handling

- **LLM Provider Offline / Unreachable**: If Ollama or OpenAI is offline, the API catches the error gracefully, returning a structured response containing deterministic metrics and explicit warning messages (`"LLM Provider unavailable"`), preventing application 500 crashes.
- **Malformed JSON Output**: Automatically strips code block markdown (` ```json `) and re-validates.

---

## 8. Automated Testing Strategy

The test suite in `backend/tests/test_llm.py` runs completely offline using `FakeLLMProvider`:
- Test Provider Factory
- Test Intent Classification & Entity Extraction
- Test Context Assembly
- Test Source Citation Validation
- Test Prompt Injection Defense (treating document text as DATA)
- Test `POST /api/v1/copilot/query` REST API
- Test Provider Fallback Behavior
