"""
Menu Cache Interface

Abstract interface for menu caching to allow different implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.menu_item import MenuItem


class MenuCacheInterface(ABC):
    """Abstract interface for menu caching operations"""
    
    @abstractmethod
    async def get_menu_items(self, restaurant_id: int) -> List[MenuItem]:
        """Get all menu items for a restaurant from cache"""
        pass
    
    @abstractmethod
    async def get_menu_item_by_id(self, restaurant_id: int, menu_item_id: int) -> Optional[MenuItem]:
        """Get a specific menu item by ID from cache"""
        pass
    
    @abstractmethod
    async def search_menu_items(self, restaurant_id: int, query: str) -> List[MenuItem]:
        """Search menu items by name/description from cache"""
        pass
    
    @abstractmethod
    async def get_available_items(self, restaurant_id: int) -> List[str]:
        """Get available menu item names from cache"""
        pass
    
    @abstractmethod
    async def cache_menu_items(self, restaurant_id: int, menu_items: List[MenuItem]) -> None:
        """Cache menu items for a restaurant"""
        pass
    
    @abstractmethod
    async def invalidate_restaurant_cache(self, restaurant_id: int) -> None:
        """Invalidate cache for a specific restaurant"""
        pass
    
    @abstractmethod
    async def invalidate_all_cache(self) -> None:
        """Invalidate all menu cache"""
        pass
    
    @abstractmethod
    async def is_cache_available(self) -> bool:
        """Check if cache is available and working"""
        pass
