import pandas as pd
import numpy as np
from typing import Tuple, List

FEATURE_COLUMNS: List[str] = [
    "lag_1", "lag_7", "lag_14", "lag_28",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
    "rolling_std_7", "rolling_std_14",
    "day_of_week", "day_of_month", "month", "week_of_year", "trend"
]


def prepare_daily_sales(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates sales data to daily total per product and reindexes date range
    to explicitly preserve zero-demand days.
    """
    if sales_df.empty:
        return pd.DataFrame(columns=["product_id", "sale_date", "quantity"])

    sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])

    # Aggregate by product_id and sale_date
    daily = sales_df.groupby(["product_id", "sale_date"])["quantity"].sum().reset_index()

    # Reindex date range per product to preserve zero sales days
    processed_dfs = []
    for pid, group in daily.groupby("product_id"):
        group = group.set_index("sale_date")
        full_idx = pd.date_range(start=group.index.min(), end=group.index.max(), freq="D")
        reindexed = group.reindex(full_idx)
        reindexed["product_id"] = pid
        reindexed["quantity"] = reindexed["quantity"].fillna(0)
        reindexed = reindexed.reset_index().rename(columns={"index": "sale_date"})
        processed_dfs.append(reindexed)

    if not processed_dfs:
        return pd.DataFrame(columns=["product_id", "sale_date", "quantity"])

    return pd.concat(processed_dfs, ignore_index=True)


def create_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates time-series lag, rolling statistics, calendar, and trend features.
    
    STRICT LEAKAGE PREVENTION:
    All rolling statistics are computed on shifted data (.shift(1)) to ensure that
    today's features only use past historical observations and never future values.
    """
    df = daily_df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values(by=["product_id", "sale_date"]).reset_index(drop=True)

    feature_dfs = []

    for pid, group in df.groupby("product_id"):
        group = group.sort_values(by="sale_date").copy()
        
        # Shifted series to prevent data leakage
        shifted_qty = group["quantity"].shift(1)

        # Lags
        group["lag_1"] = group["quantity"].shift(1)
        group["lag_7"] = group["quantity"].shift(7)
        group["lag_14"] = group["quantity"].shift(14)
        group["lag_28"] = group["quantity"].shift(28)

        # Rolling means & std (computed on shifted_qty)
        group["rolling_mean_7"] = shifted_qty.rolling(window=7, min_periods=1).mean()
        group["rolling_mean_14"] = shifted_qty.rolling(window=14, min_periods=1).mean()
        group["rolling_mean_28"] = shifted_qty.rolling(window=28, min_periods=1).mean()
        
        group["rolling_std_7"] = shifted_qty.rolling(window=7, min_periods=1).std().fillna(0)
        group["rolling_std_14"] = shifted_qty.rolling(window=14, min_periods=1).std().fillna(0)

        # Calendar features
        group["day_of_week"] = group["sale_date"].dt.dayofweek
        group["day_of_month"] = group["sale_date"].dt.day
        group["month"] = group["sale_date"].dt.month
        group["week_of_year"] = group["sale_date"].dt.isocalendar().week.astype(int)

        # Trend feature (sequential integer day count)
        min_date = group["sale_date"].min()
        group["trend"] = (group["sale_date"] - min_date).dt.days

        feature_dfs.append(group)

    result_df = pd.concat(feature_dfs, ignore_index=True)
    # Drop initial rows where maximum lag (28 days) produces NaN
    result_df = result_df.dropna(subset=["lag_28"]).reset_index(drop=True)
    return result_df
