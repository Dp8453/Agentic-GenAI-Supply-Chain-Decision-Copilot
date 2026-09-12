from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from sqlalchemy.orm import Session
import pandas as pd
import os

from app.database.connection import get_db
from app.database.models import Product, Supplier
from app.decision.service import evaluate_product_inventory_risk
from app.decision.schemas import (
    InventoryRiskItem, RiskListResponse, RecommendationItem, RecommendationsListResponse
)

router = APIRouter()


@router.get("/risk", response_model=RiskListResponse, summary="List Deterministic Inventory Risk Profiles")
async def get_inventory_risks(
    warehouse_id: Optional[int] = Query(None, description="Filter by Warehouse ID"),
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    risk_level: Optional[str] = Query(None, description="Filter by Risk Level (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(50, gt=0, le=500, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """
    Evaluates and retrieves inventory risk scores, stockout projections, and explanations across products.
    """
    product_ids = []
    if product_id:
        product_ids = [product_id]
    else:
        try:
            products = db.query(Product.id).all()
            product_ids = [p.id for p in products]
        except Exception:
            raw_p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "products.csv")
            if os.path.exists(raw_p):
                df = pd.read_csv(raw_p)
                product_ids = df["id"].tolist()
            else:
                product_ids = [1, 2, 3]

    items = []
    for pid in product_ids[:limit]:
        try:
            item_dict = evaluate_product_inventory_risk(product_id=pid, warehouse_id=warehouse_id, db=db)
            if risk_level and item_dict["risk_level"].upper() != risk_level.upper():
                continue
            items.append(InventoryRiskItem(**item_dict))
        except Exception:
            continue

    crit_cnt = sum(1 for i in items if i.risk_level == "CRITICAL")
    high_cnt = sum(1 for i in items if i.risk_level == "HIGH")
    med_cnt = sum(1 for i in items if i.risk_level == "MEDIUM")
    low_cnt = sum(1 for i in items if i.risk_level == "LOW")

    return RiskListResponse(
        total_count=len(items),
        critical_count=crit_cnt,
        high_count=high_cnt,
        medium_count=med_cnt,
        low_count=low_cnt,
        items=items
    )


@router.get("/risk/{product_id}", response_model=InventoryRiskItem, summary="Get Product Inventory Risk Profile")
async def get_product_risk(
    product_id: int,
    warehouse_id: Optional[int] = Query(None, description="Filter by Warehouse ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieves the detailed deterministic inventory risk profile and stockout forecast for a specific product.
    """
    try:
        item_dict = evaluate_product_inventory_risk(product_id=product_id, warehouse_id=warehouse_id, db=db)
        return InventoryRiskItem(**item_dict)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate risk: {str(e)}")


@router.get("/recommendations", response_model=RecommendationsListResponse, summary="Get Deterministic Procurement Recommendations")
async def get_recommendations(
    action: Optional[str] = Query(None, description="Filter by action (REORDER, URGENT_REORDER, MONITOR)"),
    limit: int = Query(50, gt=0, le=500),
    db: Session = Depends(get_db)
):
    """
    Retrieves deterministic procurement recommendations (reorder quantities & MOQ rounding).
    """
    try:
        products = db.query(Product).all()
        prod_dict = {p.id: p for p in products}
        suppliers = db.query(Supplier).all()
        supp_dict = {s.id: s.name for s in suppliers}
        product_ids = [p.id for p in products]
    except Exception:
        raw_p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "products.csv")
        raw_s = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "suppliers.csv")
        p_df = pd.read_csv(raw_p) if os.path.exists(raw_p) else pd.DataFrame()
        s_df = pd.read_csv(raw_s) if os.path.exists(raw_s) else pd.DataFrame()
        product_ids = p_df["id"].tolist() if not p_df.empty else []
        prod_dict = {}
        supp_dict = {}

    rec_items = []
    for pid in product_ids[:limit]:
        try:
            risk = evaluate_product_inventory_risk(product_id=pid, db=db)
            if risk["recommended_action"] in ["REORDER", "URGENT_REORDER"]:
                if action and risk["recommended_action"].upper() != action.upper():
                    continue

                p_obj = prod_dict.get(pid)
                supp_name = supp_dict.get(p_obj.supplier_id, "Unknown Vendor") if p_obj else "Vendor"
                moq = p_obj.minimum_order_quantity if p_obj else 50

                rec_items.append(RecommendationItem(
                    product_id=pid,
                    sku=risk["sku"],
                    product_name=risk["product_name"],
                    warehouse_code=risk["warehouse_code"],
                    supplier_id=p_obj.supplier_id if p_obj else 1,
                    supplier_name=supp_name,
                    current_stock=risk["current_stock"],
                    inventory_position=risk["inventory_position"],
                    reorder_point=risk["reorder_point"],
                    minimum_order_quantity=moq,
                    action=risk["recommended_action"],
                    recommended_order_quantity=risk["recommended_order_quantity"],
                    risk_level=risk["risk_level"],
                    reasons=risk["reasons"]
                ))
        except Exception:
            continue

    urgent_cnt = sum(1 for r in rec_items if r.action == "URGENT_REORDER")
    std_cnt = sum(1 for r in rec_items if r.action == "REORDER")

    return RecommendationsListResponse(
        total_recommendations=len(rec_items),
        urgent_reorders=urgent_cnt,
        standard_reorders=std_cnt,
        items=rec_items
    )
