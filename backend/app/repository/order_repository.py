"""
Order repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from .base_repository import BaseRepository
from ..models.order import Order, OrderStatus


class OrderRepository(BaseRepository[Order]):
    """
    Repository for Order model with order-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)
    
    async def get_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get all orders for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of orders for the restaurant
        """
        result = await self.db.execute(
            select(Order)
            .where(Order.restaurant_id == restaurant_id)
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_status(self, restaurant_id: int, status: OrderStatus, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get orders by status for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            status: Order status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of orders with specified status
        """
        result = await self.db.execute(
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                Order.status == status
            )
            .order_by(Order.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get all orders for a user
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of orders for the user
        """
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_order_with_items(self, order_id: int) -> Optional[Order]:
        """
        Get order with its items loaded
        
        Args:
            order_id: Order ID
            
        Returns:
            Order or None: Order with items if found
        """
        return await self.get_by_id_with_relations(order_id, ["order_items"])
    
    async def get_recent_orders(self, restaurant_id: int, hours: int = 24, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get recent orders for a restaurant within specified hours
        
        Args:
            restaurant_id: Restaurant ID
            hours: Number of hours to look back
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of recent orders
        """
        result = await self.db.execute(
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                Order.created_at >= func.now() - func.interval(f'{hours} hours')
            )
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_orders_by_date_range(self, restaurant_id: int, start_date, end_date, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get orders within a date range for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            start_date: Start date
            end_date: End date
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of orders within date range
        """
        result = await self.db.execute(
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_pending_orders(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get pending orders for a restaurant (for kitchen display)
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of pending orders
        """
        return await self.get_by_status(restaurant_id, OrderStatus.PENDING, skip, limit)
    
    async def get_preparing_orders(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """
        Get preparing orders for a restaurant (for kitchen display)
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Order]: List of preparing orders
        """
        return await self.get_by_status(restaurant_id, OrderStatus.PREPARING, skip, limit)
    
    async def count_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count orders for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of orders for the restaurant
        """
        return await self.count({"restaurant_id": restaurant_id})
    
    async def count_by_status(self, restaurant_id: int, status: OrderStatus) -> int:
        """
        Count orders by status for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            status: Order status
            
        Returns:
            int: Number of orders with specified status
        """
        result = await self.db.execute(
            select(Order.id)
            .where(
                Order.restaurant_id == restaurant_id,
                Order.status == status
            )
        )
        return len(result.scalars().all())
