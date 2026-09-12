import os
import pandas as pd

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")


def validate_dataset():
    print("--- Running Synthetic Data Quality & Validation Engine ---")

    suppliers = pd.read_csv(os.path.join(DATA_RAW_DIR, "suppliers.csv"))
    warehouses = pd.read_csv(os.path.join(DATA_RAW_DIR, "warehouses.csv"))
    products = pd.read_csv(os.path.join(DATA_RAW_DIR, "products.csv"))
    inventory = pd.read_csv(os.path.join(DATA_RAW_DIR, "inventory.csv"))
    sales = pd.read_csv(os.path.join(DATA_RAW_DIR, "sales.csv"))
    pos = pd.read_csv(os.path.join(DATA_RAW_DIR, "purchase_orders.csv"))
    perf = pd.read_csv(os.path.join(DATA_RAW_DIR, "supplier_performance.csv"))

    errors = []

    # 1. Uniqueness Checks
    if len(suppliers["supplier_code"].unique()) != len(suppliers):
        errors.append("Duplicate supplier_code detected in suppliers.csv")
    if len(products["sku"].unique()) != len(products):
        errors.append("Duplicate SKU detected in products.csv")
    if len(warehouses["warehouse_code"].unique()) != len(warehouses):
        errors.append("Duplicate warehouse_code detected in warehouses.csv")
    if len(pos["po_number"].unique()) != len(pos):
        errors.append("Duplicate po_number detected in purchase_orders.csv")

    # 2. Foreign Key Integrity Checks
    supplier_ids = set(suppliers["id"])
    product_ids = set(products["id"])
    warehouse_ids = set(warehouses["id"])

    invalid_prod_supp = set(products["supplier_id"]) - supplier_ids
    if invalid_prod_supp:
        errors.append(f"Products reference non-existent supplier_id: {invalid_prod_supp}")

    invalid_inv_prod = set(inventory["product_id"]) - product_ids
    if invalid_inv_prod:
        errors.append(f"Inventory references non-existent product_id: {invalid_inv_prod}")

    invalid_inv_wh = set(inventory["warehouse_id"]) - warehouse_ids
    if invalid_inv_wh:
        errors.append(f"Inventory references non-existent warehouse_id: {invalid_inv_wh}")

    invalid_sales_prod = set(sales["product_id"]) - product_ids
    if invalid_sales_prod:
        errors.append(f"Sales reference non-existent product_id: {invalid_sales_prod}")

    invalid_po_supp = set(pos["supplier_id"]) - supplier_ids
    if invalid_po_supp:
        errors.append(f"Purchase orders reference non-existent supplier_id: {invalid_po_supp}")

    # 3. Numeric & Constraint Sanity Checks
    if (products["unit_cost"] <= 0).any():
        errors.append("Products with unit_cost <= 0 found")
    if (products["selling_price"] <= 0).any():
        errors.append("Products with selling_price <= 0 found")
    if (inventory["current_stock"] < 0).any():
        errors.append("Inventory with negative current_stock found")
    if (sales["quantity"] <= 0).any():
        errors.append("Sales with quantity <= 0 found")
    if (pos["quantity"] <= 0).any():
        errors.append("Purchase orders with quantity <= 0 found")

    if errors:
        print("[FAIL] Data Validation Failed with Errors:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("[SUCCESS] Data Validation Passed Successfully!")
        print(f"  - Suppliers Verified: {len(suppliers)}")
        print(f"  - Warehouses Verified: {len(warehouses)}")
        print(f"  - Products Verified: {len(products)}")
        print(f"  - Inventory Records Verified: {len(inventory)}")
        print(f"  - Sales Records Verified: {len(sales)}")
        print(f"  - Purchase Orders Verified: {len(pos)}")
        print(f"  - Supplier Performance Records Verified: {len(perf)}")
        return True


if __name__ == "__main__":
    success = validate_dataset()
    if not success:
        exit(1)
