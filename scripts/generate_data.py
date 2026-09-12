import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Reproducible seed
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
os.makedirs(DATA_RAW_DIR, exist_ok=True)


def generate_suppliers():
    suppliers = []
    # 15 Suppliers categorized into 3 reliability profiles
    profiles = [
        ("Reliable", 90, 98, 3, 7, "ACTIVE"),
        ("Average", 70, 89, 7, 14, "ACTIVE"),
        ("Risky", 40, 69, 14, 25, "UNDER_REVIEW")
    ]

    locations = ["Chicago, IL", "Dallas, TX", "Seattle, WA", "Atlanta, GA", "Columbus, OH", "Hamburg, DE", "Shenzhen, CN"]
    
    count = 1
    for profile_name, min_rel, max_rel, min_lt, max_lt, status in profiles:
        num_in_tier = 5
        for i in range(num_in_tier):
            supplier_code = f"SUP-{count:03d}"
            name = f"{profile_name} Supply Co #{i+1}"
            location = random.choice(locations)
            reliability_score = round(random.uniform(min_rel, max_rel), 2)
            average_lead_time_days = float(random.randint(min_lt, max_lt))
            contract_status = status if profile_name != "Risky" else random.choice(["ACTIVE", "UNDER_REVIEW"])
            
            suppliers.append({
                "id": count,
                "supplier_code": supplier_code,
                "name": name,
                "location": location,
                "reliability_score": reliability_score,
                "average_lead_time_days": average_lead_time_days,
                "contract_status": contract_status,
                "created_at": "2024-01-01 00:00:00"
            })
            count += 1

    df = pd.DataFrame(suppliers)
    df.to_csv(os.path.join(DATA_RAW_DIR, "suppliers.csv"), index=False)
    print(f"Generated {len(df)} suppliers -> data/raw/suppliers.csv")
    return df


def generate_warehouses():
    warehouses = [
        {"id": 1, "warehouse_code": "WH-EAST", "name": "East Coast Distribution Hub", "location": "Newark, NJ", "capacity": 500000, "created_at": "2024-01-01 00:00:00"},
        {"id": 2, "warehouse_code": "WH-WEST", "name": "Pacific Logistics Depot", "location": "Ontario, CA", "capacity": 750000, "created_at": "2024-01-01 00:00:00"},
        {"id": 3, "warehouse_code": "WH-MIDWEST", "name": "Central Freight Center", "location": "Indianapolis, IN", "capacity": 600000, "created_at": "2024-01-01 00:00:00"},
        {"id": 4, "warehouse_code": "WH-SOUTH", "name": "Gulf Logistics Facility", "location": "Memphis, TN", "capacity": 450000, "created_at": "2024-01-01 00:00:00"},
    ]
    df = pd.DataFrame(warehouses)
    df.to_csv(os.path.join(DATA_RAW_DIR, "warehouses.csv"), index=False)
    print(f"Generated {len(df)} warehouses -> data/raw/warehouses.csv")
    return df


def generate_products(suppliers_df):
    categories = {
        "Electronics": (40.0, 150.0, 10, 21),
        "Industrial Components": (15.0, 75.0, 7, 14),
        "Raw Materials": (5.0, 25.0, 5, 10),
        "Packaging": (1.5, 8.0, 3, 7),
        "Consumer Goods": (12.0, 45.0, 5, 12),
    }

    products = []
    prod_id = 1
    supplier_ids = suppliers_df["id"].tolist()

    for category, (min_cost, max_cost, min_lt, max_lt) in categories.items():
        num_products = 16  # Total 80 products
        for i in range(num_products):
            sku = f"SKU-{prod_id:03d}"
            name = f"{category[:-1] if category.endswith('s') else category} Item #{i+1}"
            unit_cost = round(random.uniform(min_cost, max_cost), 2)
            margin = random.uniform(1.3, 1.8)
            selling_price = round(unit_cost * margin, 2)
            lead_time_days = random.randint(min_lt, max_lt)
            minimum_order_quantity = random.choice([50, 100, 200, 500])
            supplier_id = random.choice(supplier_ids)

            products.append({
                "id": prod_id,
                "sku": sku,
                "name": name,
                "category": category,
                "unit_cost": unit_cost,
                "selling_price": selling_price,
                "lead_time_days": lead_time_days,
                "minimum_order_quantity": minimum_order_quantity,
                "supplier_id": supplier_id,
                "created_at": "2024-01-01 00:00:00"
            })
            prod_id += 1

    df = pd.DataFrame(products)
    df.to_csv(os.path.join(DATA_RAW_DIR, "products.csv"), index=False)
    print(f"Generated {len(df)} products -> data/raw/products.csv")
    return df


def generate_inventory(products_df, warehouses_df):
    inventory_records = []
    inv_id = 1

    for _, product in products_df.iterrows():
        prod_id = int(product["id"])
        lead_time = int(product["lead_time_days"])

        for _, wh in warehouses_df.iterrows():
            wh_id = int(wh["id"])

            # Classify inventory risk profile (Healthy, Low Stock, Critical High Risk)
            risk_tier = random.choices(["HEALTHY", "LOW_STOCK", "CRITICAL"], weights=[0.65, 0.20, 0.15])[0]

            daily_demand = random.randint(15, 60)
            safety_stock = int(daily_demand * lead_time * 0.5)
            reorder_point = int(daily_demand * lead_time + safety_stock)

            if risk_tier == "HEALTHY":
                current_stock = random.randint(reorder_point + 100, reorder_point + 1000)
            elif risk_tier == "LOW_STOCK":
                current_stock = random.randint(safety_stock, reorder_point)
            else:  # CRITICAL
                current_stock = random.randint(5, max(10, safety_stock - 10))

            reserved_stock = random.randint(0, min(20, current_stock))

            inventory_records.append({
                "id": inv_id,
                "product_id": prod_id,
                "warehouse_id": wh_id,
                "current_stock": current_stock,
                "reserved_stock": reserved_stock,
                "safety_stock": safety_stock,
                "reorder_point": reorder_point,
                "updated_at": "2025-09-01 00:00:00"
            })
            inv_id += 1

    df = pd.DataFrame(inventory_records)
    df.to_csv(os.path.join(DATA_RAW_DIR, "inventory.csv"), index=False)
    print(f"Generated {len(df)} inventory records -> data/raw/inventory.csv")
    return df


def generate_sales(products_df, warehouses_df):
    sales_records = []
    sale_id = 1

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 30)  # 18 months of history
    delta_days = (end_date - start_date).days

    warehouses = warehouses_df["id"].tolist()

    # Pre-assign base demand multiplier per product
    product_multipliers = {int(p["id"]): random.uniform(0.5, 2.5) for _, p in products_df.iterrows()}
    product_prices = {int(p["id"]): float(p["selling_price"]) for _, p in products_df.iterrows()}

    for day_offset in range(0, delta_days, 2):  # Bi-daily sales records per product/warehouse
        current_date = start_date + timedelta(days=day_offset)
        month = current_date.month
        weekday = current_date.weekday()

        # Seasonality factor (Q4 holiday surge in Nov/Dec)
        seasonality = 1.4 if month in [11, 12] else (1.15 if month in [6, 7] else 1.0)
        # Day of week factor (lower sales on weekends)
        day_factor = 0.6 if weekday in [5, 6] else 1.1

        for _, prod in products_df.iterrows():
            prod_id = int(prod["id"])
            price = product_prices[prod_id]
            base_mult = product_multipliers[prod_id]

            # Sample 2 active warehouses per date
            active_whs = random.sample(warehouses, k=2)
            for wh_id in active_whs:
                noise = random.uniform(0.8, 1.2)
                raw_qty = int(20 * base_mult * seasonality * day_factor * noise)
                qty = max(1, raw_qty)
                revenue = round(qty * price, 2)

                sales_records.append({
                    "id": sale_id,
                    "product_id": prod_id,
                    "warehouse_id": wh_id,
                    "sale_date": current_date.strftime("%Y-%m-%d"),
                    "quantity": qty,
                    "revenue": revenue
                })
                sale_id += 1

    df = pd.DataFrame(sales_records)
    df.to_csv(os.path.join(DATA_RAW_DIR, "sales.csv"), index=False)
    print(f"Generated {len(df)} sales records -> data/raw/sales.csv")
    return df


def generate_purchase_orders(suppliers_df, products_df, warehouses_df):
    po_records = []
    po_id = 1

    suppliers = suppliers_df.to_dict("records")
    supp_dict = {s["id"]: s for s in suppliers}
    products = products_df.to_dict("records")
    warehouses = warehouses_df["id"].tolist()

    start_date = datetime(2024, 6, 1)

    for i in range(1200):
        po_number = f"PO-{2024000 + po_id}"
        product = random.choice(products)
        prod_id = product["id"]
        supp_id = product["supplier_id"]
        supplier = supp_dict[supp_id]
        wh_id = random.choice(warehouses)

        days_offset = random.randint(0, 450)
        order_dt = start_date + timedelta(days=days_offset)
        promised_lead_time = int(supplier["average_lead_time_days"])
        expected_dt = order_dt + timedelta(days=promised_lead_time)

        # Reliability probability check
        reliability = supplier["reliability_score"]
        is_delayed = random.uniform(0, 100) > reliability

        qty = product["minimum_order_quantity"] * random.choice([1, 2, 3])

        # Status assignment based on timeline
        today = datetime(2025, 7, 1)
        if expected_dt > today:
            status = "DELAYED" if is_delayed else random.choice(["PENDING", "IN_TRANSIT"])
            actual_dt = None
            received_qty = 0
        else:
            status = "DELAYED" if is_delayed else "DELIVERED"
            delay_days = random.randint(3, 14) if is_delayed else 0
            actual_dt = expected_dt + timedelta(days=delay_days)
            received_qty = qty if status == "DELIVERED" else random.choice([0, qty // 2])

        po_records.append({
            "id": po_id,
            "po_number": po_number,
            "supplier_id": supp_id,
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "order_date": order_dt.strftime("%Y-%m-%d"),
            "expected_date": expected_dt.strftime("%Y-%m-%d"),
            "actual_delivery_date": actual_dt.strftime("%Y-%m-%d") if actual_dt else None,
            "quantity": qty,
            "received_quantity": received_qty,
            "status": status
        })
        po_id += 1

    df = pd.DataFrame(po_records)
    df.to_csv(os.path.join(DATA_RAW_DIR, "purchase_orders.csv"), index=False)
    print(f"Generated {len(df)} purchase orders -> data/raw/purchase_orders.csv")
    return df


def generate_supplier_performance(suppliers_df):
    perf_records = []
    perf_id = 1
    start_date = datetime(2024, 1, 1)

    for _, supplier in suppliers_df.iterrows():
        supp_id = int(supplier["id"])
        promised = int(supplier["average_lead_time_days"])
        reliability = float(supplier["reliability_score"])

        for month in range(18):
            eval_date = start_date + timedelta(days=month * 30)
            is_on_time = random.uniform(0, 100) <= reliability
            delay_days = 0 if is_on_time else random.randint(2, 12)
            actual_lead_time = promised + delay_days
            quality_score = round(random.uniform(85, 100) if is_on_time else random.uniform(60, 84), 2)

            perf_records.append({
                "id": perf_id,
                "supplier_id": supp_id,
                "date": eval_date.strftime("%Y-%m-%d"),
                "promised_lead_time": promised,
                "actual_lead_time": actual_lead_time,
                "delay_days": delay_days,
                "quality_score": quality_score,
                "on_time": is_on_time
            })
            perf_id += 1

    df = pd.DataFrame(perf_records)
    df.to_csv(os.path.join(DATA_RAW_DIR, "supplier_performance.csv"), index=False)
    print(f"Generated {len(df)} supplier performance records -> data/raw/supplier_performance.csv")
    return df


def main():
    print(f"--- Generating Synthetic Supply Chain Dataset (Seed = {SEED}) ---")
    suppliers_df = generate_suppliers()
    warehouses_df = generate_warehouses()
    products_df = generate_products(suppliers_df)
    generate_inventory(products_df, warehouses_df)
    generate_sales(products_df, warehouses_df)
    generate_purchase_orders(suppliers_df, products_df, warehouses_df)
    generate_supplier_performance(suppliers_df)
    print("--- Synthetic Data Generation Complete! ---")


if __name__ == "__main__":
    main()
