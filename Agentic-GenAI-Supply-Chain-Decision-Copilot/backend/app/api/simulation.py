from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.connection import get_db
from app.simulation.schemas import SimulationRequest, SimulationResponse, SimulationScenario
from app.simulation.service import SimulationService

router = APIRouter(prefix="/simulation", tags=["What-If Simulation Engine"])


@router.post("/query", response_model=SimulationResponse)
def run_natural_language_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db)
) -> SimulationResponse:
    """
    POST /api/v1/simulation/query
    Executes a what-if simulation from a natural language scenario prompt.
    Parses scenario -> Loads baseline -> Calculates in-memory simulation -> Formats grounded explanation.
    """
    try:
        service = SimulationService(provider_name=request.provider_override)
        response = service.run_simulation(
            question=request.question,
            scenario=request.scenario,
            db=db,
            provider_override=request.provider_override
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation Error: {str(e)}")


@router.post("/run", response_model=SimulationResponse)
def run_structured_simulation(
    scenario: SimulationScenario,
    provider_override: str = "fake",
    db: Session = Depends(get_db)
) -> SimulationResponse:
    """
    POST /api/v1/simulation/run
    Executes a what-if simulation directly from a structured SimulationScenario payload.
    """
    try:
        service = SimulationService(provider_name=provider_override)
        response = service.run_simulation(
            scenario=scenario,
            db=db,
            provider_override=provider_override
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation Error: {str(e)}")
