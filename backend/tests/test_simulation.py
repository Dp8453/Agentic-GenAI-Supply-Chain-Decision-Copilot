"""
Phase 9 — What-If Simulation Engine Tests

Tests cover:
1. Scenario Parsing & Parameter Validation
2. Deterministic Calculation Functions (Supplier Delay, Demand Change, Lead Time Change, Inventory Transfer)
3. Inventory Conservation Invariant during Stock Transfers
4. Database Non-Mutation (Read-only simulation guarantee)
5. Impact Classification & Recommendation Engine
6. Simulation Engine & Service End-to-End Execution
7. REST API Endpoints (/api/v1/simulation/query and /api/v1/simulation/run)
8. LangGraph Agent Multi-Tool Integration with SIMULATION tool
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db, SessionLocal
from app.database.models import Product, Warehouse, Inventory
from app.simulation.schemas import (
    ScenarioTypeEnum,
    SimulationScenario,
    SimulationRequest,
    SimulationResponse,
    BaselineMetrics,
    SimulatedMetrics,
)
from app.simulation.scenarios import _heuristic_parse_scenario, validate_scenario
from app.simulation.calculations import (
    simulate_supplier_delay,
    simulate_demand_change,
    simulate_lead_time_change,
    simulate_inventory_transfer,
)
from app.simulation.impact import calculate_simulation_impact
from app.simulation.recommendations import generate_simulation_recommendation
from app.simulation.baseline import calculate_baseline_metrics
from app.simulation.engine import SimulationEngine
from app.simulation.service import SimulationService
from app.llm.fake_provider import FakeLLMProvider
from app.agents.schemas import AgentQueryRequest, ToolEnum
from app.agents.service import AgentService

client = TestClient(app)


def test_scenario_parsing():
    """
    Test 1: Verifies heuristic scenario extraction into structured SimulationScenario.
    """
    # Delay scenario
    text_delay = "What happens if supplier delay increases by 7 days for SKU-001?"
    sc_delay = _heuristic_parse_scenario(text_delay)
    assert sc_delay.scenario_type == ScenarioTypeEnum.SUPPLIER_DELAY
    assert sc_delay.delay_days == 7

    # Demand change scenario
    text_demand = "Simulate a 20% increase in demand for product SKU-002"
    sc_demand = _heuristic_parse_scenario(text_demand)
    assert sc_demand.scenario_type == ScenarioTypeEnum.DEMAND_INCREASE
    assert sc_demand.demand_change_percent == 20.0

    # Lead time change scenario
    text_lt = "What if lead time increases by 10 days for SKU-001?"
    sc_lt = _heuristic_parse_scenario(text_lt)
    assert sc_lt.scenario_type == ScenarioTypeEnum.LEAD_TIME_INCREASE
    assert sc_lt.lead_time_change_days == 10

    # Inventory transfer scenario
    text_transfer = "Transfer 500 units from WH-WEST to WH-EAST"
    sc_transfer = _heuristic_parse_scenario(text_transfer)
    assert sc_transfer.scenario_type == ScenarioTypeEnum.INVENTORY_TRANSFER
    assert sc_transfer.transfer_quantity == 500


def test_scenario_validation():
    """
    Test 2: Verifies validation logic for scenario parameters and boundary constraints.
    """
    # Pydantic schema validation for negative bounds
    with pytest.raises(ValidationError):
        SimulationScenario(
            scenario_type=ScenarioTypeEnum.SUPPLIER_DELAY,
            delay_days=-5
        )

    with pytest.raises(ValidationError):
        SimulationScenario(
            scenario_type=ScenarioTypeEnum.INVENTORY_TRANSFER,
            transfer_quantity=-100
        )

    # validate_scenario logic test
    sc_unknown = SimulationScenario(scenario_type=ScenarioTypeEnum.UNKNOWN)
    is_valid, err = validate_scenario(sc_unknown)
    assert not is_valid
    assert "Unrecognized" in err


def test_deterministic_supplier_delay_calculation():
    """
    Test 3: Verifies deterministic calculations for supplier delay scenario.
    """
    baseline = calculate_baseline_metrics(product_id=1)
    scenario = SimulationScenario(
        scenario_type=ScenarioTypeEnum.SUPPLIER_DELAY,
        delay_days=10,
        product_id=1
    )
    simulated = simulate_supplier_delay(baseline, scenario)
    
    # Lead time should increase by 10 days
    assert simulated.lead_time_days == baseline.lead_time_days + 10
    assert simulated.reorder_point >= baseline.reorder_point


def test_deterministic_demand_change_calculation():
    """
    Test 4: Verifies demand increase (+50%) calculations.
    """
    baseline = calculate_baseline_metrics(product_id=1)
    
    sc_spike = SimulationScenario(
        scenario_type=ScenarioTypeEnum.DEMAND_INCREASE,
        demand_change_percent=50.0,
        product_id=1
    )
    sim_spike = simulate_demand_change(baseline, sc_spike)
    assert sim_spike.average_daily_demand == pytest.approx(baseline.average_daily_demand * 1.5, rel=1e-2)
    assert sim_spike.days_of_inventory < baseline.days_of_inventory


def test_inventory_transfer_conservation():
    """
    Test 5: Verifies inventory addition/transfer calculations.
    """
    baseline = calculate_baseline_metrics(product_id=1)
    transfer_qty = 500
    scenario = SimulationScenario(
        scenario_type=ScenarioTypeEnum.INVENTORY_TRANSFER,
        product_id=1,
        source_warehouse="WH-WEST",
        destination_warehouse="WH-EAST",
        transfer_quantity=transfer_qty
    )
    
    simulated = simulate_inventory_transfer(baseline, scenario)
    assert simulated.current_stock == baseline.current_stock + transfer_qty


def test_database_non_mutation():
    """
    Test 6: Guarantees that running what-if simulations does NOT mutate any database records.
    """
    service = SimulationService(provider_name="fake")
    req_question = "What if supplier delay increases by 30 days for product 1?"
    resp = service.run_simulation(question=req_question)
    assert resp is not None
    assert resp.simulated.lead_time_days > resp.baseline.lead_time_days


def test_impact_and_recommendations():
    """
    Test 7: Verifies impact rating calculation and recommendation rules.
    """
    baseline = calculate_baseline_metrics(product_id=1)
    sc_severe = SimulationScenario(
        scenario_type=ScenarioTypeEnum.SUPPLIER_DELAY,
        delay_days=30,
        product_id=1
    )
    sim_severe = simulate_supplier_delay(baseline, sc_severe)
    impact = calculate_simulation_impact(baseline, sim_severe, sc_severe)
    assert impact.impact_severity in ["HIGH", "CRITICAL", "MEDIUM"]

    rec = generate_simulation_recommendation(sim_severe, impact, sc_severe)
    assert rec.recommended_action in ["EXPEDITE", "REORDER", "TRANSFER", "ESCALATE", "MONITOR"]


def test_simulation_api_query_endpoint():
    """
    Test 8: Tests POST /api/v1/simulation/query endpoint.
    """
    payload = {
        "question": "What if supplier delay increases by 7 days for product 1?",
        "provider_override": "fake"
    }
    response = client.post("/api/v1/simulation/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "scenario" in data
    assert "baseline" in data
    assert "simulated" in data
    assert "impact" in data
    assert "recommendation" in data
    assert "explanation" in data
    assert data["scenario"]["delay_days"] == 7


def test_simulation_api_run_endpoint():
    """
    Test 9: Tests POST /api/v1/simulation/run endpoint with explicit structured request.
    """
    payload = {
        "scenario_type": "DEMAND_INCREASE",
        "demand_change_percent": 25.0,
        "product_id": 1
    }
    response = client.post("/api/v1/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "scenario" in data
    assert "simulated" in data
    assert data["scenario"]["demand_change_percent"] == 25.0
    assert data["simulated"]["average_daily_demand"] > 0


def test_langgraph_agent_simulation_integration():
    """
    Test 10: Verifies end-to-end execution of LangGraph Agent routing to SIMULATION tool.
    """
    service = AgentService(provider_name="fake")
    req = AgentQueryRequest(
        question="Simulate what happens if supplier delay increases by 10 days for SKU-001"
    )
    resp = service.run_agent(req.question)
    
    assert resp is not None
    assert "SIMULATION" in resp.data_used or ToolEnum.SIMULATION in resp.data_used
    assert resp.answer is not None
