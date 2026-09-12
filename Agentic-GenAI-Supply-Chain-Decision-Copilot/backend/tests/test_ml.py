import pytest
import pandas as pd
import numpy as np
import os
import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.ml.features import prepare_daily_sales, create_features, FEATURE_COLUMNS
from app.ml.train import train_forecasting_models
from app.ml.predict import forecast_product, MODEL_PATH, METADATA_PATH

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_sales_df():
    dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
    records = []
    for d in dates:
        qty = int(20 + 5 * np.sin(d.dayofweek) + np.random.randint(-3, 4))
        records.append({"product_id": 1, "sale_date": str(d.date()), "quantity": max(0, qty)})
    return pd.DataFrame(records)


def test_prepare_daily_sales_and_feature_engineering(sample_sales_df):
    daily = prepare_daily_sales(sample_sales_df)
    assert not daily.empty
    assert "product_id" in daily.columns
    assert "sale_date" in daily.columns
    assert "quantity" in daily.columns

    features_df = create_features(daily)
    assert not features_df.empty
    for col in FEATURE_COLUMNS:
        assert col in features_df.columns
    assert not features_df[FEATURE_COLUMNS].isnull().any().any()


def test_train_forecasting_models(sample_sales_df):
    metadata = train_forecasting_models(sales_df=sample_sales_df)
    assert os.path.exists(MODEL_PATH)
    assert os.path.exists(METADATA_PATH)
    assert "metrics" in metadata
    assert "baseline" in metadata["metrics"]
    assert "gradient_boosting" in metadata["metrics"]
    assert metadata["metrics"]["gradient_boosting"]["mae"] >= 0


def test_forecast_product_multistep(sample_sales_df):
    result = forecast_product(product_id=1, horizon_days=14, sales_df=sample_sales_df)
    assert result["product_id"] == 1
    assert result["horizon_days"] == 14
    assert len(result["forecast"]) == 14
    assert result["total_predicted_demand"] >= 0

    for item in result["forecast"]:
        assert "date" in item
        assert "predicted_demand" in item
        assert item["predicted_demand"] >= 0
        assert not np.isnan(item["predicted_demand"])
        assert not np.isinf(item["predicted_demand"])
        assert item["lower_bound"] <= item["upper_bound"]


def test_forecast_product_invalid_horizon(sample_sales_df):
    with pytest.raises(ValueError):
        forecast_product(product_id=1, horizon_days=0, sales_df=sample_sales_df)

    with pytest.raises(ValueError):
        forecast_product(product_id=1, horizon_days=100, sales_df=sample_sales_df)


def test_forecast_api_endpoint(sample_sales_df):
    # Ensure model is trained
    train_forecasting_models(sales_df=sample_sales_df)

    response = client.post("/api/v1/forecast", json={"product_id": 1, "horizon_days": 7})
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == 1
    assert data["horizon_days"] == 7
    assert len(data["forecast"]) == 7

    # Test invalid horizon validation
    bad_response = client.post("/api/v1/forecast", json={"product_id": 1, "horizon_days": 150})
    assert bad_response.status_code == 422  # Pydantic validation error (le=90)
