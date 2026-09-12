from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.llm.schemas import ExtractedEntities, IntentClassificationResult, IntentEnum
from app.rag.retriever import retrieve_relevant_chunks
from app.decision.service import evaluate_product_inventory_risk
from app.ml.predict import forecast_product


class LLMContext(BaseModel):
    """
    Structured context container passed to LLM for grounded synthesis.
    Integrates trusted database facts, deterministic risk metrics, ML forecasts, and RAG document chunks.
    """
    question: str = Field(..., description="Original user prompt")
    intent: str = Field(..., description="Classified question intent")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="RAG document chunks with metadata")
    risk_facts: Dict[str, Any] = Field(default_factory=dict, description="Deterministic risk engine output")
    forecast_facts: Dict[str, Any] = Field(default_factory=dict, description="Phase 3 ML forecast output")
    database_facts: Dict[str, Any] = Field(default_factory=dict, description="Structured DB metadata")
    warnings: List[str] = Field(default_factory=list, description="Context boundaries and warnings")

    def to_markdown(self) -> str:
        """
        Formats the context object into a structured markdown string for LLM system prompts.
        """
        lines = []

        # 1. RAG Documents
        if self.retrieved_chunks:
            lines.append("### RETRIEVED KNOWLEDGE BASE DOCUMENTS (RAG Evidence):")
            for idx, chunk in enumerate(self.retrieved_chunks, 1):
                doc_name = chunk.get("document_name", f"doc_{idx}.md")
                doc_type = chunk.get("document_type", "Policy/Contract")
                sec = chunk.get("metadata", {}).get("section", "General")
                sim = chunk.get("similarity", 0.0)
                lines.append(f"--- Document #{idx}: [{doc_name}] (Type: {doc_type}, Section: {sec}, Similarity: {sim:.4f}) ---")
                lines.append(chunk.get("content", "").strip())
                lines.append("")
        else:
            lines.append("### RETRIEVED KNOWLEDGE BASE DOCUMENTS: None retrieved.")

        # 2. Risk Engine Metrics
        if self.risk_facts:
            lines.append("### DETERMINISTIC INVENTORY RISK ENGINE METRICS:")
            lines.append(f"- SKU / Product: {self.risk_facts.get('sku')} ({self.risk_facts.get('product_name')})")
            lines.append(f"- Current Stock: {self.risk_facts.get('current_stock')} | Reserved Stock: {self.risk_facts.get('reserved_stock')}")
            lines.append(f"- Inventory Position: {self.risk_facts.get('inventory_position')}")
            lines.append(f"- Safety Stock: {self.risk_facts.get('safety_stock')} | Reorder Point: {self.risk_facts.get('reorder_point')}")
            lines.append(f"- Risk Score: {self.risk_facts.get('risk_score')}/100 | Level: {self.risk_facts.get('risk_level')}")
            lines.append(f"- Stockout Projected: {self.risk_facts.get('projected_stockout')} (Date: {self.risk_facts.get('projected_stockout_date')})")
            lines.append(f"- Recommended Action: {self.risk_facts.get('recommended_action')} (Order Qty: {self.risk_facts.get('recommended_order_quantity')})")
            if self.risk_facts.get("reasons"):
                lines.append("  Reasons: " + "; ".join(self.risk_facts.get("reasons", [])))
            lines.append("")

        # 3. Forecast Metrics
        if self.forecast_facts:
            lines.append("### MACHINE LEARNING DEMAND FORECAST METRICS:")
            lines.append(f"- Forecast Horizon: {self.forecast_facts.get('horizon_days')} days")
            lines.append(f"- Total Predicted Demand: {self.forecast_facts.get('total_predicted_demand')} units")
            lines.append(f"- Daily Avg Forecast: {self.forecast_facts.get('average_daily_demand')} units/day")
            lines.append("")

        # 4. Warnings
        if self.warnings:
            lines.append("### APPLICATION WARNINGS & BOUNDARIES:")
            for w in self.warnings:
                lines.append(f"- {w}")

        return "\n".join(lines)


def build_copilot_context(
    question: str,
    intent_result: IntentClassificationResult,
    supplier_filter: Optional[str] = None,
    doc_type_filter: Optional[str] = None,
    top_k: int = 5,
    db: Any = None
) -> LLMContext:
    """
    Assembles trusted application context across RAG Retriever, Risk Engine, and ML Forecast.
    """
    entities = intent_result.entities
    warnings = []

    # 1. Execute RAG Retrieval
    try:
        sup_filter = supplier_filter or entities.supplier
        rag_res = retrieve_relevant_chunks(
            query=question,
            top_k=top_k,
            supplier_filter=sup_filter,
            doc_type_filter=doc_type_filter,
            db=db
        )
        retrieved_chunks = rag_res.get("results", [])
    except Exception as e:
        warnings.append(f"RAG retrieval degraded: {str(e)}")
        retrieved_chunks = []

    # 2. Execute Deterministic Risk Engine if intent or entity requires inventory metrics
    risk_facts = {}
    target_pid = entities.product_id or 1  # Default to Product ID 1 for testing if SKU/product specified
    if intent_result.intent in [IntentEnum.INVENTORY_RISK, IntentEnum.FORECAST] or entities.sku:
        try:
            risk_facts = evaluate_product_inventory_risk(product_id=target_pid, db=db)
        except Exception as e:
            warnings.append(f"Inventory risk evaluation fallback: {str(e)}")
            risk_facts = {}

    # 3. Execute ML Demand Forecast if forecast intent or product specified
    forecast_facts = {}
    horizon = entities.horizon_days or 14
    if intent_result.intent == IntentEnum.FORECAST or entities.sku:
        try:
            forecast_facts = forecast_product(product_id=target_pid, horizon_days=horizon, db=db)
        except Exception as e:
            warnings.append(f"Demand forecast service fallback: {str(e)}")
            forecast_facts = {}

    return LLMContext(
        question=question,
        intent=intent_result.intent.value,
        entities=entities,
        retrieved_chunks=retrieved_chunks,
        risk_facts=risk_facts,
        forecast_facts=forecast_facts,
        warnings=warnings
    )
