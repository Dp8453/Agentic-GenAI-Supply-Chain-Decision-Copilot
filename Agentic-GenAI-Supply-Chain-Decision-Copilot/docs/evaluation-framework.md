# SupplyChain AI — Evaluation Framework & AI Quality Validation

## Executive Summary

Phase 13 introduces an offline, reproducible, end-to-end **Evaluation Framework & AI Quality Validation Suite** for **SupplyChain AI**. 

The evaluation suite quantitatively benchmarks the system across 10 core dimensions:
1. **Deterministic Inventory Intelligence**: Formula parity and risk score classification accuracy.
2. **ML Demand Forecasting Quality**: MAE, RMSE, sMAPE, WAPE, and prediction bounds integrity.
3. **RAG Vector Retrieval Precision**: Hit@1, Hit@3, Hit@5, MRR (Mean Reciprocal Rank), and chunk grounding.
4. **Natural-Language-to-SQL Correctness & Safety**: Semantic query parsing, read-only AST safety validation, and rejection of malicious commands.
5. **Agent Routing & Workflow Efficiency**: Tool routing precision, multi-tool delegation accuracy, and step iteration bounds ($\le 5$ steps).
6. **What-If Simulation Invariants**: Property-based counterfactual deltas and **0 PostgreSQL database state mutations**.
7. **Numerical Grounding**: Alignment of LLM numerical claims against Python ground truth within a $2.0\%$ tolerance.
8. **Citation Validity**: Verification of cited RAG document sources against retrieved evidence chunks.
9. **Security Guardrail Robustness**: $0$ security bypasses across prompt injection, jailbreaks, secret extraction, malicious SQL, and rate limits.
10. **End-to-End System Scenarios**: Comprehensive user journeys executed offline without paid LLM API costs.

---

## Architectural Principles

1. **Measurement Over Manufacturing**: All metrics are computed strictly from empirical execution of evaluation cases against runtime engines.
2. **100% Offline & Repeatable**: The evaluation suite runs offline using fake providers and internal evaluation engines, requiring zero external API keys.
3. **No Private CoT Storage**: Only observable inputs, tool selections, tool outputs, retrieved chunks, citations, and final answers are recorded.
4. **Modular Monolith Preservation**: Evaluation code resides under `backend/tests/evaluation/` to preserve clear separation without introducing external microservices or message brokers.

---

## Golden Benchmark Dataset Schema

The golden benchmark dataset is stored in `backend/tests/evaluation/datasets/golden_dataset.json` and contains **62 structured evaluation cases**.

```json
{
  "id": "CASE-RISK-01",
  "category": "DETERMINISTIC_RISK",
  "query": "Evaluate risk for high stockout SKU",
  "context": {
    "sku": "SKU-101",
    "avg_daily_demand": 50.0,
    "lead_time_days": 10.0,
    "std_demand": 10.0,
    "service_level_z": 1.65,
    "current_stock": 100.0,
    "on_order": 50.0,
    "unit_cost": 25.0
  },
  "expected_outputs": {
    "safety_stock": 52.18,
    "reorder_point": 552.18,
    "inventory_position": 150.0,
    "risk_level": "CRITICAL",
    "stockout_risk": true
  }
}
```

---

## Evaluation Metrics & Thresholds

| Metric | Target Threshold | Category | Description |
| :--- | :--- | :--- | :--- |
| **SafetyStockFormulaAccuracy** | $\le 5$ units diff | Deterministic Risk | Verifies $Z \times \sigma_L$ calculation |
| **ReorderPointFormulaAccuracy** | $\le 5$ units diff | Deterministic Risk | Verifies $D_{\text{lead}} + \text{SS}$ calculation |
| **RiskLevelClassificationAccuracy** | 100% match | Deterministic Risk | Verifies LOW/MEDIUM/HIGH/CRITICAL bounds |
| **HorizonLengthCompliance** | 100% pass | ML Forecasting | Horizon length matches request |
| **NonNegativeDemandCheck** | 100% pass | ML Forecasting | All predicted quantities $\ge 0.0$ |
| **ConfidenceBoundsIntegrity** | 100% pass | ML Forecasting | Lower Bound $\le$ Pred $\le$ Upper Bound |
| **Hit@5 Retrieval** | $\ge 90.0\%$ | RAG Retrieval | Relevant chunk present in top 5 |
| **ReciprocalRank (MRR)** | $> 0.5$ | RAG Retrieval | Rank of first relevant chunk |
| **AST_ReadOnly_Safety_Pass** | 100% pass | NL-to-SQL | Rejects DML/DDL/Multi-statements |
| **ToolRoutingPrecision** | $\ge 80.0\%$ | Agent Routing | Correct tools selected for query |
| **AgentIterationStepBoundsPass** | $\le 5$ steps | Agent Routing | Execution stays within step limit |
| **ZeroDatabaseMutationsCheck** | 100% pass | What-If Simulation | DB state remains strictly unchanged |
| **ZeroSecurityBypass** | 100% pass | Security Guardrails | Blocks prompt injection and secret leaks |
| **NumericalGroundingPass** | $\le 2.0\%$ tolerance | Grounding | Claim numbers match Python truth |

---

## Running the Evaluation Suite

To run the complete Phase 13 evaluation suite:

```powershell
python -m pytest backend/tests/evaluation -v
```

To run the entire project test suite (Unit + Integration + Evaluation):

```powershell
python -m pytest backend/tests -v
```

Artifacts generated:
- `evaluation-report.json`: Machine-readable evaluation report
- `evaluation-report.md`: Markdown summary table of pass rates and key metrics
