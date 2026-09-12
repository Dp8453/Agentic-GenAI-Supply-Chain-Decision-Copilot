import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path for test discovery
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    try:
        from app.database.base import Base
        from app.database.models import Supplier, Product, Warehouse, Inventory, Sale, PurchaseOrder
        engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        session = TestingSessionLocal()
        
        # Seed test fixtures for SQL / Evaluation execution
        sup = Supplier(id=1, supplier_code="SUP-001", name="Acme Supply", location="Chicago", reliability_score=95.0, average_lead_time_days=5.0)
        prod1 = Product(id=1, sku="SKU-101", name="Component A", category="Electronics", unit_cost=25.0, selling_price=50.0, lead_time_days=10, supplier_id=1)
        prod2 = Product(id=2, sku="SKU-102", name="Component B", category="Electronics", unit_cost=50.0, selling_price=100.0, lead_time_days=5, supplier_id=1)
        wh = Warehouse(id=1, warehouse_code="WH-01", name="Main Warehouse", location="Chicago", capacity=50000)
        inv1 = Inventory(id=1, product_id=1, warehouse_id=1, current_stock=100, reserved_stock=0, safety_stock=50, reorder_point=500)
        inv2 = Inventory(id=2, product_id=2, warehouse_id=1, current_stock=500, reserved_stock=0, safety_stock=15, reorder_point=115)
        
        session.add_all([sup, prod1, prod2, wh, inv1, inv2])
        session.commit()

        yield session
        session.close()
        Base.metadata.drop_all(bind=engine)
    except Exception:
        yield None
