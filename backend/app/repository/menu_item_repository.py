"""
MenuItem repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from .base_repository import BaseRepository
from ..models.menu_item import MenuItem


class MenuItemRepository(BaseRepository[MenuItem]):
    """
    Repository for MenuItem model with menu item-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(MenuItem, db)
    
    async def get_by_name_and_category(self, name: str, category_id: int) -> Optional[MenuItem]:
        """
        Get menu item by name and category
        
        Args:
            name: Menu item name
            category_id: Category ID
            
        Returns:
            MenuItem or None: Menu item instance if found
        """
        result = await self.db.execute(
            select(MenuItem)
            .where(MenuItem.name == name, MenuItem.category_id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """
        Get all menu items for a category
        
        Args:
            category_id: Category ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItem]: List of menu items for the category
        """
        return await self.get_all_by_filter({"category_id": category_id}, skip, limit)
    
    async def get_available_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """
        Get all available menu items for a category
        
        Args:
            category_id: Category ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItem]: List of available menu items for the category
        """
        try:
            result = await self.db.execute(
                select(MenuItem)
                .where(
                    MenuItem.category_id == category_id,
                    MenuItem.is_available == True
                )
                .order_by(MenuItem.display_order)
                .offset(skip)
                .limit(limit)
            )
            menu_items = result.scalars().all()
            return menu_items
        except Exception as e:
            raise
    
    async def get_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """
        Get all menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItem]: List of menu items for the restaurant
        """
        return await self.get_all_by_filter({"restaurant_id": restaurant_id}, skip, limit)
    
    async def get_available_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """
        Get all available menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItem]: List of available menu items for the restaurant
        """
        result = await self.db.execute(
            select(MenuItem)
            .where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            )
            .order_by(MenuItem.display_order)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_menu_item_with_tags(self, menu_item_id: int) -> Optional[MenuItem]:
        """
        Get menu item with its tags loaded
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            MenuItem or None: Menu item with tags if found
        """
        return await self.get_by_id_with_relations(menu_item_id, ["tags"])
    
    async def search_menu_items(self, restaurant_id: int, search_term: str, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """
        Search menu items by name or description within a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItem]: List of matching menu items
        """
        result = await self.db.execute(
            select(MenuItem)
            .where(
                and_(
                    MenuItem.restaurant_id == restaurant_id,
                    MenuItem.is_available == True,
                    MenuItem.name.ilike(f"%{search_term}%")
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_price_range(self, restaurant_id: int, min_price: float, max_price: float, skip: int = 0, limit: int = 100) -> List[MenuItem]:
        """
        Get menu items within a price range for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            min_price: Minimum price
            max_price: Maximum price
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItem]: List of menu items within price range
        """
        result = await self.db.execute(
            select(MenuItem)
            .where(
                and_(
                    MenuItem.restaurant_id == restaurant_id,
                    MenuItem.is_available == True,
                    MenuItem.price >= min_price,
                    MenuItem.price <= max_price
                )
            )
            .order_by(MenuItem.price)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of menu items for the restaurant
        """
        return await self.count({"restaurant_id": restaurant_id})
    
    async def count_available_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count available menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of available menu items for the restaurant
        """
        result = await self.db.execute(
            select(MenuItem.id)
            .where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            )
        )
        return len(result.scalars().all())
