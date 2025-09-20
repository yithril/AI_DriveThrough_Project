"""
OrderSessionService - Redis primary with PostgreSQL fallback
Implements OrderSessionInterface for managing sessions and orders
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .order_session_interface import OrderSessionInterface
from .redis_service import RedisService
from ..core.unit_of_work import UnitOfWork
from ..models.order import Order, OrderStatus
from ..models.order_item import OrderItem
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class OrderSessionService(OrderSessionInterface):
    """
    Service for managing order sessions with Redis primary storage and PostgreSQL fallback
    """

    def __init__(self, redis_service: RedisService):
        """
        Initialize the service with Redis service dependency
        
        Args:
            redis_service: Redis service instance
        """
        self.redis = redis_service

    async def is_redis_available(self) -> bool:
        """
        Check if Redis is available and connected
        
        Returns:
            bool: True if Redis is available, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            return await self.redis.is_connected()
        except Exception as e:
            logger.error(f"Failed to check Redis availability: {e}")
            return False

    async def get_current_session_id(self) -> Optional[str]:
        """
        Get the current active session ID
        
        Returns:
            str: Current session ID if exists, None otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot get current session")
            return None
        
        try:
            return await self.redis.get("current:session")
        except Exception as e:
            logger.error(f"Failed to get current session ID: {e}")
            return None

    async def set_current_session_id(self, session_id: str, ttl: int = 900) -> bool:
        """
        Set the current active session ID
        
        Args:
            session_id: Session ID to set as current
            ttl: Time to live in seconds (default 15 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot set current session")
            return False
        
        try:
            return await self.redis.set("current:session", session_id, ttl)
        except Exception as e:
            logger.error(f"Failed to set current session ID: {e}")
            return False

    async def clear_current_session_id(self) -> bool:
        """
        Clear the current active session ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot clear current session")
            return False
        
        try:
            return await self.redis.delete("current:session")
        except Exception as e:
            logger.error(f"Failed to clear current session ID: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            dict: Session data if exists, None otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot get session")
            return None
        
        try:
            session_data = await self.redis.get(f"session:{session_id}")
            if session_data:
                return json.loads(session_data)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse session data for {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def create_session(self, session_data: Dict[str, Any], ttl: int = 900) -> bool:
        """
        Create a new session
        
        Args:
            session_data: Session data dictionary
            ttl: Time to live in seconds (default 15 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot create session")
            return False
        
        try:
            session_id = session_data.get("id")
            if not session_id:
                logger.error("Session data must contain 'id' field")
                return False
            
            session_json = json.dumps(session_data)
            return await self.redis.set(f"session:{session_id}", session_json, ttl)
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode session data: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False

    async def update_session(self, session_id: str, updates: Dict[str, Any], ttl: int = 900) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID to update
            updates: Data to merge into session
            ttl: Time to live in seconds (default 15 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot update session")
            return False
        
        try:
            # Get current session data
            current_data = await self.get_session(session_id)
            if not current_data:
                logger.error(f"Session {session_id} not found for update")
                return False
            
            # Merge updates
            current_data.update(updates)
            current_data["updated_at"] = datetime.now().isoformat()
            
            # Save updated session
            session_json = json.dumps(current_data)
            return await self.redis.set(f"session:{session_id}", session_json, ttl)
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode updated session data: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.warning("Redis not available, cannot delete session")
            return False
        
        try:
            return await self.redis.delete(f"session:{session_id}")
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    async def get_order(self, db: AsyncSession, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order data (Redis first, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_id: Order ID to retrieve
            
        Returns:
            dict: Order data if exists, None otherwise
        """
        # Try Redis first if it's a Redis order ID
        if order_id.startswith("redis_") and await self.is_redis_available():
            try:
                redis_order = await self.redis.get_order(order_id)
                if redis_order:
                    logger.info(f"Retrieved Redis order {order_id}")
                    return redis_order
            except Exception as e:
                logger.error(f"Failed to get Redis order {order_id}: {e}")
        
        # Try PostgreSQL fallback
        try:
            async with UnitOfWork(db) as uow:
                db_order = await uow.orders.get_by_id(int(order_id))
            if db_order:
                logger.info(f"Retrieved PostgreSQL order {order_id}")
                return db_order.to_dict()
        except ValueError:
            # order_id is not a valid integer, skip PostgreSQL lookup
            logger.debug(f"Order ID {order_id} is not a valid integer for PostgreSQL lookup")
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL order {order_id}: {e}")
        
        return None

    async def create_order(self, db: AsyncSession, order_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Create a new order (Redis primary, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_data: Order data dictionary
            ttl: Time to live in seconds for Redis (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Try Redis first if available
        if await self.is_redis_available():
            try:
                order_id = order_data.get("id")
                if not order_id:
                    logger.error("Order data must contain 'id' field")
                    return False
                
                success = await self.redis.set_order(order_id, order_data, ttl)
                if success:
                    logger.info(f"Created Redis order {order_id}")
                    return True
            except Exception as e:
                logger.error(f"Failed to create Redis order: {e}")
        
        # Fallback to PostgreSQL
        try:
            async with UnitOfWork(db) as uow:
                order = await uow.orders.create(
                    restaurant_id=order_data["restaurant_id"],
                    customer_name=order_data.get("customer_name"),
                    status=OrderStatus(order_data.get("status", "PENDING")),
                    subtotal=order_data.get("subtotal", 0.0),
                    tax_amount=order_data.get("tax_amount", 0.0),
                    total_amount=order_data.get("total_amount", 0.0)
                )
            
            logger.info(f"Created PostgreSQL order {order.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL order: {e}")
            return False

    async def update_order(self, db: AsyncSession, order_id: str, updates: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Update order data (Redis primary, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_id: Order ID to update
            updates: Data to merge into order
            ttl: Time to live in seconds for Redis (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Try Redis first if it's a Redis order ID
        if order_id.startswith("redis_") and await self.is_redis_available():
            try:
                redis_order = await self.redis.get_order(order_id)
                if redis_order:
                    # Merge updates
                    redis_order.update(updates)
                    redis_order["updated_at"] = datetime.now().isoformat()
                    
                    success = await self.redis.set_order(order_id, redis_order, ttl)
                    if success:
                        logger.info(f"Updated Redis order {order_id}")
                        return True
            except Exception as e:
                logger.error(f"Failed to update Redis order {order_id}: {e}")
        
        # Try PostgreSQL fallback
        try:
            async with UnitOfWork(db) as uow:
                db_order = await uow.orders.get_by_id(int(order_id))
            if db_order:
                # Update fields if they exist in updates
                if "status" in updates:
                    db_order.status = OrderStatus(updates["status"])
                if "customer_name" in updates:
                    db_order.customer_name = updates["customer_name"]
                if "subtotal" in updates:
                    db_order.subtotal = updates["subtotal"]
                if "tax_amount" in updates:
                    db_order.tax_amount = updates["tax_amount"]
                if "total_amount" in updates:
                    db_order.total_amount = updates["total_amount"]
                
                # Repository will handle the commit
                logger.info(f"Updated PostgreSQL order {order_id}")
                return True
        except ValueError:
            # order_id is not a valid integer
            logger.debug(f"Order ID {order_id} is not a valid integer for PostgreSQL update")
        except Exception as e:
            logger.error(f"Failed to update PostgreSQL order {order_id}: {e}")
        
        return False

    async def delete_order(self, db: AsyncSession, order_id: str) -> bool:
        """
        Delete an order (Redis primary, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_id: Order ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Try Redis first if it's a Redis order ID
        if order_id.startswith("redis_") and await self.is_redis_available():
            try:
                success = await self.redis.delete_order(order_id)
                if success:
                    logger.info(f"Deleted Redis order {order_id}")
                    return True
            except Exception as e:
                logger.error(f"Failed to delete Redis order {order_id}: {e}")
        
        # PostgreSQL doesn't typically delete orders, just mark as cancelled
        logger.warning(f"PostgreSQL order deletion not implemented for {order_id}")
        return False

    async def archive_order_to_postgres(self, db: AsyncSession, order_data: Dict[str, Any]) -> Optional[int]:
        """
        Archive order from Redis to PostgreSQL
        
        Args:
            db: Database session
            order_data: Order data to archive
            
        Returns:
            int: PostgreSQL order ID if successful, None otherwise
        """
        try:
            async with UnitOfWork(db) as uow:
                # Create order in PostgreSQL
                db_order = await uow.orders.create(
                    restaurant_id=order_data["restaurant_id"],
                    customer_name=order_data.get("customer_name"),
                    status=OrderStatus(order_data.get("status", "PENDING")),
                    subtotal=order_data.get("subtotal", 0.0),
                    tax_amount=order_data.get("tax_amount", 0.0),
                    total_amount=order_data.get("total_amount", 0.0)
                )
                
                # Archive order items if any
                for item in order_data.get("items", []):
                    await uow.order_items.create(
                        order_id=db_order.id,
                        menu_item_id=item["menu_item_id"],
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                        total_price=item["total_price"],
                        special_instructions=item.get("special_instructions")
                    )
            
            logger.info(f"Archived order {order_data.get('id')} to PostgreSQL order {db_order.id}")
            return db_order.id
            
        except Exception as e:
            logger.error(f"Failed to archive order to PostgreSQL: {e}")
            return None
