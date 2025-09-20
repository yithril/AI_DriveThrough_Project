"""
Order validation limits and business rules
These constants define the business logic boundaries for order validation
"""

from typing import Dict, Any
from ..core.config import settings


class OrderLimits:
    """Configurable order validation limits"""
    
    # Quantity limits per item (prevents "10,000 tacos" scenarios)
    MAX_QUANTITY_PER_ITEM: int = settings.MAX_QUANTITY_PER_ITEM
    MIN_QUANTITY_PER_ITEM: int = 1  # Prevents negative quantities
    
    # Order totals (prevents massive order abuse)
    MAX_ORDER_TOTAL: float = settings.MAX_ORDER_TOTAL
    MIN_ORDER_TOTAL: float = 0.01  # Minimum reasonable order value
    
    # Item counts (prevents "500 different items" scenarios)
    MAX_ITEMS_PER_ORDER: int = settings.MAX_ITEMS_PER_ORDER
    MIN_ITEMS_PER_ORDER: int = 1  # Minimum items for a valid order
    
    # Customization limits (prevents excessive customizations)
    MAX_CUSTOMIZATIONS_PER_ITEM: int = 10  # Reasonable limit on customizations
    
    
