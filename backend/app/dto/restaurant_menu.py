"""
Restaurant menu DTOs for API responses
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class TagDto:
    """Tag data transfer object"""
    name: str
    color: str


@dataclass
class MenuItemDto:
    """Menu item data transfer object"""
    id: int
    name: str
    price: float
    description: Optional[str]
    image_url: Optional[str]
    sort_order: int
    tags: List[TagDto]


@dataclass
class CategoryDto:
    """Category data transfer object"""
    id: int
    name: str
    description: Optional[str]
    sort_order: int
    items: List[MenuItemDto]


@dataclass
class RestaurantDto:
    """Restaurant data transfer object"""
    id: int
    name: str
    primary_color: str
    secondary_color: str
    logo_url: Optional[str]


@dataclass
class RestaurantMenuResponse:
    """Complete restaurant menu response"""
    restaurant: RestaurantDto
    menu: List[CategoryDto]
    total_items: int
