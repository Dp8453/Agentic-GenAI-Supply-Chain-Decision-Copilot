# Machine Learning Demand Forecasting Module — SupplyChain AI

## 1. Executive Summary & Problem Statement

Accurate demand forecasting is the bedrock of proactive supply chain management. In **SupplyChain AI**, the Machine Learning module predicts expected daily product sales over a forward-looking horizon (e.g., 14 to 30 days).

Crucially, the ML module is designed as an **independent deterministic tool**. It can be executed standalone via API or called by the **LangGraph Agent** to evaluate inventory stockout risk.

---

## 2. Feature Engineering & Leakage Prevention

The feature engineering pipeline (`backend/app/ml/features.py`) converts raw transactional sales into structured supervised learning feature matrices.

### Target Variable
- **Daily Sales Quantity**: Aggregate daily total sales per `product_id`. Zero-demand days are explicitly preserved by reindexing the date range from `min_date` to `max_date` per product.

### Feature Matrix Definition
| Feature Group | Features | Description |
|---|---|---|
| **Lags** | `lag_1`, `lag_7`, `lag_14`, `lag_28` | Previous demand observations (1, 7, 14, and 28 days ago) |
| **Rolling Means** | `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28` | Historical moving average demand over 7, 14, and 28 days |
| **Rolling Std** | `rolling_std_7`, `rolling_std_14` | Volatility & variance measure of historical demand |
| **Calendar** | `day_of_week`, `day_of_month`, `month`, `week_of_year` | Day of week (0-6), day of month (1-31), month (1-12) |
| **Trend** | `trend` | Sequential day count integer since observation start |

### Strict Future Data Leakage Prevention
To prevent data leakage during time-series feature generation:
- All rolling statistics (`rolling_mean_7`, `rolling_std_7`, etc.) are computed strictly on shifted data (`quantity.shift(1)`).
- When forecasting day $T + k$ in multi-step predictions, features are calculated using historical observations up to day $T + k - 1$. No future actual sales are ever exposed to the model.

---

## 3. Chronological Train / Validation / Test Splitting

Randomly shuffling time-series data creates severe data leakage, as future data points pollute past training windows.

We enforce strict **chronological splitting**:
- **70% Training**: Learns baseline sales patterns, trendlines, and weekly/monthly seasonality.
- **15% Validation**: Used during XGBoost training for early stopping and hyperparameter tuning.
- **15% Out-of-Sample Test**: Unseen future data window used to measure final model accuracy.

---

## 4. Model Benchmarking & Evaluation

We evaluate model performance using **MAE (Mean Absolute Error)** and **RMSE (Root Mean Squared Error)**:

$$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$

$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}$$

### Model Comparison
- **Baseline Model (7-Day Seasonal Naive)**: Predicts demand based on `lag_7` (same day of previous week).
- **XGBoost Regressor**: Gradient boosted decision trees trained on full lag, rolling, calendar, and trend features.

---

## 5. Multi-Step Recursive Prediction Pipeline

Multi-day forecasting (e.g., predicting 14 days into the future) uses a **recursive multi-step strategy**:
1. For step $k = 1$: Compute feature vector from historical data, predict demand $\hat{y}_{T+1}$.
2. Append $\hat{y}_{T+1}$ to the historical series.
3. For step $k = 2$: Compute feature vector using updated series containing $\hat{y}_{T+1}$, predict $\hat{y}_{T+2}$.
4. Repeat up to $k = N$.
5. Apply numerical boundary validation: clip predictions to $\ge 0.0$ and verify non-NaN/non-Inf values.

---

## 6. API Integration

`POST /api/v1/forecast`
```json
{
  "product_id": 1,
  "horizon_days": 14
}
```
Response:
```json
{
  "product_id": 1,
  "sku": "SKU-001",
  "horizon_days": 14,
  "model_used": "XGBoost Regressor Demand Forecaster",
  "model_version": "1.0.0",
  "total_predicted_demand": 425.5,
  "forecast": [
    {
      "date": "2025-07-01",
      "predicted_demand": 30.5,
      "lower_bound": 25.0,
      "upper_bound": 36.0
    }
  ]
}
```
