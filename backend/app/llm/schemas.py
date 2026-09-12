from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class IntentEnum(str, Enum):
    INVENTORY_RISK = "INVENTORY_RISK"
    FORECAST = "FORECAST"
    SUPPLIER_INFORMATION = "SUPPLIER_INFORMATION"
    POLICY_QUESTION = "POLICY_QUESTION"
    CONTRACT_QUESTION = "CONTRACT_QUESTION"
    GENERAL_SUPPLY_CHAIN = "GENERAL_SUPPLY_CHAIN"
    UNKNOWN = "UNKNOWN"


class ExtractedEntities(BaseModel):
    product_id: Optional[int] = Field(None, description="Extracted Product ID")
    sku: Optional[str] = Field(None, description="Extracted Stock Keeping Unit")
    supplier: Optional[str] = Field(None, description="Extracted Supplier Name or Code")
    warehouse_id: Optional[int] = Field(None, description="Extracted Warehouse ID")
    horizon_days: Optional[int] = Field(None, description="Extracted Time Horizon in Days")


class IntentClassificationResult(BaseModel):
    intent: IntentEnum = Field(..., description="Classified intent category")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities, description="Extracted entity parameters")
    reasoning: str = Field("", description="Explanation for classification choice")


class Source(BaseModel):
    document_name: str = Field(..., description="Name of the cited document file")
    document_type: Optional[str] = Field(None, description="Type/Category of document")
    section: Optional[str] = Field(None, description="Section header or title")
    similarity: Optional[float] = Field(None, description="Vector similarity score")


class AffectedProduct(BaseModel):
    sku: str = Field(..., description="Product SKU code")
    product_name: str = Field(..., description="Descriptive product name")
    reason: str = Field(..., description="Explanation of risk or status")


class RecommendedAction(BaseModel):
    action: str = Field(..., description="Action title (e.g. REORDER, MONITOR, ESCALATE)")
    priority: str = Field(..., description="Priority level (HIGH, MEDIUM, LOW)")
    reason: str = Field(..., description="Justification for recommendation")


class CopilotResponse(BaseModel):
    summary: str = Field(..., description="Concise executive summary of answer")
    intent: str = Field(..., description="Identified question intent")
    answer: str = Field(..., description="Comprehensive grounded natural-language answer")
    risk_level: Optional[str] = Field(None, description="Associated overall risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    affected_products: List[AffectedProduct] = Field(default_factory=list, description="List of products mentioned or impacted")
    recommended_actions: List[RecommendedAction] = Field(default_factory=list, description="Machine-readable recommendations")
    explanation: str = Field(..., description="Detailed analytical explanation of facts")
    confidence: float = Field(..., description="Application-level evidence confidence score (0.0 to 1.0)")
    sources: List[Source] = Field(default_factory=list, description="Retrieved evidence document citations")
    data_used: List[str] = Field(default_factory=list, description="Data sources utilized (e.g. RAG, Risk Engine, Forecast)")
    warnings: List[str] = Field(default_factory=list, description="Disclaimers, data gaps, or boundary notices")


class CopilotQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question from user")
    supplier_filter: Optional[str] = Field(None, description="Optional supplier filter")
    document_type_filter: Optional[str] = Field(None, description="Optional document type filter")
    top_k: int = Field(5, ge=1, le=20, description="Max RAG chunks to retrieve")
    provider_override: Optional[str] = Field(None, description="Override default LLM provider (fake, ollama, openai)")
