"""
Category repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.category import Category


class CategoryRepository(BaseRepository[Category]):
    """
    Repository for Category model with category-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Category, db)
    
    async def get_by_name_and_restaurant(self, name: str, restaurant_id: int) -> Optional[Category]:
        """
        Get category by name and restaurant
        
        Args:
            name: Category name
            restaurant_id: Restaurant ID
            
        Returns:
            Category or None: Category instance if found
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.name == name, Category.restaurant_id == restaurant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Category]:
        """
        Get all categories for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Category]: List of categories for the restaurant
        """
        return await self.get_all_by_filter({"restaurant_id": restaurant_id}, skip, limit)
    
    async def get_active_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Category]:
        """
        Get all active categories for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Category]: List of active categories for the restaurant
        """
        result = await self.db.execute(
            select(Category)
            .where(
                Category.restaurant_id == restaurant_id,
                Category.is_active == True
            )
            .order_by(Category.display_order)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_category_with_menu_items(self, category_id: int) -> Optional[Category]:
        """
        Get category with its menu items loaded
        
        Args:
            category_id: Category ID
            
        Returns:
            Category or None: Category with menu items if found
        """
        return await self.get_by_id_with_relations(category_id, ["menu_items"])
    
    async def reorder_categories(self, restaurant_id: int, category_orders: dict) -> bool:
        """
        Update display order for categories
        
        Args:
            restaurant_id: Restaurant ID
            category_orders: Dictionary mapping category_id to display_order
            
        Returns:
            bool: True if successful
        """
        try:
            for category_id, display_order in category_orders.items():
                await self.update(category_id, display_order=display_order)
            return True
        except Exception:
            return False
    
    async def count_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count categories for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of categories for the restaurant
        """
        return await self.count({"restaurant_id": restaurant_id})
