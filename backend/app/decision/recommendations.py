import math
from typing import Tuple


def classify_recommendation_action(
    risk_level: str,
    has_stockout: bool,
    inventory_position: int,
    reorder_point: int
) -> str:
    """
    Classifies recommended procurement action:
    URGENT_REORDER, REORDER, MONITOR, NO_ACTION
    """
    if risk_level == "CRITICAL" or has_stockout:
        return "URGENT_REORDER"
    elif risk_level == "HIGH" or inventory_position <= reorder_point:
        return "REORDER"
    elif risk_level == "MEDIUM":
        return "MONITOR"
    else:
        return "NO_ACTION"


def calculate_recommended_reorder_quantity(
    target_inventory: int,
    inventory_position: int,
    minimum_order_quantity: int
) -> int:
    """
    Calculates recommended order quantity and rounds up to the Minimum Order Quantity (MOQ) increment.
    
    Rule:
    1. Raw deficit = Target Inventory - Inventory Position
    2. If Raw deficit <= 0: 0
    3. If 0 < Raw deficit <= MOQ: MOQ
    4. If Raw deficit > MOQ: ceil(Raw deficit / MOQ) * MOQ
    """
    deficit = target_inventory - inventory_position
    if deficit <= 0:
        return 0

    moq = max(1, minimum_order_quantity)
    if deficit <= moq:
        return moq

    num_moqs = math.ceil(deficit / float(moq))
    return int(num_moqs * moq)
