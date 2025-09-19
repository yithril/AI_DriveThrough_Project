"""
Unit of Work pattern for managing database transactions
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..repository.base_repository import BaseRepository
from ..repository.order_repository import OrderRepository
from ..repository.order_item_repository import OrderItemRepository
from ..repository.restaurant_repository import RestaurantRepository
from ..repository.menu_item_repository import MenuItemRepository
from ..repository.inventory_repository import InventoryRepository
from ..repository.menu_item_ingredient_repository import MenuItemIngredientRepository


class UnitOfWork:
    """
    Unit of Work pattern - manages a single transaction across multiple repositories
    Like a DbContext in .NET Entity Framework
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._repositories: Dict[str, BaseRepository] = {}
        self._committed = False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-commit on success, rollback on exception"""
        if exc_type is None and not self._committed:
            # No exception occurred, commit the transaction
            import asyncio
            asyncio.create_task(self.commit())
        elif exc_type is not None:
            # Exception occurred, rollback
            import asyncio
            asyncio.create_task(self.rollback())
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None and not self._committed:
            await self.commit()
        elif exc_type is not None:
            await self.rollback()
    
    @property
    def orders(self) -> OrderRepository:
        """Get OrderRepository instance"""
        if 'orders' not in self._repositories:
            self._repositories['orders'] = OrderRepository(self.db)
        return self._repositories['orders']
    
    @property
    def order_items(self) -> OrderItemRepository:
        """Get OrderItemRepository instance"""
        if 'order_items' not in self._repositories:
            self._repositories['order_items'] = OrderItemRepository(self.db)
        return self._repositories['order_items']
    
    @property
    def restaurants(self) -> RestaurantRepository:
        """Get RestaurantRepository instance"""
        if 'restaurants' not in self._repositories:
            self._repositories['restaurants'] = RestaurantRepository(self.db)
        return self._repositories['restaurants']
    
    @property
    def menu_items(self) -> MenuItemRepository:
        """Get MenuItemRepository instance"""
        if 'menu_items' not in self._repositories:
            self._repositories['menu_items'] = MenuItemRepository(self.db)
        return self._repositories['menu_items']
    
    @property
    def inventory(self) -> InventoryRepository:
        """Get InventoryRepository instance"""
        if 'inventory' not in self._repositories:
            self._repositories['inventory'] = InventoryRepository(self.db)
        return self._repositories['inventory']
    
    @property
    def menu_item_ingredients(self) -> MenuItemIngredientRepository:
        """Get MenuItemIngredientRepository instance"""
        if 'menu_item_ingredients' not in self._repositories:
            self._repositories['menu_item_ingredients'] = MenuItemIngredientRepository(self.db)
        return self._repositories['menu_item_ingredients']
    
    async def commit(self):
        """Commit all changes in the transaction"""
        if not self._committed:
            await self.db.commit()
            self._committed = True
    
    async def rollback(self):
        """Rollback all changes in the transaction"""
        await self.db.rollback()
        self._committed = True  # Mark as "committed" to prevent double rollback
