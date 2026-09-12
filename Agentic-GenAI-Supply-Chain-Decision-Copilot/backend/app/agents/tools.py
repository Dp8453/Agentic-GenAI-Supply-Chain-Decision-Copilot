import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.sql.service import SQLService
from app.rag.retriever import retrieve_relevant_chunks
from app.ml.predict import forecast_product
from app.decision.service import evaluate_product_inventory_risk

logger = logging.getLogger(__name__)


def execute_sql_tool(
    question: str,
    db: Optional[Session] = None,
    provider_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrapper around Phase 7 Safe Natural-Language-to-SQL Service.
    Enforces read-only AST/regex validation, execution timeouts, and limit capping.
    """
    try:
        sql_service = SQLService(provider_name=provider_override)
        res = sql_service.execute_natural_language_query(
            question=question,
            db=db,
            provider_override=provider_override
        )
        return {
            "status": "success" if res.validation.allowed else "blocked",
            "sql": res.generated_sql,
            "allowed": res.validation.allowed,
            "validation_reason": res.validation.reason,
            "columns": res.result.columns,
            "rows": res.result.rows,
            "row_count": res.result.row_count,
            "explanation": res.explanation,
            "warnings": res.warnings
        }
    except Exception as e:
        logger.error(f"SQL Tool execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "sql": None,
            "allowed": False,
            "rows": [],
            "row_count": 0,
            "explanation": f"Database query failed due to an error: {e}",
            "warnings": [f"SQL Tool error: {e}"]
        }


def execute_rag_tool(
    query: str,
    top_k: int = 5,
    supplier_filter: Optional[str] = None,
    doc_type_filter: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Wrapper around Phase 5 Vector Grounded Retrieval Service.
    Retrieves policy documents, supplier contracts, and guidelines.
    """
    try:
        rag_res = retrieve_relevant_chunks(
            query=query,
            top_k=top_k,
            supplier_filter=supplier_filter,
            doc_type_filter=doc_type_filter,
            db=db
        )
        chunks = rag_res.get("chunks", [])
        return {
            "status": "success",
            "chunks": chunks,
            "count": len(chunks),
            "query": query,
            "warnings": []
        }
    except Exception as e:
        logger.error(f"RAG Tool execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "chunks": [],
            "count": 0,
            "query": query,
            "warnings": [f"RAG Tool error: {e}"]
        }


def execute_forecast_tool(
    product_id: int = 1,
    horizon_days: int = 14,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Wrapper around Phase 3 Machine Learning Demand Forecasting Model.
    Produces multi-step XGBoost recursive demand predictions.
    """
    try:
        fc_res = forecast_product(
            product_id=product_id,
            horizon_days=horizon_days,
            db=db
        )
        return {
            "status": "success",
            "product_id": product_id,
            "sku": fc_res.get("sku"),
            "horizon_days": horizon_days,
            "total_predicted_demand": fc_res.get("total_predicted_demand", 0.0),
            "forecast_items": fc_res.get("forecast", []),
            "mae": fc_res.get("mae", 5.0),
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Forecast Tool execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "product_id": product_id,
            "horizon_days": horizon_days,
            "total_predicted_demand": 0.0,
            "forecast_items": [],
            "warnings": [f"Forecast Tool error for product {product_id}: {e}"]
        }


def execute_risk_tool(
    product_id: int = 1,
    warehouse_id: Optional[int] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Wrapper around Phase 4 Deterministic Inventory Risk & Recommendation Engine.
    Evaluates safety stock, reorder point, inventory position, stockout timeline, and recommendations.
    """
    try:
        risk_res = evaluate_product_inventory_risk(
            product_id=product_id,
            warehouse_id=warehouse_id,
            db=db
        )
        return {
            "status": "success",
            "product_id": product_id,
            "sku": risk_res.get("sku"),
            "product_name": risk_res.get("product_name"),
            "category": risk_res.get("category"),
            "current_stock": risk_res.get("current_stock"),
            "reserved_stock": risk_res.get("reserved_stock"),
            "incoming_quantity": risk_res.get("incoming_quantity"),
            "inventory_position": risk_res.get("inventory_position"),
            "reorder_point": risk_res.get("reorder_point"),
            "safety_stock": risk_res.get("safety_stock"),
            "days_of_inventory": risk_res.get("days_of_inventory"),
            "projected_stockout": risk_res.get("projected_stockout"),
            "projected_stockout_date": risk_res.get("projected_stockout_date"),
            "risk_score": risk_res.get("risk_score"),
            "risk_level": risk_res.get("risk_level"),
            "recommended_action": risk_res.get("recommended_action"),
            "recommended_order_quantity": risk_res.get("recommended_order_quantity"),
            "reasons": risk_res.get("reasons", []),
            "warnings": risk_res.get("warnings", [])
        }
    except Exception as e:
        logger.error(f"Risk Tool execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "product_id": product_id,
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "recommended_action": "MONITOR",
            "recommended_order_quantity": 0,
            "reasons": [f"Risk Engine evaluation failed: {e}"],
            "warnings": [f"Risk Tool error for product {product_id}: {e}"]
        }


def execute_simulation_tool(
    question: str,
    db: Optional[Session] = None,
    provider_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrapper around Phase 9 What-If Simulation Engine.
    Parses scenario, loads baseline, runs deterministic calculations, and returns comparative delta.
    """
    try:
        from app.simulation.service import SimulationService
        sim_service = SimulationService(provider_name=provider_override)
        res = sim_service.run_simulation(
            question=question,
            db=db,
            provider_override=provider_override
        )
        return {
            "status": "success",
            "scenario_type": res.scenario.scenario_type.value,
            "sku": res.simulated.sku,
            "baseline": res.baseline.model_dump(),
            "simulated": res.simulated.model_dump(),
            "impact": res.impact.model_dump(),
            "recommendation": res.recommendation.model_dump(),
            "explanation": res.explanation,
            "warnings": res.warnings
        }
    except Exception as e:
        logger.error(f"Simulation Tool execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "explanation": f"What-If Simulation could not be executed: {e}",
            "warnings": [f"Simulation Tool error: {e}"]
        }
