from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class ScenarioTypeEnum(str, Enum):
    SUPPLIER_DELAY = "SUPPLIER_DELAY"
    DEMAND_INCREASE = "DEMAND_INCREASE"
    DEMAND_DECREASE = "DEMAND_DECREASE"
    LEAD_TIME_INCREASE = "LEAD_TIME_INCREASE"
    LEAD_TIME_DECREASE = "LEAD_TIME_DECREASE"
    WAREHOUSE_CAPACITY_CHANGE = "WAREHOUSE_CAPACITY_CHANGE"
    INVENTORY_TRANSFER = "INVENTORY_TRANSFER"
    UNKNOWN = "UNKNOWN"


class SimulationScenario(BaseModel):
    """
    Structured parameters defining a hypothetical what-if scenario.
    """
    scenario_type: ScenarioTypeEnum = Field(..., description="Type of what-if scenario")
    product_id: Optional[int] = Field(None, description="Target product ID (1-5)")
    sku: Optional[str] = Field(None, description="Target SKU code (e.g. SKU-001)")
    supplier_id: Optional[int] = Field(None, description="Target supplier ID")
    supplier_code: Optional[str] = Field(None, description="Target supplier code (e.g. SUP-001)")
    warehouse_id: Optional[int] = Field(None, description="Target warehouse ID")
    warehouse_code: Optional[str] = Field(None, description="Target warehouse code (e.g. WH-01)")
    source_warehouse: Optional[str] = Field(None, description="Source warehouse code for transfer")
    destination_warehouse: Optional[str] = Field(None, description="Destination warehouse code for transfer")
    delay_days: Optional[int] = Field(None, ge=0, description="Delay duration in days")
    demand_change_percent: Optional[float] = Field(None, description="Percentage change in demand (e.g. 20.0 for +20%)")
    lead_time_change_days: Optional[int] = Field(None, description="Change in lead time in days")
    capacity_change_percent: Optional[float] = Field(None, description="Percentage change in warehouse capacity")
    transfer_quantity: Optional[int] = Field(None, ge=0, description="Number of units to simulate transferring")
    horizon_days: int = Field(14, ge=1, le=90, description="Simulation forecast horizon in days")
    description: Optional[str] = Field(None, description="Human-readable scenario description")


class BaselineMetrics(BaseModel):
    """
    Current real-world inventory baseline state before scenario execution.
    """
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="SKU code")
    current_stock: int = Field(..., description="Current warehouse stock")
    reserved_stock: int = Field(..., description="Reserved stock")
    incoming_quantity: int = Field(..., description="Incoming PO quantity")
    inventory_position: int = Field(..., description="Effective inventory position")
    average_daily_demand: float = Field(..., description="Average daily demand rate")
    forecast_demand_lead_time: float = Field(..., description="Forecasted demand over lead-time horizon")
    lead_time_days: int = Field(..., description="Supplier lead time in days")
    safety_stock: int = Field(..., description="Calculated safety stock requirement")
    reorder_point: int = Field(..., description="Reorder point threshold")
    days_of_inventory: Optional[float] = Field(None, description="Days of stock coverage")
    projected_stockout: bool = Field(..., description="Whether stockout is projected within horizon")
    projected_stockout_date: Optional[str] = Field(None, description="Projected stockout date if applicable")
    risk_score: int = Field(..., ge=0, le=100, description="Baseline risk score (0-100)")
    risk_level: str = Field(..., description="Baseline risk level (LOW, MEDIUM, HIGH, CRITICAL)")


class SimulatedMetrics(BaseModel):
    """
    Projected inventory metrics resulting from the simulated scenario.
    """
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="SKU code")
    current_stock: int = Field(..., description="Simulated current warehouse stock")
    incoming_quantity: int = Field(..., description="Simulated incoming PO quantity")
    inventory_position: int = Field(..., description="Simulated effective inventory position")
    average_daily_demand: float = Field(..., description="Simulated average daily demand rate")
    forecast_demand_lead_time: float = Field(..., description="Simulated demand over lead-time horizon")
    lead_time_days: int = Field(..., description="Simulated supplier lead time in days")
    safety_stock: int = Field(..., description="Simulated safety stock requirement")
    reorder_point: int = Field(..., description="Simulated reorder point threshold")
    days_of_inventory: Optional[float] = Field(None, description="Simulated days of stock coverage")
    projected_stockout: bool = Field(..., description="Whether stockout occurs under simulated scenario")
    projected_stockout_date: Optional[str] = Field(None, description="Simulated stockout date if applicable")
    risk_score: int = Field(..., ge=0, le=100, description="Simulated risk score (0-100)")
    risk_level: str = Field(..., description="Simulated risk level (LOW, MEDIUM, HIGH, CRITICAL)")


class SimulationImpact(BaseModel):
    """
    Comparative delta analysis comparing Baseline vs Simulated scenario.
    """
    risk_score_change: int = Field(..., description="Delta in risk score (Simulated - Baseline)")
    days_of_inventory_change: Optional[float] = Field(None, description="Delta in stock coverage days")
    stockout_date_change: Optional[str] = Field(None, description="Shift in projected stockout date if any")
    impact_severity: str = Field(..., description="Impact severity classification (LOW, MEDIUM, HIGH, CRITICAL)")
    details: List[str] = Field(default_factory=list, description="Specific deterministic impact breakdown statements")


class SimulationRecommendation(BaseModel):
    """
    Advisory recommendation generated by the deterministic engine.
    """
    recommended_action: str = Field(..., description="Advisory action (MONITOR, REORDER, EXPEDITE, TRANSFER, ESCALATE)")
    priority: str = Field(..., description="Priority level (LOW, MEDIUM, HIGH, CRITICAL)")
    justification: str = Field(..., description="Deterministic justification based on impact delta")


class SimulationResult(BaseModel):
    """
    Complete structured output generated by the SimulationEngine.
    """
    scenario: SimulationScenario = Field(..., description="Parsed and validated scenario parameters")
    baseline: BaselineMetrics = Field(..., description="Pre-simulation baseline state")
    simulated: SimulatedMetrics = Field(..., description="Post-simulation projected state")
    impact: SimulationImpact = Field(..., description="Comparative delta analysis")
    recommendation: SimulationRecommendation = Field(..., description="Advisory recommendation")
    warnings: List[str] = Field(default_factory=list, description="Boundary disclaimers or assumption notices")


class SimulationRequest(BaseModel):
    """
    Request model for the What-If Simulation endpoint.
    """
    question: Optional[str] = Field(None, description="Natural language what-if question (e.g. 'What if Supplier ABC is delayed by 7 days?')")
    scenario: Optional[SimulationScenario] = Field(None, description="Direct structured scenario request")
    provider_override: Optional[str] = Field(None, description="Override LLM provider for scenario parsing (fake, ollama, openai)")


class SimulationResponse(BaseModel):
    """
    Full API response model bundling scenario analysis and grounded LLM explanation.
    """
    question: str = Field(..., description="Original user prompt or scenario description")
    scenario: SimulationScenario = Field(..., description="Parsed scenario parameters")
    baseline: BaselineMetrics = Field(..., description="Baseline metrics before simulation")
    simulated: SimulatedMetrics = Field(..., description="Simulated metrics after scenario application")
    impact: SimulationImpact = Field(..., description="Impact delta analysis")
    recommendation: SimulationRecommendation = Field(..., description="Advisory recommendation")
    explanation: str = Field(..., description="Grounded natural-language explanation of findings")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data provenance sources")
    warnings: List[str] = Field(default_factory=list, description="Simulation warnings and boundary notices")
