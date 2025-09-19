"""
OrderItem repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.order_item import OrderItem


class OrderItemRepository(BaseRepository[OrderItem]):
    """
    Repository for OrderItem model with order item-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(OrderItem, db)
    
    async def get_by_order(self, order_id: int, skip: int = 0, limit: int = 100) -> List[OrderItem]:
        """
        Get all order items for an order
        
        Args:
            order_id: Order ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[OrderItem]: List of order items for the order
        """
        return await self.get_all_by_filter({"order_id": order_id}, skip, limit)
    
    async def get_by_menu_item(self, menu_item_id: int, skip: int = 0, limit: int = 100) -> List[OrderItem]:
        """
        Get all order items for a menu item
        
        Args:
            menu_item_id: Menu item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[OrderItem]: List of order items for the menu item
        """
        return await self.get_all_by_filter({"menu_item_id": menu_item_id}, skip, limit)
    
    async def get_order_item_with_details(self, order_item_id: int) -> Optional[OrderItem]:
        """
        Get order item with menu item details loaded
        
        Args:
            order_item_id: Order item ID
            
        Returns:
            OrderItem or None: Order item with details if found
        """
        return await self.get_by_id_with_relations(order_item_id, ["menu_item"])
    
    async def count_by_order(self, order_id: int) -> int:
        """
        Count order items for an order
        
        Args:
            order_id: Order ID
            
        Returns:
            int: Number of order items for the order
        """
        return await self.count({"order_id": order_id})
    
    async def count_by_menu_item(self, menu_item_id: int) -> int:
        """
        Count order items for a menu item
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            int: Number of order items for the menu item
        """
        return await self.count({"menu_item_id": menu_item_id})
