from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Text, 
    ForeignKey, UniqueConstraint, CheckConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(100), nullable=False)
    reliability_score = Column(Float, nullable=False)
    average_lead_time_days = Column(Float, nullable=False)
    contract_status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("reliability_score >= 0 AND reliability_score <= 100", name="chk_reliability_score"),
        CheckConstraint("average_lead_time_days > 0", name="chk_average_lead_time"),
    )

    # Relationships
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    performances = relationship("SupplierPerformance", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    unit_cost = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    lead_time_days = Column(Integer, nullable=False, default=7)
    minimum_order_quantity = Column(Integer, nullable=False, default=50)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("unit_cost > 0", name="chk_unit_cost"),
        CheckConstraint("selling_price > 0", name="chk_selling_price"),
        CheckConstraint("lead_time_days >= 0", name="chk_lead_time_days"),
        CheckConstraint("minimum_order_quantity > 0", name="chk_minimum_order_quantity"),
    )

    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    inventories = relationship("Inventory", back_populates="product")
    sales = relationship("Sale", back_populates="product")
    purchase_orders = relationship("PurchaseOrder", back_populates="product")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("capacity > 0", name="chk_warehouse_capacity"),
    )

    # Relationships
    inventories = relationship("Inventory", back_populates="warehouse")
    sales = relationship("Sale", back_populates="warehouse")
    purchase_orders = relationship("PurchaseOrder", back_populates="warehouse")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    current_stock = Column(Integer, nullable=False, default=0)
    reserved_stock = Column(Integer, nullable=False, default=0)
    safety_stock = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_product_warehouse"),
        CheckConstraint("current_stock >= 0", name="chk_current_stock"),
        CheckConstraint("reserved_stock >= 0", name="chk_reserved_stock"),
        CheckConstraint("safety_stock >= 0", name="chk_safety_stock"),
        CheckConstraint("reorder_point >= 0", name="chk_reorder_point"),
    )

    # Relationships
    product = relationship("Product", back_populates="inventories")
    warehouse = relationship("Warehouse", back_populates="inventories")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="chk_sale_quantity"),
        CheckConstraint("revenue >= 0", name="chk_sale_revenue"),
        Index("idx_sales_product_date", "product_id", "sale_date"),
    )

    # Relationships
    product = relationship("Product", back_populates="sales")
    warehouse = relationship("Warehouse", back_populates="sales")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=False, index=True)
    actual_delivery_date = Column(Date, nullable=True)
    quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="PENDING", index=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_po_quantity"),
        CheckConstraint("received_quantity >= 0", name="chk_po_received_quantity"),
    )

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    product = relationship("Product", back_populates="purchase_orders")
    warehouse = relationship("Warehouse", back_populates="purchase_orders")


class SupplierPerformance(Base):
    __tablename__ = "supplier_performance"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    promised_lead_time = Column(Integer, nullable=False)
    actual_lead_time = Column(Integer, nullable=False)
    delay_days = Column(Integer, nullable=False, default=0)
    quality_score = Column(Float, nullable=False, default=100.0)
    on_time = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("quality_score >= 0 AND quality_score <= 100", name="chk_perf_quality_score"),
        Index("idx_perf_supplier_date", "supplier_id", "date"),
    )

    # Relationships
    supplier = relationship("Supplier", back_populates="performances")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(255), nullable=False, index=True)
    document_type = Column(String(100), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column("metadata", JSONB().with_variant(JSON(), "sqlite"), nullable=True)
    embedding = Column(Vector(384).with_variant(JSON(), "sqlite"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
