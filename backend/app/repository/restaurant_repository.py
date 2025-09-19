"""
Restaurant repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.restaurant import Restaurant


class RestaurantRepository(BaseRepository[Restaurant]):
    """
    Repository for Restaurant model with restaurant-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Restaurant, db)
    
    async def get_by_name(self, name: str) -> Optional[Restaurant]:
        """
        Get restaurant by name
        
        Args:
            name: Restaurant name
            
        Returns:
            Restaurant or None: Restaurant instance if found
        """
        return await self.get_by_field("name", name)
    
    async def get_active_restaurants(self, skip: int = 0, limit: int = 100) -> List[Restaurant]:
        """
        Get all active restaurants
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Restaurant]: List of active restaurants
        """
        return await self.get_all_by_filter({"is_active": True}, skip, limit)
    
    async def get_restaurant_with_menu(self, restaurant_id: int) -> Optional[Restaurant]:
        """
        Get restaurant with its categories and menu items loaded
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            Restaurant or None: Restaurant with menu data if found
        """
        return await self.get_by_id_with_relations(
            restaurant_id, 
            ["categories", "menu_items", "tags"]
        )
    
    async def search_restaurants(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Restaurant]:
        """
        Search restaurants by name or description
        
        Args:
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Restaurant]: List of matching restaurants
        """
        result = await self.db.execute(
            select(Restaurant)
            .where(
                Restaurant.name.ilike(f"%{search_term}%") |
                Restaurant.description.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_active_restaurants(self) -> int:
        """
        Count active restaurants
        
        Returns:
            int: Number of active restaurants
        """
        return await self.count({"is_active": True})
