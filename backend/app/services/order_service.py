"""
Order service for managing orders with validation
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.order import Order, OrderStatus
from ..models.order_item import OrderItem
from ..core.unit_of_work import UnitOfWork
from .order_validator import OrderValidator
from .redis_service import RedisService
from ..constants.audio_phrases import AudioPhraseConstants, AudioPhraseType
from ..dto.order_result import OrderResult, OrderResultStatus
from ..core.config import settings
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderService:
    """
    Service for managing orders with validation
    Uses repositories for data access and validator for business logic
    """
    
    def __init__(self, redis_service: RedisService):
        # Business logic layer only depends on Redis and will create repositories as needed
        self.redis = redis_service
    
    
    async def handle_new_car(self, db: AsyncSession, restaurant_id: int, customer_name: Optional[str] = None) -> OrderResult:
        """
        Handle new car arriving (NEW_CAR event)
        
        If current session exists, cancel it first.
        Create new session and set as current.
        Generate greeting audio for the new session.
        
        Args:
            restaurant_id: Restaurant ID
            customer_name: Optional customer name
            
        Returns:
            OrderResult: Result with new session and greeting audio URL
        """
        try:
            if not self.redis or not await self.redis.ensure_connection():
                # Fallback to PostgreSQL
                logger.warning("Redis not available, falling back to PostgreSQL")
                return await self._create_db_order(db, restaurant_id, customer_name)
            
            # Check if current session exists and cancel it
            current_session = await self.redis.get("current:session")
            if current_session:
                logger.info(f"Cancelling existing session {current_session}")
                await self._cancel_session(current_session)
            
            # Create new session
            session_id = f"session_{int(datetime.now().timestamp() * 1000)}"
            
            # Set current session
            await self.redis.set("current:session", session_id, ttl=900)  # 15 minutes
            
            # Create session data
            session_data = {
                "id": session_id,
                "restaurant_id": restaurant_id,
                "customer_name": customer_name,
                "status": "NEW",
                "items": [],
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "total_amount": 0.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Store session data
            await self.redis.set(f"session:{session_id}", json.dumps(session_data), ttl=900)
            
            # Get greeting audio URL for this session
            greeting_audio_url = self._get_greeting_audio_url(restaurant_id, session_id)
            
            logger.info(f"Created new session {session_id} for restaurant {restaurant_id}")
            return OrderResult.success(
                f"New car session created",
                data={
                    "session": session_data,
                    "greeting_audio_url": greeting_audio_url
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to handle new car: {str(e)}")
            return OrderResult.error(f"Failed to handle new car: {str(e)}")
    
    async def handle_next_car(self) -> OrderResult:
        """
        Handle next car (NEXT_CAR event)
        
        Cancel current session and clear pointer.
        
        Returns:
            OrderResult: Result of operation
        """
        try:
            if not self.redis or not await self.redis.is_connected():
                return OrderResult.error("Redis not available")
            
            # Get current session
            current_session = await self.redis.get("current:session")
            if current_session:
                # Cancel current session
                await self._cancel_session(current_session)
            
            # Clear current session pointer
            await self.redis.delete("current:session")
            
            logger.info("Handled next car - cleared current session")
            return OrderResult.success("Next car handled - session cleared")
            
        except Exception as e:
            logger.error(f"Failed to handle next car: {str(e)}")
            return OrderResult.error(f"Failed to handle next car: {str(e)}")
    
    async def get_current_session(self) -> OrderResult:
        """
        Get current active session
        
        Returns:
            OrderResult: Result with current session data
        """
        try:
            if not self.redis or not await self.redis.is_connected():
                return OrderResult.error("Redis not available")
            
            # Get current session ID
            current_session = await self.redis.get("current:session")
            if not current_session:
                return OrderResult.error("No active session")
            
            # Get session data
            session_data = await self.redis.get(f"session:{current_session}")
            if not session_data:
                return OrderResult.error("Session data not found")
            
            try:
                session_json = json.loads(session_data)
                return OrderResult.success(
                    "Current session retrieved",
                    data={"session": session_json}
                )
            except json.JSONDecodeError:
                return OrderResult.error("Invalid session data")
            
        except Exception as e:
            logger.error(f"Failed to get current session: {str(e)}")
            return OrderResult.error(f"Failed to get current session: {str(e)}")
    
    async def update_session(self, db: AsyncSession, session_id: str, updates: Dict[str, Any]) -> OrderResult:
        """
        Update session data (ORDER_ACTIVITY event)
        
        Args:
            session_id: Session ID to update
            updates: Data to merge into session
            
        Returns:
            OrderResult: Result of update
        """
        try:
            if not self.redis or not await self.redis.is_connected():
                return OrderResult.error("Redis not available")
            
            # Check that this is the current session
            current_session = await self.redis.get("current:session")
            if current_session != session_id:
                logger.warning(f"Attempted to update stale session {session_id}")
                return OrderResult.error("Session is not current")
            
            # Get current session data
            session_data = await self.redis.get(f"session:{session_id}")
            if not session_data:
                return OrderResult.error("Session not found")
            
            try:
                session_json = json.loads(session_data)
            except json.JSONDecodeError:
                return OrderResult.error("Invalid session data")
            
            # Merge updates
            session_json.update(updates)
            session_json["updated_at"] = datetime.now().isoformat()
            
            # Check if status changed to COMPLETED
            if session_json.get("status") == "COMPLETED":
                # Archive to PostgreSQL
                archive_result = await self._archive_session_to_db(db, session_json)
                if archive_result.success:
                    # Clean up Redis
                    await self.redis.delete("current:session")
                    await self.redis.delete(f"session:{session_id}")
                    return archive_result
            
            # Update session in Redis with refreshed TTL
            await self.redis.set(f"session:{session_id}", json.dumps(session_json), ttl=900)
            
            logger.info(f"Updated session {session_id}")
            return OrderResult.success(
                "Session updated successfully",
                data={"session": session_json}
            )
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {str(e)}")
            return OrderResult.error(f"Failed to update session: {str(e)}")
    
    async def _cancel_session(self, session_id: str):
        """
        Cancel a session (mark as CANCELLED)
        
        Args:
            session_id: Session ID to cancel
        """
        try:
            # Get session data
            session_data = await self.redis.get(f"session:{session_id}")
            if session_data:
                try:
                    session_json = json.loads(session_data)
                    session_json["status"] = "CANCELLED"
                    session_json["updated_at"] = datetime.now().isoformat()
                    
                    # Update session
                    await self.redis.set(f"session:{session_id}", json.dumps(session_json), ttl=900)
                    
                    # Optionally archive cancellation for analytics
                    # await self._archive_session_to_db(session_json)
                    
                    logger.info(f"Cancelled session {session_id}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid session data for {session_id}")
            
            # Delete session
            await self.redis.delete(f"session:{session_id}")
            
        except Exception as e:
            logger.error(f"Failed to cancel session {session_id}: {str(e)}")
    
    async def _archive_session_to_db(self, db: AsyncSession, session_data: Dict[str, Any]) -> OrderResult:
        """
        Archive session to PostgreSQL
        
        Args:
            session_data: Session data to archive
            
        Returns:
            OrderResult: Result of archiving
        """
        try:
            async with UnitOfWork(db) as uow:
                # Create order in PostgreSQL
                db_order = await uow.orders.create(
                restaurant_id=session_data["restaurant_id"],
                customer_name=session_data.get("customer_name"),
                status=OrderStatus(session_data["status"]),
                subtotal=session_data["subtotal"],
                tax_amount=session_data["tax_amount"],
                total_amount=session_data["total_amount"]
            )
            
            logger.info(f"Archived session {session_data['id']} to PostgreSQL order {db_order.id}")
            return OrderResult.success(
                "Session archived successfully",
                data={"order": db_order.to_dict()}
            )
            
        except Exception as e:
            logger.error(f"Failed to archive session: {str(e)}")
            return OrderResult.error(f"Failed to archive session: {str(e)}")
    
    async def _create_redis_order(self, restaurant_id: int, customer_name: Optional[str] = None) -> OrderResult:
        """Create order in Redis"""
        try:
            # Generate unique order ID
            order_id = f"redis_{int(datetime.now().timestamp() * 1000)}"
            
            # Create order data
            order_data = {
                "id": order_id,
                "restaurant_id": restaurant_id,
                "customer_name": customer_name,
                "customer_phone": None,
                "user_id": None,
                "status": OrderStatus.PENDING.value,
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "total_amount": 0.0,
                "special_instructions": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "items": []
            }
            
            # Store in Redis with 30-minute TTL
            success = await self.redis.set_order(order_id, order_data, ttl=1800)
            if not success:
                raise Exception("Failed to store order in Redis")
            
            logger.info(f"Created Redis order {order_id} for restaurant {restaurant_id}")
            return OrderResult.success(
                f"Order {order_id} created successfully",
                data={"order": order_data}
            )
            
        except Exception as e:
            logger.error(f"Failed to create Redis order: {str(e)}")
            # Fallback to PostgreSQL
            return await self._create_db_order(db, restaurant_id, customer_name)
    
    async def _create_db_order(self, db: AsyncSession, restaurant_id: int, customer_name: Optional[str] = None) -> OrderResult:
        """Create order in PostgreSQL using Unit of Work pattern"""
        try:
            async with UnitOfWork(db) as uow:
                # Create new order in database
                order = await uow.orders.create(
                    restaurant_id=restaurant_id,
                    customer_name=customer_name,
                    status=OrderStatus.PENDING,
                    subtotal=0,
                    tax_amount=0,
                    total_amount=0
                )
                
                logger.info(f"Created PostgreSQL order {order.id} for restaurant {restaurant_id}")
                return OrderResult.success(
                    f"Order {order.id} created successfully",
                    data={"order": order.to_dict()}
                )
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL order: {str(e)}")
            return OrderResult.error(f"Failed to create order: {str(e)}")
    
    async def get_order(self, db: AsyncSession, order_id: str) -> OrderResult:
        """
        Get order by ID (Redis first, PostgreSQL fallback)
        
        Args:
            order_id: Order ID (can be Redis or PostgreSQL ID)
            
        Returns:
            OrderResult: Result with order data
        """
        try:
            # Try Redis first if it's a Redis order ID
            if order_id.startswith("redis_") and self.redis and await self.redis.is_connected():
                redis_order = await self.redis.get_order(order_id)
                if redis_order:
                    logger.info(f"Retrieved Redis order {order_id}")
                    return OrderResult.success(
                        "Order retrieved successfully",
                        data={"order": redis_order}
                    )
            
            # Try PostgreSQL (for both Redis and DB orders)
            try:
                async with UnitOfWork(db) as uow:
                    db_order = await uow.orders.get_by_id(int(order_id))
                if db_order:
                    logger.info(f"Retrieved PostgreSQL order {order_id}")
                    return OrderResult.success(
                        "Order retrieved successfully",
                        data={"order": db_order.to_dict()}
                    )
            except ValueError:
                # order_id is not a valid integer, skip PostgreSQL lookup
                pass
            
            return OrderResult.error(f"Order {order_id} not found")
            
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {str(e)}")
            return OrderResult.error(f"Failed to get order: {str(e)}")
    
    async def archive_order(self, db: AsyncSession, order_id: str) -> OrderResult:
        """
        Archive order from Redis to PostgreSQL
        
        Args:
            order_id: Redis order ID to archive
            
        Returns:
            OrderResult: Result of archiving operation
        """
        try:
            if not order_id.startswith("redis_"):
                return OrderResult.error("Can only archive Redis orders")
            
            # Get order from Redis
            redis_order = await self.redis.get_order(order_id)
            if not redis_order:
                return OrderResult.error(f"Redis order {order_id} not found")
            
            async with UnitOfWork(db) as uow:
                # Create order in PostgreSQL
                db_order = await uow.orders.create(
                restaurant_id=redis_order["restaurant_id"],
                customer_name=redis_order["customer_name"],
                customer_phone=redis_order["customer_phone"],
                user_id=redis_order["user_id"],
                status=OrderStatus(redis_order["status"]),
                subtotal=redis_order["subtotal"],
                tax_amount=redis_order["tax_amount"],
                total_amount=redis_order["total_amount"],
                special_instructions=redis_order["special_instructions"]
            )
            
            # Archive order items if any
            for item in redis_order.get("items", []):
                await uow.order_items.create(
                    order_id=db_order.id,
                    menu_item_id=item["menu_item_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["total_price"],
                    special_instructions=item.get("special_instructions")
                )
            
            # Delete from Redis
            await self.redis.delete_order(order_id)
            
            logger.info(f"Archived Redis order {order_id} to PostgreSQL order {db_order.id}")
            return OrderResult.success(
                f"Order archived successfully",
                data={"order": db_order.to_dict()}
            )
            
        except Exception as e:
            logger.error(f"Failed to archive order {order_id}: {str(e)}")
            return OrderResult.error(f"Failed to archive order: {str(e)}")
    
    async def update_order_status(self, db: AsyncSession, order_id: str, status: OrderStatus) -> OrderResult:
        """
        Update order status (Redis or PostgreSQL)
        
        Args:
            order_id: Order ID
            status: New status
            
        Returns:
            OrderResult: Result of update operation
        """
        try:
            # Try Redis first
            if order_id.startswith("redis_") and self.redis and await self.redis.is_connected():
                redis_order = await self.redis.get_order(order_id)
                if redis_order:
                    # Update Redis order
                    redis_order["status"] = status.value
                    redis_order["updated_at"] = datetime.now().isoformat()
                    
                    success = await self.redis.set_order(order_id, redis_order, ttl=1800)
                    if success:
                        logger.info(f"Updated Redis order {order_id} status to {status.value}")
                        
                        # Archive to PostgreSQL if order is completed or cancelled
                        if status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                            return await self.archive_order(db, order_id)
                        
                        return OrderResult.success(
                            f"Order status updated to {status.value}",
                            data={"order": redis_order}
                        )
            
            # Try PostgreSQL
            try:
                async with UnitOfWork(db) as uow:
                    db_order = await uow.orders.get_by_id(int(order_id))
                if db_order:
                    db_order.status = status
                    # Let the repository handle the commit
                    
                    logger.info(f"Updated PostgreSQL order {order_id} status to {status.value}")
                    return OrderResult.success(
                        f"Order status updated to {status.value}",
                        data={"order": db_order.to_dict()}
                    )
            except ValueError:
                pass
            
            return OrderResult.error(f"Order {order_id} not found")
            
        except Exception as e:
            logger.error(f"Failed to update order status: {str(e)}")
            return OrderResult.error(f"Failed to update order status: {str(e)}")
    
    async def _restore_inventory(self, db: AsyncSession, menu_item_id: int, quantity: int):
        """
        Restore inventory when removing an item from order
        
        Args:
            menu_item_id: Menu item ID
            quantity: Quantity being removed
        """
        async with UnitOfWork(db) as uow:
            # Get menu item ingredients
            menu_item_ingredients = await uow.menu_item_ingredients.get_by_menu_item(menu_item_id)
        
            for menu_item_ingredient in menu_item_ingredients:
                if not menu_item_ingredient.ingredient:
                    continue
                
                # Get inventory
                inventory = await uow.inventory.get_by_ingredient(menu_item_ingredient.ingredient_id)
                if not inventory:
                    continue
                
                # Calculate quantity to restore
                quantity_to_restore = float(menu_item_ingredient.quantity) * quantity
                
                # Update inventory
                new_stock = float(inventory.current_stock) + quantity_to_restore
                await uow.inventory.update(inventory.id, current_stock=new_stock)
    
    def _get_greeting_audio_url(self, restaurant_id: int, session_id: str) -> Optional[str]:
        """
        Get greeting audio URL for a new session using existing canned audio files
        
        Args:
            restaurant_id: Restaurant ID
            session_id: Session ID
            
        Returns:
            str: URL to the greeting audio file, or None if not available
        """
        try:
            # Use restaurant slug for audio organization
            # For now, use a simple restaurant slug based on ID
            restaurant_slug = f"restaurant_{restaurant_id}"
            
            # Get the blob path for the greeting audio file
            blob_path = AudioPhraseConstants.get_blob_path(AudioPhraseType.GREETING, restaurant_slug)
            
            # Construct the URL to the existing canned audio file
            # This assumes the files are accessible via HTTP (LocalStack S3 or real S3)
            endpoint_url = os.getenv('AWS_ENDPOINT_URL')
            bucket_name = os.getenv('S3_BUCKET_NAME', 'ai-drivethru-files')
            
            if endpoint_url:
                # LocalStack or custom endpoint
                greeting_url = f"{endpoint_url}/{bucket_name}/{blob_path}"
            else:
                # Real AWS S3
                region = os.getenv('AWS_REGION', 'us-east-1')
                greeting_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{blob_path}"
            
            # TODO: Add file existence check here to return None if file doesn't exist
            # For now, we'll return the URL and let the frontend handle 404s gracefully
            logger.info(f"Using greeting audio URL for session {session_id}: {greeting_url}")
            return greeting_url
                
        except Exception as e:
            logger.error(f"Failed to get greeting audio URL: {str(e)}")
            return None
