from sqlalchemy.orm import Session
from sqlalchemy import func, select
from typing import List, Optional, Dict, Any

from app.database.models import (
    Supplier, Product, Warehouse, Inventory, Sale, PurchaseOrder, SupplierPerformance
)


def get_product_inventory(db: Session, product_id: Optional[int] = None, sku: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve inventory status along with product and warehouse details.
    """
    query = db.query(
        Inventory.id,
        Product.id.label("product_id"),
        Product.sku,
        Product.name.label("product_name"),
        Warehouse.id.label("warehouse_id"),
        Warehouse.name.label("warehouse_name"),
        Inventory.current_stock,
        Inventory.reserved_stock,
        Inventory.safety_stock,
        Inventory.reorder_point
    ).join(Product, Inventory.product_id == Product.id)\
     .join(Warehouse, Inventory.warehouse_id == Warehouse.id)

    if product_id:
        query = query.filter(Product.id == product_id)
    if sku:
        query = query.filter(Product.sku == sku)

    results = query.all()
    return [
        {
            "id": r.id,
            "product_id": r.product_id,
            "sku": r.sku,
            "product_name": r.product_name,
            "warehouse_id": r.warehouse_id,
            "warehouse_name": r.warehouse_name,
            "current_stock": r.current_stock,
            "reserved_stock": r.reserved_stock,
            "safety_stock": r.safety_stock,
            "reorder_point": r.reorder_point,
            "available_stock": r.current_stock - r.reserved_stock
        }
        for r in results
    ]


def get_supplier_performance(db: Session, supplier_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieve supplier performance historical metrics.
    """
    query = db.query(
        SupplierPerformance.id,
        Supplier.id.label("supplier_id"),
        Supplier.supplier_code,
        Supplier.name.label("supplier_name"),
        SupplierPerformance.date,
        SupplierPerformance.promised_lead_time,
        SupplierPerformance.actual_lead_time,
        SupplierPerformance.delay_days,
        SupplierPerformance.quality_score,
        SupplierPerformance.on_time
    ).join(Supplier, SupplierPerformance.supplier_id == Supplier.id)

    if supplier_id:
        query = query.filter(Supplier.id == supplier_id)

    results = query.order_by(SupplierPerformance.date.desc()).all()
    return [
        {
            "id": r.id,
            "supplier_id": r.supplier_id,
            "supplier_code": r.supplier_code,
            "supplier_name": r.supplier_name,
            "date": str(r.date),
            "promised_lead_time": r.promised_lead_time,
            "actual_lead_time": r.actual_lead_time,
            "delay_days": r.delay_days,
            "quality_score": r.quality_score,
            "on_time": r.on_time
        }
        for r in results
    ]


def get_delayed_purchase_orders(db: Session) -> List[Dict[str, Any]]:
    """
    Retrieve active purchase orders that are classified as DELAYED or are past expected date.
    """
    query = db.query(
        PurchaseOrder.id,
        PurchaseOrder.po_number,
        Supplier.name.label("supplier_name"),
        Product.sku,
        Product.name.label("product_name"),
        Warehouse.name.label("warehouse_name"),
        PurchaseOrder.order_date,
        PurchaseOrder.expected_date,
        PurchaseOrder.quantity,
        PurchaseOrder.received_quantity,
        PurchaseOrder.status
    ).join(Supplier, PurchaseOrder.supplier_id == Supplier.id)\
     .join(Product, PurchaseOrder.product_id == Product.id)\
     .join(Warehouse, PurchaseOrder.warehouse_id == Warehouse.id)\
     .filter(PurchaseOrder.status.in_(["DELAYED", "IN_TRANSIT", "PENDING"]))

    results = query.order_by(PurchaseOrder.expected_date.asc()).all()
    return [
        {
            "id": r.id,
            "po_number": r.po_number,
            "supplier_name": r.supplier_name,
            "sku": r.sku,
            "product_name": r.product_name,
            "warehouse_name": r.warehouse_name,
            "order_date": str(r.order_date),
            "expected_date": str(r.expected_date),
            "quantity": r.quantity,
            "received_quantity": r.received_quantity,
            "status": r.status
        }
        for r in results
    ]


def get_sales_history(db: Session, product_id: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Retrieve historical sales records for forecasting model.
    """
    query = db.query(
        Sale.id,
        Product.sku,
        Product.name.label("product_name"),
        Sale.warehouse_id,
        Sale.sale_date,
        Sale.quantity,
        Sale.revenue
    ).join(Product, Sale.product_id == Product.id)

    if product_id:
        query = query.filter(Sale.product_id == product_id)

    results = query.order_by(Sale.sale_date.asc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "sku": r.sku,
            "product_name": r.product_name,
            "warehouse_id": r.warehouse_id,
            "sale_date": str(r.sale_date),
            "quantity": r.quantity,
            "revenue": r.revenue
        }
        for r in results
    ]


def get_products_by_supplier(db: Session, supplier_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all products supplied by a specific supplier.
    """
    products = db.query(Product).filter(Product.supplier_id == supplier_id).all()
    return [
        {
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "unit_cost": p.unit_cost,
            "selling_price": p.selling_price,
            "lead_time_days": p.lead_time_days,
            "minimum_order_quantity": p.minimum_order_quantity
        }
        for p in products
    ]


def get_inventory_risk_candidates(db: Session) -> List[Dict[str, Any]]:
    """
    Identify products where current stock is at or below the reorder point.
    """
    results = db.query(
        Inventory.id,
        Product.sku,
        Product.name.label("product_name"),
        Product.lead_time_days,
        Supplier.name.label("supplier_name"),
        Inventory.current_stock,
        Inventory.safety_stock,
        Inventory.reorder_point
    ).join(Product, Inventory.product_id == Product.id)\
     .join(Supplier, Product.supplier_id == Supplier.id)\
     .filter(Inventory.current_stock <= Inventory.reorder_point)\
     .all()

    return [
        {
            "id": r.id,
            "sku": r.sku,
            "product_name": r.product_name,
            "supplier_name": r.supplier_name,
            "lead_time_days": r.lead_time_days,
            "current_stock": r.current_stock,
            "safety_stock": r.safety_stock,
            "reorder_point": r.reorder_point,
            "shortage": max(0, r.reorder_point - r.current_stock)
        }
        for r in results
    ]
