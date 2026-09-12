import os
import math
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models import Product, Supplier, Warehouse, Inventory, Sale, PurchaseOrder, SupplierPerformance
from app.ml.predict import forecast_product
from app.decision.inventory import (
    calculate_inventory_position, calculate_demand_stats, calculate_lead_time_stats,
    calculate_safety_stock, calculate_reorder_point, calculate_days_of_inventory
)
from app.decision.risk import (
    project_inventory_timeline, calculate_risk_score, generate_deterministic_reasons
)
from app.decision.recommendations import (
    classify_recommendation_action, calculate_recommended_reorder_quantity
)
from app.decision.schemas import InventoryRiskItem, RecommendationItem


def evaluate_product_inventory_risk(
    product_id: int,
    warehouse_id: Optional[int] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Evaluates comprehensive inventory risk and produces deterministic recommendations for a product.
    Consumes DB repository data and Phase 3 ML demand forecasting with graceful fallback to CSV dataset.
    """
    warnings = []
    prod = None

    # 1. Fetch Product metadata (with CSV fallback for unseeded DB testing)
    if db:
        try:
            prod = db.query(Product).filter(Product.id == product_id).first()
            if prod:
                sku = prod.sku
                prod_name = prod.name
                category = prod.category
                lead_time_days = prod.lead_time_days
                moq = prod.minimum_order_quantity
                supplier_id = prod.supplier_id
        except Exception:
            prod = None

    if not prod:
        raw_prod = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "products.csv")
        if os.path.exists(raw_prod):
            p_df = pd.read_csv(raw_prod)
            row = p_df[p_df["id"] == product_id]
            if row.empty:
                raise ValueError(f"Product ID {product_id} not found.")
            r = row.iloc[0]
            sku = str(r["sku"])
            prod_name = str(r["name"])
            category = str(r["category"])
            lead_time_days = int(r["lead_time_days"])
            moq = int(r["minimum_order_quantity"])
            supplier_id = int(r["supplier_id"])
        else:
            raise ValueError(f"Product ID {product_id} not found and dataset missing.")

    # 2. Fetch Inventory Record
    inv = None
    if db:
        try:
            inv_query = db.query(Inventory).filter(Inventory.product_id == product_id)
            if warehouse_id:
                inv_query = inv_query.filter(Inventory.warehouse_id == warehouse_id)
            inv = inv_query.first()
        except Exception:
            inv = None

    if inv:
        current_stock = inv.current_stock
        reserved_stock = inv.reserved_stock
        target_wh_id = inv.warehouse_id
        wh = db.query(Warehouse).filter(Warehouse.id == target_wh_id).first() if db else None
        wh_code = wh.warehouse_code if wh else f"WH-{target_wh_id:02d}"
    else:
        raw_inv = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "inventory.csv")
        if os.path.exists(raw_inv):
            i_df = pd.read_csv(raw_inv)
            matching = i_df[i_df["product_id"] == product_id]
            if warehouse_id:
                matching = matching[matching["warehouse_id"] == warehouse_id]
            if not matching.empty:
                r = matching.iloc[0]
                current_stock = int(r["current_stock"])
                reserved_stock = int(r["reserved_stock"])
                target_wh_id = int(r["warehouse_id"])
                wh_code = f"WH-{target_wh_id:02d}"
            else:
                current_stock, reserved_stock, target_wh_id, wh_code = 0, 0, 1, "WH-DEFAULT"
                warnings.append("No warehouse inventory record found.")
        else:
            current_stock, reserved_stock, target_wh_id, wh_code = 0, 0, 1, "WH-DEFAULT"
            warnings.append("No warehouse inventory record found.")

    # 3. Fetch Incoming POs
    incoming_quantity = 0
    incoming_orders = []
    pos = []
    if db:
        try:
            pos = db.query(PurchaseOrder).filter(
                PurchaseOrder.product_id == product_id,
                PurchaseOrder.warehouse_id == target_wh_id,
                PurchaseOrder.status.in_(["PENDING", "IN_TRANSIT", "DELAYED"])
            ).all()
        except Exception:
            pos = []

    if pos:
        for po in pos:
            rem = po.quantity - po.received_quantity
            if rem > 0:
                incoming_quantity += rem
                incoming_orders.append({"expected_date": str(po.expected_date), "quantity": rem})
    else:
        raw_po = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "purchase_orders.csv")
        if os.path.exists(raw_po):
            po_df = pd.read_csv(raw_po)
            m_po = po_df[(po_df["product_id"] == product_id) & (po_df["warehouse_id"] == target_wh_id) & (po_df["status"].isin(["PENDING", "IN_TRANSIT", "DELAYED"]))]
            for _, r in m_po.iterrows():
                rem = int(r["quantity"]) - int(r["received_quantity"])
                if rem > 0:
                    incoming_quantity += rem
                    incoming_orders.append({"expected_date": str(r["expected_date"]), "quantity": rem})

    # 4. Fetch Sales Demand Stats
    sales_qtys = []
    if db:
        try:
            sales = db.query(Sale).filter(Sale.product_id == product_id).all()
            sales_qtys = [s.quantity for s in sales]
        except Exception:
            sales_qtys = []

    if not sales_qtys:
        raw_sales = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "sales.csv")
        if os.path.exists(raw_sales):
            s_df = pd.read_csv(raw_sales)
            m_sales = s_df[s_df["product_id"] == product_id]
            sales_qtys = m_sales["quantity"].tolist()

    avg_demand, std_demand = calculate_demand_stats(sales_qtys)

    # 5. Fetch Supplier Performance & Lead Time Stats
    perf_dicts = []
    if db:
        try:
            perfs = db.query(SupplierPerformance).filter(SupplierPerformance.supplier_id == supplier_id).all()
            perf_dicts = [{"actual_lead_time": p.actual_lead_time} for p in perfs]
        except Exception:
            perf_dicts = []

    if not perf_dicts:
        raw_perf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "raw", "supplier_performance.csv")
        if os.path.exists(raw_perf):
            perf_df = pd.read_csv(raw_perf)
            m_perf = perf_df[perf_df["supplier_id"] == supplier_id]
            perf_dicts = m_perf.to_dict("records")

    avg_lt, std_lt = calculate_lead_time_stats(perf_dicts, default_lead_time=float(lead_time_days))

    # 6. Safety Stock & Reorder Point Calculations
    safety_stock = calculate_safety_stock(avg_demand, std_demand, avg_lt, std_lt)
    
    # Consume Phase 3 Forecast Service for Lead Time Horizon Demand
    forecast_horizon_days = max(7, math.ceil(avg_lt))
    try:
        fc_res = forecast_product(product_id=product_id, horizon_days=forecast_horizon_days, db=db)
        forecast_items = fc_res["forecast"]
        forecast_demand_lead_time = fc_res["total_predicted_demand"]
    except Exception as e:
        warnings.append(f"Forecast service fallback used: {e}")
        forecast_demand_lead_time = round(avg_demand * forecast_horizon_days, 2)
        forecast_items = []

    reorder_point = calculate_reorder_point(forecast_demand_lead_time, safety_stock)
    inv_pos = calculate_inventory_position(current_stock, incoming_quantity, reserved_stock)
    days_inv = calculate_days_of_inventory(current_stock, avg_demand)

    # 7. Inventory Stockout Projection
    has_stockout, stockout_date, min_proj_stock, _ = project_inventory_timeline(current_stock, incoming_orders, forecast_items)

    # 8. Risk Score & Level
    risk_score, risk_level = calculate_risk_score(
        inventory_position=inv_pos,
        reorder_point=reorder_point,
        safety_stock=safety_stock,
        has_stockout=has_stockout,
        days_of_inventory=days_inv,
        lead_time_days=int(avg_lt)
    )

    reasons = generate_deterministic_reasons(
        inventory_position=inv_pos,
        reorder_point=reorder_point,
        safety_stock=safety_stock,
        days_of_inventory=days_inv,
        lead_time_days=int(avg_lt),
        has_stockout=has_stockout,
        stockout_date=stockout_date
    )

    # 9. Recommendation & MOQ Rounding
    rec_action = classify_recommendation_action(risk_level, has_stockout, inv_pos, reorder_point)
    target_inventory = reorder_point + safety_stock
    rec_order_qty = calculate_recommended_reorder_quantity(target_inventory, inv_pos, moq)

    return {
        "product_id": product_id,
        "sku": sku,
        "product_name": prod_name,
        "category": category,
        "warehouse_id": target_wh_id,
        "warehouse_code": wh_code,
        "current_stock": current_stock,
        "reserved_stock": reserved_stock,
        "incoming_quantity": incoming_quantity,
        "inventory_position": inv_pos,
        "average_daily_demand": avg_demand,
        "forecast_demand_lead_time": forecast_demand_lead_time,
        "lead_time_days": int(avg_lt),
        "lead_time_std": std_lt,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "days_of_inventory": days_inv,
        "projected_stockout": has_stockout,
        "projected_stockout_date": stockout_date,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_action": rec_action,
        "recommended_order_quantity": rec_order_qty,
        "reasons": reasons,
        "warnings": warnings
    }
