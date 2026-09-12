from pydantic import BaseModel, Field
from typing import List, Optional


class InventoryRiskItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    warehouse_id: int
    warehouse_code: str
    current_stock: int
    reserved_stock: int
    incoming_quantity: int
    inventory_position: int
    average_daily_demand: float
    forecast_demand_lead_time: float
    lead_time_days: int
    lead_time_std: float
    safety_stock: int
    reorder_point: int
    days_of_inventory: Optional[float]
    projected_stockout: bool
    projected_stockout_date: Optional[str]
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommended_action: str  # NO_ACTION, MONITOR, REORDER, URGENT_REORDER
    recommended_order_quantity: int
    reasons: List[str]
    warnings: List[str]


class RiskListResponse(BaseModel):
    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    items: List[InventoryRiskItem]


class RecommendationItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    warehouse_code: str
    supplier_id: int
    supplier_name: str
    current_stock: int
    inventory_position: int
    reorder_point: int
    minimum_order_quantity: int
    action: str  # NO_ACTION, MONITOR, REORDER, URGENT_REORDER
    recommended_order_quantity: int
    risk_level: str
    reasons: List[str]


class RecommendationsListResponse(BaseModel):
    total_recommendations: int
    urgent_reorders: int
    standard_reorders: int
    items: List[RecommendationItem]
