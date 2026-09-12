from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class EvaluationCategory(str, Enum):
    DETERMINISTIC_RISK = "DETERMINISTIC_RISK"
    ML_FORECASTING = "ML_FORECASTING"
    RAG_RETRIEVAL = "RAG_RETRIEVAL"
    NL_TO_SQL = "NL_TO_SQL"
    AGENT_ROUTING = "AGENT_ROUTING"
    WHAT_IF_SIMULATION = "WHAT_IF_SIMULATION"
    SECURITY_GUARDRAILS = "SECURITY_GUARDRAILS"
    END_TO_END = "END_TO_END"


class EvaluationCase(BaseModel):
    id: str = Field(..., description="Unique case ID, e.g. CASE-RISK-01")
    category: EvaluationCategory = Field(..., description="Category of evaluation case")
    query: str = Field(..., description="Input query or prompt")
    context: Dict[str, Any] = Field(default_factory=dict, description="Input parameters, payload, or context")
    expected_outputs: Dict[str, Any] = Field(default_factory=dict, description="Expected ground truth outputs and criteria")


class MetricResult(BaseModel):
    metric_name: str = Field(..., description="Name of metric e.g. MAE, Hit@1, AST_ReadOnly_Pass")
    score: float = Field(..., description="Numerical metric value")
    passed: bool = Field(..., description="Whether score meets target threshold")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional breakdown or diagnostic metrics")


class EvaluationResult(BaseModel):
    case_id: str = Field(..., description="Case identifier")
    category: EvaluationCategory = Field(..., description="Evaluation category")
    passed: bool = Field(..., description="Overall status for case")
    metrics: List[MetricResult] = Field(default_factory=list, description="Computed metrics for case")
    actual_output: Dict[str, Any] = Field(default_factory=dict, description="Observed runtime result")
    error: Optional[str] = Field(None, description="Error trace if case failed unexpectedly")


class CategorySummary(BaseModel):
    category: EvaluationCategory = Field(..., description="Category name")
    total_cases: int = Field(0, description="Total cases executed in category")
    passed_cases: int = Field(0, description="Number of passed cases")
    pass_rate: float = Field(0.0, description="Pass percentage (0.0 to 100.0)")
    key_metrics: Dict[str, float] = Field(default_factory=dict, description="Aggregated category metric averages")


class EvaluationReport(BaseModel):
    timestamp: str = Field(..., description="Execution timestamp")
    total_cases: int = Field(0, description="Total cases evaluated across suite")
    passed_cases: int = Field(0, description="Total cases passed")
    overall_pass_rate: float = Field(0.0, description="Overall pass rate percentage")
    category_summaries: List[CategorySummary] = Field(default_factory=list, description="Per-category summaries")
    results: List[EvaluationResult] = Field(default_factory=list, description="Detailed case results")
