from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ml.predict import forecast_product

router = APIRouter()


class ForecastRequest(BaseModel):
    product_id: int = Field(..., gt=0, description="Unique product ID")
    horizon_days: int = Field(14, gt=0, le=90, description="Forecast horizon in days (1 to 90)")


class DailyForecastItem(BaseModel):
    date: str
    predicted_demand: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    product_id: int
    sku: str
    horizon_days: int
    model_used: str
    model_version: str
    total_predicted_demand: float
    forecast: List[DailyForecastItem]


@router.post("/forecast", response_model=ForecastResponse, summary="Generate ML Demand Forecast")
async def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a multi-step ML demand forecast for a target product over a specified horizon.
    """
    try:
        result = forecast_product(
            product_id=request.product_id,
            horizon_days=request.horizon_days,
            db=db
        )
        return ForecastResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=500, detail=f"ML Model configuration error: {str(fnf)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")
