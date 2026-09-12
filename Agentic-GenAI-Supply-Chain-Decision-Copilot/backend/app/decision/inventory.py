import math
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


def calculate_inventory_position(current_stock: int, incoming_quantity: int, reserved_stock: int) -> int:
    """
    Inventory Position = Current Stock + Incoming Purchase Orders - Reserved Stock
    """
    pos = current_stock + incoming_quantity - reserved_stock
    return max(0, pos)


def calculate_demand_stats(sales_quantities: List[float]) -> Tuple[float, float]:
    """
    Calculates average daily demand (D) and demand standard deviation (sigma_D).
    """
    if not sales_quantities:
        return 0.0, 0.0
    arr = np.array(sales_quantities, dtype=float)
    avg_demand = float(np.mean(arr))
    std_demand = float(np.std(arr)) if len(arr) > 1 else 0.0
    return max(0.0, round(avg_demand, 2)), max(0.0, round(std_demand, 2))


def calculate_lead_time_stats(
    perf_records: List[Dict[str, Any]], 
    default_lead_time: float = 7.0
) -> Tuple[float, float]:
    """
    Calculates average actual lead time (L) and lead time standard deviation (sigma_L)
    from historical supplier performance.
    """
    if not perf_records:
        return float(default_lead_time), 1.5  # Default std fallback

    lead_times = [r["actual_lead_time"] for r in perf_records if "actual_lead_time" in r]
    if not lead_times:
        return float(default_lead_time), 1.5

    arr = np.array(lead_times, dtype=float)
    avg_lt = float(np.mean(arr))
    std_lt = float(np.std(arr)) if len(arr) > 1 else 1.0
    return max(1.0, round(avg_lt, 2)), max(0.2, round(std_lt, 2))


def calculate_safety_stock(
    avg_demand: float,
    std_demand: float,
    avg_lead_time: float,
    std_lead_time: float,
    service_level_z: float = 1.645  # 95% service level
) -> int:
    """
    Safety Stock Formula:
    SS = Z * sqrt( L * (sigma_D ^ 2) + (D ^ 2) * (sigma_L ^ 2) )
    Incorporates both demand variability (sigma_D) and lead-time variability (sigma_L).
    """
    if avg_demand <= 0:
        return 0

    variance = (avg_lead_time * (std_demand ** 2)) + ((avg_demand ** 2) * (std_lead_time ** 2))
    ss_raw = service_level_z * math.sqrt(max(0.0, variance))
    return max(0, math.ceil(ss_raw))


def calculate_reorder_point(expected_demand_during_lead_time: float, safety_stock: int) -> int:
    """
    Reorder Point (ROP) = Expected Demand During Lead Time + Safety Stock
    """
    rop_raw = expected_demand_during_lead_time + safety_stock
    return max(0, math.ceil(rop_raw))


def calculate_days_of_inventory(current_stock: int, avg_daily_demand: float) -> Optional[float]:
    """
    Days of Inventory = Current Stock / Average Daily Demand
    Handles zero average daily demand cleanly by returning None.
    """
    if avg_daily_demand <= 0:
        return None
    return round(float(current_stock) / avg_daily_demand, 1)
