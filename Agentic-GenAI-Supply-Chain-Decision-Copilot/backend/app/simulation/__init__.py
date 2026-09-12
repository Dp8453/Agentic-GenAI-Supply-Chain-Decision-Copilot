"""
What-If Simulation Engine Package for SupplyChain AI.
Provides deterministic scenario modeling for supplier delays, demand spikes, lead-time changes,
capacity changes, and inventory transfers without mutating database state.
"""

from app.simulation.schemas import (
    ScenarioTypeEnum, SimulationScenario, BaselineMetrics, SimulatedMetrics,
    SimulationImpact, SimulationRecommendation, SimulationResult,
    SimulationRequest, SimulationResponse
)
from app.simulation.service import SimulationService

__all__ = [
    "ScenarioTypeEnum",
    "SimulationScenario",
    "BaselineMetrics",
    "SimulatedMetrics",
    "SimulationImpact",
    "SimulationRecommendation",
    "SimulationResult",
    "SimulationRequest",
    "SimulationResponse",
    "SimulationService",
]
