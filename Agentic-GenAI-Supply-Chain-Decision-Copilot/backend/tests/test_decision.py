import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.decision.inventory import (
    calculate_inventory_position, calculate_demand_stats, calculate_lead_time_stats,
    calculate_safety_stock, calculate_reorder_point, calculate_days_of_inventory
)
from app.decision.risk import project_inventory_timeline, calculate_risk_score, generate_deterministic_reasons
from app.decision.recommendations import classify_recommendation_action, calculate_recommended_reorder_quantity
from app.decision.service import evaluate_product_inventory_risk

client = TestClient(app)


def test_inventory_position_and_days_of_inventory():
    pos = calculate_inventory_position(current_stock=100, incoming_quantity=50, reserved_stock=20)
    assert pos == 130

    days = calculate_days_of_inventory(current_stock=100, avg_daily_demand=10.0)
    assert days == 10.0

    days_zero = calculate_days_of_inventory(current_stock=100, avg_daily_demand=0.0)
    assert days_zero is None


def test_safety_stock_and_reorder_point():
    ss = calculate_safety_stock(avg_demand=20.0, std_demand=5.0, avg_lead_time=7.0, std_lead_time=1.5)
    assert ss > 0

    rop = calculate_reorder_point(expected_demand_during_lead_time=140.0, safety_stock=ss)
    assert rop > 140.0


def test_moq_rounding_logic():
    # Deficit = 0 -> 0
    qty1 = calculate_recommended_reorder_quantity(target_inventory=100, inventory_position=120, minimum_order_quantity=50)
    assert qty1 == 0

    # Deficit = 30 <= MOQ 50 -> 50
    qty2 = calculate_recommended_reorder_quantity(target_inventory=100, inventory_position=70, minimum_order_quantity=50)
    assert qty2 == 50

    # Deficit = 75 > MOQ 50 -> 100
    qty3 = calculate_recommended_reorder_quantity(target_inventory=150, inventory_position=75, minimum_order_quantity=50)
    assert qty3 == 100


def test_stockout_timeline_projection():
    forecast_items = [
        {"date": "2025-07-01", "predicted_demand": 20.0},
        {"date": "2025-07-02", "predicted_demand": 20.0},
        {"date": "2025-07-03", "predicted_demand": 20.0},
    ]
    incoming_orders = [{"expected_date": "2025-07-02", "quantity": 10}]

    has_stockout, stockout_date, min_stock, timeline = project_inventory_timeline(
        current_stock=30, incoming_orders=incoming_orders, forecast_items=forecast_items
    )
    # Day 1: 30 - 20 = 10
    # Day 2: 10 + 10 - 20 = 0 -> Stockout on Day 2!
    assert has_stockout is True
    assert stockout_date == "2025-07-02"


def test_risk_scoring_and_level_mapping():
    score_critical, level_critical = calculate_risk_score(
        inventory_position=10, reorder_point=50, safety_stock=20, has_stockout=True, days_of_inventory=2.0, lead_time_days=7
    )
    assert score_critical >= 75
    assert level_critical == "CRITICAL"

    score_low, level_low = calculate_risk_score(
        inventory_position=200, reorder_point=50, safety_stock=20, has_stockout=False, days_of_inventory=20.0, lead_time_days=7
    )
    assert score_low < 25
    assert level_low == "LOW"


def test_service_evaluate_product_risk():
    res = evaluate_product_inventory_risk(product_id=1)
    assert res["product_id"] == 1
    assert "sku" in res
    assert "risk_score" in res
    assert "risk_level" in res
    assert "recommended_action" in res
    assert "reasons" in res


def test_risk_and_recommendation_api_endpoints():
    r1 = client.get("/api/v1/risk")
    assert r1.status_code == 200
    data1 = r1.json()
    assert "total_count" in data1
    assert "items" in data1

    r2 = client.get("/api/v1/risk/1")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["product_id"] == 1

    r3 = client.get("/api/v1/recommendations")
    assert r3.status_code == 200
    data3 = r3.json()
    assert "total_recommendations" in data3
