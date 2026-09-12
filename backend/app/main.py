import time
import uuid
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings
from app.api.health import router as health_router
from app.api.forecast import router as forecast_router
from app.api.risk import router as risk_router
from app.api.rag import router as rag_router
from app.api.copilot import router as copilot_router
from app.api.sql_query import router as sql_router
from app.api.agent import router as agent_router
from app.api.simulation import router as simulation_router
from app.guardrails.sensitive_data import detect_and_redact_sensitive_data

# Configure structured application logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s (%(correlation_id)s): %(message)s"
)
logger = logging.getLogger("supplychain_ai")


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic GenAI Supply Chain Decision Copilot REST API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS using settings origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_and_security_middleware(request: Request, call_next):
    """
    HTTP Middleware for request correlation tracking, execution timing, rate limiting, and security header injection.
    """
    from app.guardrails.rate_limit import rate_limiter

    # 1. Correlation ID tracking
    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    start_time = time.time()

    # 2. Rate Limiting Check on API routes
    client_ip = request.client.host if request.client else "127.0.0.1"
    if request.url.path.startswith("/api/"):
        is_limited, _ = rate_limiter.is_rate_limited(client_ip)
        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {client_ip}", extra={"correlation_id": correlation_id})
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Please wait a moment before trying again."
                    }
                },
                headers={"X-Request-ID": correlation_id}
            )

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        # Log request completion with timing
        logger.info(
            f"{request.method} {request.url.path} status={response.status_code} duration={duration_ms}ms",
            extra={"correlation_id": correlation_id}
        )

        # Injects correlation ID and Security Headers
        response.headers["X-Request-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "no-referrer"

        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"{request.method} {request.url.path} failed after {duration_ms}ms: {exc}", extra={"correlation_id": correlation_id})
        raise exc


# Centralized Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    cid = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    _, safe_detail = detect_and_redact_sensitive_data(str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": safe_detail
            }
        },
        headers={"X-Request-ID": cid}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cid = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameter or request payload structure.",
                "details": exc.errors()
            }
        },
        headers={"X-Request-ID": cid}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    cid = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    logger.exception(f"Unhandled system exception: {exc}", extra={"correlation_id": cid})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "The supply chain copilot service encountered an unhandled error. Please try again."
            }
        },
        headers={"X-Request-ID": cid}
    )


# Include API Routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health & Readiness"])
app.include_router(forecast_router, prefix=settings.API_V1_STR, tags=["Forecasting"])
app.include_router(risk_router, prefix=settings.API_V1_STR, tags=["Inventory & Risk"])
app.include_router(rag_router, prefix=settings.API_V1_STR, tags=["RAG Retrieval"])
app.include_router(copilot_router, prefix=settings.API_V1_STR, tags=["Copilot AI Layer"])
app.include_router(sql_router, prefix=settings.API_V1_STR, tags=["NL-to-SQL Tool"])
app.include_router(agent_router, prefix=settings.API_V1_STR, tags=["Agent Orchestrator"])
app.include_router(simulation_router, prefix=settings.API_V1_STR, tags=["What-If Simulation Engine"])


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "health_check": f"{settings.API_V1_STR}/health",
        "readiness_check": f"{settings.API_V1_STR}/ready",
        "forecast": f"{settings.API_V1_STR}/forecast",
        "risk": f"{settings.API_V1_STR}/risk",
        "recommendations": f"{settings.API_V1_STR}/recommendations",
        "rag_query": f"{settings.API_V1_STR}/rag/query",
        "copilot_query": f"{settings.API_V1_STR}/copilot/query",
        "sql_query": f"{settings.API_V1_STR}/sql/query",
        "agent_query": f"{settings.API_V1_STR}/agent/query",
        "simulation_query": f"{settings.API_V1_STR}/simulation/query",
        "docs": "/docs" if settings.DEBUG else "Disabled in Production"
    }
