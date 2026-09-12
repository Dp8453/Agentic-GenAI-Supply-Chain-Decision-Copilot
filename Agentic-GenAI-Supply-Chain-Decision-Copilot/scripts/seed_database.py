import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# Add backend to path for imports
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.connection import engine, SessionLocal
from app.database.base import Base
from app.database.models import (
    Supplier, Product, Warehouse, Inventory, Sale, PurchaseOrder, SupplierPerformance, DocumentChunk
)

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")


def seed_database():
    print("--- Starting PostgreSQL Supply Chain Database Seeding ---")

    # 1. Check PostgreSQL connection & enable pgvector extension
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
    except OperationalError as oe:
        print("[WARNING] PostgreSQL database is currently unreachable on localhost:5432.")
        print("          To seed PostgreSQL, start the container using: docker-compose up -d")
        print(f"          Error details: {oe}")
        return False

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] Database schema & pgvector extension initialized.")

    db = SessionLocal()

    try:
        # 2. Seed Suppliers
        suppliers_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "suppliers.csv"))
        for _, row in suppliers_df.iterrows():
            db.add(Supplier(
                id=int(row["id"]),
                supplier_code=str(row["supplier_code"]),
                name=str(row["name"]),
                location=str(row["location"]),
                reliability_score=float(row["reliability_score"]),
                average_lead_time_days=float(row["average_lead_time_days"]),
                contract_status=str(row["contract_status"])
            ))
        db.commit()
        print(f"  - Seeded Suppliers: {len(suppliers_df)}")

        # 3. Seed Warehouses
        warehouses_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "warehouses.csv"))
        for _, row in warehouses_df.iterrows():
            db.add(Warehouse(
                id=int(row["id"]),
                warehouse_code=str(row["warehouse_code"]),
                name=str(row["name"]),
                location=str(row["location"]),
                capacity=int(row["capacity"])
            ))
        db.commit()
        print(f"  - Seeded Warehouses: {len(warehouses_df)}")

        # 4. Seed Products
        products_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "products.csv"))
        for _, row in products_df.iterrows():
            db.add(Product(
                id=int(row["id"]),
                sku=str(row["sku"]),
                name=str(row["name"]),
                category=str(row["category"]),
                unit_cost=float(row["unit_cost"]),
                selling_price=float(row["selling_price"]),
                lead_time_days=int(row["lead_time_days"]),
                minimum_order_quantity=int(row["minimum_order_quantity"]),
                supplier_id=int(row["supplier_id"])
            ))
        db.commit()
        print(f"  - Seeded Products: {len(products_df)}")

        # 5. Seed Inventory
        inventory_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "inventory.csv"))
        for _, row in inventory_df.iterrows():
            db.add(Inventory(
                id=int(row["id"]),
                product_id=int(row["product_id"]),
                warehouse_id=int(row["warehouse_id"]),
                current_stock=int(row["current_stock"]),
                reserved_stock=int(row["reserved_stock"]),
                safety_stock=int(row["safety_stock"]),
                reorder_point=int(row["reorder_point"])
            ))
        db.commit()
        print(f"  - Seeded Inventory: {len(inventory_df)}")

        # 6. Seed Sales
        sales_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "sales.csv"))
        sales_batch = []
        for _, row in sales_df.iterrows():
            sales_batch.append(Sale(
                id=int(row["id"]),
                product_id=int(row["product_id"]),
                warehouse_id=int(row["warehouse_id"]),
                sale_date=datetime.strptime(str(row["sale_date"]), "%Y-%m-%d").date(),
                quantity=int(row["quantity"]),
                revenue=float(row["revenue"])
            ))
            if len(sales_batch) >= 1000:
                db.bulk_save_objects(sales_batch)
                db.commit()
                sales_batch = []
        if sales_batch:
            db.bulk_save_objects(sales_batch)
            db.commit()
        print(f"  - Seeded Sales Records: {len(sales_df)}")

        # 7. Seed Purchase Orders
        po_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "purchase_orders.csv"))
        for _, row in po_df.iterrows():
            actual_dt = datetime.strptime(str(row["actual_delivery_date"]), "%Y-%m-%d").date() if pd.notna(row["actual_delivery_date"]) else None
            db.add(PurchaseOrder(
                id=int(row["id"]),
                po_number=str(row["po_number"]),
                supplier_id=int(row["supplier_id"]),
                product_id=int(row["product_id"]),
                warehouse_id=int(row["warehouse_id"]),
                order_date=datetime.strptime(str(row["order_date"]), "%Y-%m-%d").date(),
                expected_date=datetime.strptime(str(row["expected_date"]), "%Y-%m-%d").date(),
                actual_delivery_date=actual_dt,
                quantity=int(row["quantity"]),
                received_quantity=int(row["received_quantity"]),
                status=str(row["status"])
            ))
        db.commit()
        print(f"  - Seeded Purchase Orders: {len(po_df)}")

        # 8. Seed Supplier Performance
        perf_df = pd.read_csv(os.path.join(DATA_RAW_DIR, "supplier_performance.csv"))
        for _, row in perf_df.iterrows():
            db.add(SupplierPerformance(
                id=int(row["id"]),
                supplier_id=int(row["supplier_id"]),
                date=datetime.strptime(str(row["date"]), "%Y-%m-%d").date(),
                promised_lead_time=int(row["promised_lead_time"]),
                actual_lead_time=int(row["actual_lead_time"]),
                delay_days=int(row["delay_days"]),
                quality_score=float(row["quality_score"]),
                on_time=bool(row["on_time"])
            ))
        db.commit()
        print(f"  - Seeded Supplier Performance: {len(perf_df)}")

        print("[SUCCESS] Database Seeding Completed Successfully!")
        return True

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Database Seeding Failed with Error: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
