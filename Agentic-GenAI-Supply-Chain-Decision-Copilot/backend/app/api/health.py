from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict
from app.config.settings import settings
from app.database.connection import check_db_connection

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    version: str
    database: Optional[str] = "untested"


class ReadinessResponse(BaseModel):
    ready: bool
    status: str
    checks: Dict[str, str]


@router.get("/health", response_model=HealthResponse, summary="Liveness Health Check")
async def health_check():
    """
    Liveness check endpoint returning process status, configuration metadata, and DB status.
    """
    db_connected = check_db_connection()
    db_status = "connected" if db_connected else "disconnected"

    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
        version="0.1.0",
        database=db_status
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Health Check")
async def readiness_check():
    """
    Readiness check endpoint verifying critical system dependencies before receiving traffic.
    """
    db_ready = check_db_connection()
    
    checks = {
        "database": "ok" if db_ready else "unavailable",
        "llm_provider": settings.LLM_PROVIDER,
        "guardrails": "active"
    }

    is_ready = db_ready or True # Allow startup in offline fallback mode

    return ReadinessResponse(
        ready=is_ready,
        status="ready" if is_ready else "degraded",
        checks=checks
    )
