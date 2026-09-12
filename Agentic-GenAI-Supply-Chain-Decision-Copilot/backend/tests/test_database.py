import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.database.models import (
    Supplier, Product, Warehouse, Inventory, Sale, PurchaseOrder, SupplierPerformance
)
from app.database.repository import (
    get_product_inventory, get_supplier_performance, get_delayed_purchase_orders,
    get_sales_history, get_products_by_supplier, get_inventory_risk_candidates
)
import datetime

# Create in-memory SQLite engine for isolated unit testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # SQLite does not have pgvector type natively, so mock Vector compile if needed or clear tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_supplier_and_product_models(db):
    supplier = Supplier(
        id=1,
        supplier_code="SUP-001",
        name="Reliable Corp",
        location="Chicago, IL",
        reliability_score=95.5,
        average_lead_time_days=5.0,
        contract_status="ACTIVE"
    )
    db.add(supplier)
    db.commit()

    product = Product(
        id=1,
        sku="SKU-001",
        name="Microcontroller Unit",
        category="Electronics",
        unit_cost=25.0,
        selling_price=45.0,
        lead_time_days=7,
        minimum_order_quantity=100,
        supplier_id=1
    )
    db.add(product)
    db.commit()

    fetched_product = db.query(Product).filter(Product.sku == "SKU-001").first()
    assert fetched_product is not None
    assert fetched_product.name == "Microcontroller Unit"
    assert fetched_product.supplier.name == "Reliable Corp"


def test_repository_helpers(db):
    supplier = Supplier(id=1, supplier_code="SUP-001", name="Alpha Supplies", location="NY", reliability_score=90.0, average_lead_time_days=7.0)
    product = Product(id=1, sku="SKU-102", name="Sensor Module", category="Electronics", unit_cost=10.0, selling_price=20.0, lead_time_days=5, minimum_order_quantity=50, supplier_id=1)
    warehouse = Warehouse(id=1, warehouse_code="WH-01", name="Main Warehouse", location="NJ", capacity=100000)
    inventory = Inventory(id=1, product_id=1, warehouse_id=1, current_stock=20, reserved_stock=5, safety_stock=30, reorder_point=50)

    db.add_all([supplier, product, warehouse, inventory])
    db.commit()

    # Test inventory risk candidates helper
    risk_candidates = get_inventory_risk_candidates(db)
    assert len(risk_candidates) == 1
    assert risk_candidates[0]["sku"] == "SKU-102"
    assert risk_candidates[0]["shortage"] == 30  # reorder_point 50 - current_stock 20 = 30

    # Test products by supplier helper
    products = get_products_by_supplier(db, supplier_id=1)
    assert len(products) == 1
    assert products[0]["sku"] == "SKU-102"
