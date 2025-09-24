"""
Order service for managing orders with validation
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.order import Order, OrderStatus
from ..models.order_item import OrderItem
from ..core.unit_of_work import UnitOfWork
from .order_validator import OrderValidator
from .order_session_interface import OrderSessionInterface
from .customization_validation_service import CustomizationValidationService
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
    
    def __init__(self, order_session_service: OrderSessionInterface, customization_validator: CustomizationValidationService):
        # Business logic layer uses OrderSessionService for all storage operations
        self.storage = order_session_service
        self.customization_validator = customization_validator
    
    
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
            # Check if current session exists and cancel it
            current_session = await self.storage.get_current_session_id()
            if current_session:
                logger.info(f"Cancelling existing session {current_session}")
                await self._cancel_session(current_session)
            
            # Create new session
            session_id = f"session_{int(datetime.now().timestamp() * 1000)}"
            
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
            
            # Create session using OrderSessionService
            session_created = await self.storage.create_session(session_data, ttl=900)
            if not session_created:
                # Fallback to PostgreSQL if session creation failed
                logger.warning("Failed to create session in storage, falling back to PostgreSQL")
                return await self._create_db_order(db, restaurant_id, customer_name)
            
            # Set current session
            await self.storage.set_current_session_id(session_id)
            
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
            # Get current session
            current_session = await self.storage.get_current_session_id()
            if current_session:
                # Cancel current session
                await self._cancel_session(current_session)
            
            # Clear current session pointer
            await self.storage.clear_current_session_id()
            
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
            # Get current session ID
            current_session = await self.storage.get_current_session_id()
            if not current_session:
                return OrderResult.error("No active session")
            
            # Get session data
            session_data = await self.storage.get_session(current_session)
            if not session_data:
                return OrderResult.error("Session data not found")
            
            return OrderResult.success(
                "Current session retrieved",
                data={"session": session_data}
            )
            
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
            # Check that this is the current session
            current_session = await self.storage.get_current_session_id()
            if current_session != session_id:
                logger.warning(f"Attempted to update stale session {session_id}")
                return OrderResult.error("Session is not current")
            
            # Check if status changed to COMPLETED
            if updates.get("status") == "COMPLETED":
                # Get current session data for archiving
                session_data = await self.storage.get_session(session_id)
                if session_data:
                    # Archive to PostgreSQL
                    archive_result = await self._archive_session_to_db(db, session_data)
                    if archive_result.success:
                        # Clean up storage
                        await self.storage.clear_current_session_id()
                        await self.storage.delete_session(session_id)
                        return archive_result
            
            # Update session using OrderSessionService
            update_success = await self.storage.update_session(session_id, updates, ttl=900)
            if not update_success:
                return OrderResult.error("Failed to update session")
            
            # Get updated session data for response
            updated_session = await self.storage.get_session(session_id)
            
            logger.info(f"Updated session {session_id}")
            return OrderResult.success(
                "Session updated successfully",
                data={"session": updated_session}
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
            # Get session data and mark as cancelled
            session_data = await self.storage.get_session(session_id)
            if session_data:
                session_data["status"] = "CANCELLED"
                session_data["updated_at"] = datetime.now().isoformat()
                
                # Update session
                await self.storage.update_session(session_id, {"status": "CANCELLED"}, ttl=900)
                
                # Optionally archive cancellation for analytics
                # await self._archive_session_to_db(session_data)
                
                logger.info(f"Cancelled session {session_id}")
            
            # Delete session
            await self.storage.delete_session(session_id)
            
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
            # TODO: REFACTOR - Consolidate PostgreSQL order creation logic
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
    
    
    async def _create_db_order(self, db: AsyncSession, restaurant_id: int, customer_name: Optional[str] = None) -> OrderResult:
        """Create order in PostgreSQL using OrderSessionService"""
        try:
            # Generate unique order ID
            order_id = f"db_{int(datetime.now().timestamp() * 1000)}"
            
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
            
            # Create order using OrderSessionService (will fallback to PostgreSQL)
            success = await self.storage.create_order(db, order_data)
            if success:
                logger.info(f"Created PostgreSQL order for restaurant {restaurant_id}")
                return OrderResult.success(
                    f"Order created successfully",
                    data={"order": order_data}
                )
            else:
                return OrderResult.error("Failed to create order")
            
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
            # Use OrderSessionService for unified Redis/PostgreSQL fallback
            order_data = await self.storage.get_order(db, order_id)
            if order_data:
                return OrderResult.success(
                    "Order retrieved successfully",
                    data={"order": order_data}
                )
            
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
            
            # Get order from storage
            redis_order = await self.storage.get_order(db, order_id)
            if not redis_order:
                return OrderResult.error(f"Redis order {order_id} not found")
            
            # Archive to PostgreSQL using OrderSessionService
            postgres_order_id = await self.storage.archive_order_to_postgres(db, redis_order)
            if not postgres_order_id:
                return OrderResult.error("Failed to archive order to PostgreSQL")
            
            # Delete from Redis
            await self.storage.delete_order(db, order_id)
            
            logger.info(f"Archived Redis order {order_id} to PostgreSQL order {postgres_order_id}")
            return OrderResult.success(
                f"Order archived successfully",
                data={"order_id": postgres_order_id}
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
            # Update order using OrderSessionService
            updates = {
                "status": status.value,
                "updated_at": datetime.now().isoformat()
            }
            
            update_success = await self.storage.update_order(db, order_id, updates, ttl=1800)
            if not update_success:
                return OrderResult.error(f"Order {order_id} not found")
            
            # Archive to PostgreSQL if order is completed or cancelled
            if status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED] and order_id.startswith("redis_"):
                return await self.archive_order(db, order_id)
            
            # Get updated order data for response
            updated_order = await self.storage.get_order(db, order_id)
            
            logger.info(f"Updated order {order_id} status to {status.value}")
            return OrderResult.success(
                f"Order status updated to {status.value}",
                data={"order": updated_order}
            )
            
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
            # Use the same path structure as the import script: restaurants/{id}/audio/{filename}
            blob_path = f"restaurants/{restaurant_id}/audio/greeting.mp3"
            
            # Construct the URL to the existing canned audio file
            # This assumes the files are accessible via HTTP (LocalStack S3 or real S3)
            endpoint_url = os.getenv('AWS_ENDPOINT_URL')
            bucket_name = os.getenv('S3_BUCKET_NAME', 'ai-drivethru-files')
            
            if endpoint_url:
                # LocalStack or custom endpoint
                greeting_url = f"{endpoint_url}/{bucket_name}/{blob_path}"
            else:
                # Real AWS S3 - use S3_REGION instead of AWS_REGION
                region = os.getenv('S3_REGION', 'us-east-1')
                greeting_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{blob_path}"
            
            # TODO: Add file existence check here to return None if file doesn't exist
            # For now, we'll return the URL and let the frontend handle 404s gracefully
            logger.info(f"Using greeting audio URL for session {session_id}: {greeting_url}")
            return greeting_url
                
        except Exception as e:
            logger.error(f"Failed to get greeting audio URL: {str(e)}")
            return None
    
    # ============================================================================
    # CART OPERATION METHODS - Called by Commands
    # These methods handle adding, removing, and modifying items in orders
    # ============================================================================
    
    async def add_item_to_order(
        self, 
        db: AsyncSession,
        order_id: str, 
        menu_item_id: int, 
        quantity: int, 
        customizations: Optional[List[str]] = None, 
        special_instructions: Optional[str] = None,
        size: Optional[str] = None
    ) -> OrderResult:
        """
        Add item to order - called by AddItemCommand
        Uses OrderSessionService for Redis/PostgreSQL fallback
        
        Args:
            db: Database session
            order_id: Order ID to add item to
            menu_item_id: Menu item ID to add
            quantity: Quantity to add
            customizations: List of modifiers/customizations
            special_instructions: Special cooking instructions
            size: Item size (e.g., "Large", "Small")
            
        Returns:
            OrderResult: Result with order_item data and comprehensive message
        """
        try:
            # 1. Get menu item details from database
            menu_item_details = await self._get_menu_item_details(db, menu_item_id)
            if not menu_item_details:
                return OrderResult.error(f"Menu item {menu_item_id} not found or not available")
            
            # 2. Get current order from storage (Redis first, PostgreSQL fallback)
            order_data = await self.storage.get_order(db, order_id)
            if not order_data:
                # Create new order if it doesn't exist
                order_data = {
                    "id": order_id,
                    "items": [],
                    "subtotal": 0.0,
                    "tax_amount": 0.0,
                    "total_amount": 0.0,
                    "status": "ACTIVE",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            
            # 3. Validate customizations if provided
            extra_cost = 0.0
            if customizations:
                # Get restaurant_id from menu item details
                restaurant_id = menu_item_details.get("restaurant_id")
                if not restaurant_id:
                    return OrderResult.error("Cannot validate customizations - restaurant ID not found")
                
                # Create UnitOfWork for validation
                uow = UnitOfWork(db)
                
                # Validate customizations
                validation_results = await self.customization_validator.validate_customizations(
                    menu_item_id, customizations, restaurant_id, uow
                )
                
                # Check for validation errors
                validation_errors = []
                for customization, result in validation_results.items():
                    if not result.is_valid:
                        validation_errors.extend(result.errors)
                    else:
                        extra_cost += result.extra_cost
                
                if validation_errors:
                    return OrderResult.error(f"Invalid customizations: {'; '.join(validation_errors)}")
            
            # 4. Create order item with unique ID
            order_item_id = await self._generate_order_item_id()
            base_price = menu_item_details["price"]
            total_item_price = (base_price + extra_cost) * quantity
            
            order_item = {
                "id": order_item_id,
                "menu_item_id": menu_item_id,
                "menu_item": menu_item_details,
                "quantity": quantity,
                "unit_price": base_price,
                "extra_cost": extra_cost,
                "total_price": total_item_price,
                "customizations": customizations or [],
                "special_instructions": special_instructions,
                "created_at": datetime.now().isoformat()
            }
            
            # 5. Add to order items list
            order_data["items"].append(order_item)
            
            # 6. Recalculate totals (subtotal, tax, total)
            await self._recalculate_order_totals(order_data)
            
            # 7. Update timestamp
            order_data["updated_at"] = datetime.now().isoformat()
            
            # 8. Save updated order to storage (Redis/PostgreSQL)
            save_success = await self.storage.update_order(db, order_id, order_data, ttl=1800)
            if not save_success:
                return OrderResult.error("Failed to save updated order")
            
            # 9. Generate comprehensive message
            message = self._generate_add_item_message(
                quantity, menu_item_details, customizations, size, special_instructions
            )
            
            # 10. Return OrderResult with order_item data
            logger.info(f"Added {quantity}x {menu_item_details['name']} to order {order_id}")
            return OrderResult.success(
                message,
                data={
                    "order_item": order_item,
                    "order": order_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to add item to order: {str(e)}")
            return OrderResult.error(f"Failed to add item to order: {str(e)}")
    
    async def remove_item_from_order(
        self, 
        db: AsyncSession,
        order_id: str, 
        order_item_id: str
    ) -> OrderResult:
        """
        Remove item from order - called by RemoveItemCommand
        Uses OrderSessionService for Redis/PostgreSQL fallback
        
        Args:
            db: Database session
            order_id: Order ID to remove item from
            order_item_id: ID of the order item to remove (resolved from target_ref)
            
        Returns:
            OrderResult: Result of item removal
        """
        try:
            # 1. Get current order from storage (Redis first, PostgreSQL fallback)
            order_data = await self.storage.get_order(db, order_id)
            if not order_data:
                return OrderResult.error(f"Order {order_id} not found")
            
            # 2. Find order item by order_item_id
            items = order_data.get("items", [])
            item_to_remove = None
            item_index = -1
            
            for i, item in enumerate(items):
                if item.get("id") == order_item_id:
                    item_to_remove = item
                    item_index = i
                    break
            
            if not item_to_remove:
                return OrderResult.error(f"Order item {order_item_id} not found in order")
            
            # 3. Remove item from order items list
            removed_item = items.pop(item_index)
            order_data["items"] = items
            
            # 4. Recalculate order totals (subtotal, tax, total)
            await self._recalculate_order_totals(order_data)
            
            # 5. Update timestamp
            order_data["updated_at"] = datetime.now().isoformat()
            
            # 6. Save updated order to storage (Redis/PostgreSQL)
            save_success = await self.storage.update_order(db, order_id, order_data, ttl=1800)
            if not save_success:
                return OrderResult.error("Failed to save updated order")
            
            # 7. Return OrderResult with success message
            item_name = removed_item.get("menu_item", {}).get("name", "item")
            logger.info(f"Removed {item_name} from order {order_id}")
            return OrderResult.success(
                f"Removed {item_name} from order",
                data={
                    "removed_item": removed_item,
                    "order": order_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to remove item from order: {str(e)}")
            return OrderResult.error(f"Failed to remove item from order: {str(e)}")
    
    async def modify_order_item(
        self, 
        db: AsyncSession,
        order_id: str, 
        order_item_id: str,
        changes: Dict[str, Any]
    ) -> OrderResult:
        """
        Modify an existing order item - called by ModifyItemCommand
        Uses OrderSessionService for Redis/PostgreSQL fallback
        
        Args:
            db: Database session
            order_id: Order ID containing the item
            order_item_id: ID of the order item to modify (resolved from target_ref)
            changes: Dictionary of changes to apply (e.g., {"remove_modifier": "onions"})
            
        Returns:
            OrderResult: Result of modifying the item
        """
        try:
            # 1. Get current order from storage (Redis first, PostgreSQL fallback)
            order_data = await self.storage.get_order(db, order_id)
            if not order_data:
                return OrderResult.error(f"Order {order_id} not found")
            
            # 2. Find order item by order_item_id
            items = order_data.get("items", [])
            item_to_modify = None
            item_index = -1
            
            for i, item in enumerate(items):
                if item.get("id") == order_item_id:
                    item_to_modify = item
                    item_index = i
                    break
            
            if not item_to_modify:
                return OrderResult.error(f"Order item {order_item_id} not found in order")
            
            # 3. Apply changes to the item
            changes_applied = []
            
            for change_op, change_value in changes.items():
                if change_op == "remove_modifier":
                    # Remove a modifier from customizations
                    customizations = item_to_modify.get("customizations", [])
                    if change_value in customizations:
                        customizations.remove(change_value)
                        item_to_modify["customizations"] = customizations
                        changes_applied.append(f"removed {change_value}")
                
                elif change_op == "add_modifier":
                    # Add a modifier to customizations
                    customizations = item_to_modify.get("customizations", [])
                    if change_value not in customizations:
                        customizations.append(change_value)
                        item_to_modify["customizations"] = customizations
                        changes_applied.append(f"added {change_value}")
                
                elif change_op == "set_special_instructions":
                    # Update special instructions
                    item_to_modify["special_instructions"] = change_value
                    changes_applied.append(f"special instructions to: {change_value}")
                
                elif change_op == "clear_special_instructions":
                    # Clear special instructions
                    item_to_modify["special_instructions"] = None
                    changes_applied.append("cleared special instructions")
                
                elif change_op == "set_size":
                    # Update item size (if supported by menu item)
                    item_to_modify["size"] = change_value
                    changes_applied.append(f"size to {change_value}")
                
                else:
                    # Generic change - just store it
                    item_to_modify[change_op] = change_value
                    changes_applied.append(f"{change_op} to {change_value}")
            
            # 4. Update the item in the list
            items[item_index] = item_to_modify
            order_data["items"] = items
            
            # 5. Update timestamp
            order_data["updated_at"] = datetime.now().isoformat()
            
            # 6. Save updated order to storage (Redis/PostgreSQL)
            save_success = await self.storage.update_order(db, order_id, order_data, ttl=1800)
            if not save_success:
                return OrderResult.error("Failed to save updated order")
            
            # 7. Return OrderResult with success message
            item_name = item_to_modify.get("menu_item", {}).get("name", "item")
            logger.info(f"Modified {item_name} in order {order_id}: {', '.join(changes_applied)}")
            return OrderResult.success(
                f"Modified {item_name}: {', '.join(changes_applied)}",
                data={
                    "modified_item": item_to_modify,
                    "changes_applied": changes_applied,
                    "order": order_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to modify item: {str(e)}")
            return OrderResult.error(f"Failed to modify item: {str(e)}")
    
    async def update_order_item_quantity(
        self, 
        db: AsyncSession,
        order_id: str, 
        order_item_id: str, 
        quantity: int
    ) -> OrderResult:
        """
        Update item quantity - called by SetQuantityCommand
        Uses OrderSessionService for Redis/PostgreSQL fallback
        
        Args:
            db: Database session
            order_id: Order ID containing the item
            order_item_id: ID of the order item to update (resolved from target_ref)
            quantity: New quantity
            
        Returns:
            OrderResult: Result of quantity update
        """
        try:
            # 1. Get current order from storage (Redis first, PostgreSQL fallback)
            order_data = await self.storage.get_order(db, order_id)
            if not order_data:
                return OrderResult.error(f"Order {order_id} not found")
            
            # 2. Find order item by order_item_id
            items = order_data.get("items", [])
            item_to_update = None
            item_index = -1
            
            for i, item in enumerate(items):
                if item.get("id") == order_item_id:
                    item_to_update = item
                    item_index = i
                    break
            
            if not item_to_update:
                return OrderResult.error(f"Order item {order_item_id} not found in order")
            
            # 3. Update quantity on the order item
            old_quantity = item_to_update.get("quantity", 0)
            item_to_update["quantity"] = quantity
            
            # 4. Recalculate item total and order totals (subtotal, tax, total)
            unit_price = item_to_update.get("unit_price", 0.0)
            item_to_update["total_price"] = unit_price * quantity
            
            # Update the item in the list
            items[item_index] = item_to_update
            order_data["items"] = items
            
            # Recalculate overall order totals
            await self._recalculate_order_totals(order_data)
            
            # 5. Update timestamp
            order_data["updated_at"] = datetime.now().isoformat()
            
            # 6. Save updated order to storage (Redis/PostgreSQL)
            save_success = await self.storage.update_order(db, order_id, order_data, ttl=1800)
            if not save_success:
                return OrderResult.error("Failed to save updated order")
            
            # 7. Return OrderResult with success message
            item_name = item_to_update.get("menu_item", {}).get("name", "item")
            logger.info(f"Updated {item_name} quantity from {old_quantity} to {quantity} in order {order_id}")
            return OrderResult.success(
                f"Updated {item_name} quantity to {quantity}",
                data={
                    "updated_item": item_to_update,
                    "order": order_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update item quantity: {str(e)}")
            return OrderResult.error(f"Failed to update item quantity: {str(e)}")
    
    async def clear_order(
        self, 
        db: AsyncSession,
        order_id: str
    ) -> OrderResult:
        """
        Clear all items from order - called by ClearOrderCommand
        Uses OrderSessionService for Redis/PostgreSQL fallback
        
        Args:
            db: Database session
            order_id: Order ID to clear
            
        Returns:
            OrderResult: Result of clearing order
        """
        try:
            # 1. Get current order from storage (Redis first, PostgreSQL fallback)
            order_data = await self.storage.get_order(db, order_id)
            if not order_data:
                return OrderResult.error(f"Order {order_id} not found")
            
            # 2. Clear items list from order
            item_count = len(order_data.get("items", []))
            order_data["items"] = []
            
            # 3. Reset totals to 0 (subtotal, tax, total)
            order_data["subtotal"] = 0.0
            order_data["tax_amount"] = 0.0
            order_data["total_amount"] = 0.0
            
            # 4. Update timestamp
            order_data["updated_at"] = datetime.now().isoformat()
            
            # 5. Save updated order to storage (Redis/PostgreSQL)
            save_success = await self.storage.update_order(db, order_id, order_data, ttl=1800)
            if not save_success:
                return OrderResult.error("Failed to save updated order")
            
            # 6. Return OrderResult with success message
            logger.info(f"Cleared {item_count} items from order {order_id}")
            return OrderResult.success(
                f"Cleared all {item_count} items from order",
                data={
                    "cleared_item_count": item_count,
                    "order": order_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to clear order: {str(e)}")
            return OrderResult.error(f"Failed to clear order: {str(e)}")
    
    async def confirm_order(
        self, 
        db: AsyncSession,
        order_id: str
    ) -> OrderResult:
        """
        Confirm order - called by ConfirmOrderCommand
        Uses OrderSessionService for Redis/PostgreSQL fallback
        
        Args:
            db: Database session
            order_id: Order ID to confirm
            
        Returns:
            OrderResult: Result of order confirmation
        """
        try:
            # 1. Get current order from storage (Redis first, PostgreSQL fallback)
            order_data = await self.storage.get_order(db, order_id)
            if not order_data:
                return OrderResult.error(f"Order {order_id} not found")
            
            # 2. Validate order has items
            items = order_data.get("items", [])
            if not items:
                return OrderResult.error("Cannot confirm empty order. Please add items first.")
            
            # 3. Update order status to confirmed
            order_data["status"] = "CONFIRMED"
            order_data["confirmed_at"] = datetime.now().isoformat()
            order_data["updated_at"] = datetime.now().isoformat()
            
            # 4. Save updated order to storage (Redis/PostgreSQL)
            save_success = await self.storage.update_order(db, order_id, order_data, ttl=1800)
            if not save_success:
                return OrderResult.error("Failed to save confirmed order")
            
            # 5. Optionally trigger archival process to PostgreSQL
            # For now, we'll keep it in Redis until explicitly archived
            
            # 6. Return OrderResult with confirmation data
            item_count = sum(item.get("quantity", 0) for item in items)
            total_amount = order_data.get("total_amount", 0.0)
            
            logger.info(f"Confirmed order {order_id} with {item_count} items, total: ${total_amount:.2f}")
            return OrderResult.success(
                f"Order confirmed! {item_count} items, total: ${total_amount:.2f}. Please pull forward to the window.",
                data={
                    "order_confirmed": True,
                    "item_count": item_count,
                    "total_amount": total_amount,
                    "order_status": "confirmed",
                    "order": order_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to confirm order: {str(e)}")
            return OrderResult.error(f"Failed to confirm order: {str(e)}")
    
    # ============================================================================
    # HELPER METHODS FOR CART OPERATIONS
    # ============================================================================
    
    async def _get_menu_item_details(self, db: AsyncSession, menu_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get menu item details - helper method for cart operations
        
        Args:
            db: Database session
            menu_item_id: Menu item ID
            
        Returns:
            Dict with menu item details or None if not found
        """
        try:
            async with UnitOfWork(db) as uow:
                menu_item = await uow.menu_items.get_by_id(menu_item_id)
                if not menu_item:
                    return None
                
                if not menu_item.is_available:
                    return None
                
                return {
                    "id": menu_item.id,
                    "name": menu_item.name,
                    "price": float(menu_item.price),
                    "description": menu_item.description,
                    "is_available": menu_item.is_available,
                    "restaurant_id": menu_item.restaurant_id
                }
        except Exception as e:
            logger.error(f"Failed to get menu item details for {menu_item_id}: {str(e)}")
            return None
    
    async def _recalculate_order_totals(self, order_data: Dict[str, Any]) -> None:
        """
        Recalculate order totals - helper method for cart operations
        
        Args:
            order_data: Order data to recalculate totals for
            
        Note: Tax calculation is simplified for now. Future enhancement will use
        a strategy pattern to support different tax rules per restaurant/location.
        """
        try:
            items = order_data.get("items", [])
            subtotal = 0.0
            
            # Sum up all item totals
            for item in items:
                item_total = item.get("quantity", 0) * item.get("unit_price", 0.0)
                subtotal += item_total
                item["total_price"] = item_total
            
            # Apply taxes (simple for now - will be replaced with strategy pattern later)
            tax_amount = 0.0  # No taxes for now - keep it simple
            total_amount = subtotal + tax_amount
            
            # Update order totals
            order_data["subtotal"] = round(subtotal, 2)
            order_data["tax_amount"] = round(tax_amount, 2)
            order_data["total_amount"] = round(total_amount, 2)
            
        except Exception as e:
            logger.error(f"Failed to recalculate order totals: {str(e)}")
            raise
    
    async def _generate_order_item_id(self) -> str:
        """
        Generate unique order item ID - helper method for cart operations
        
        Returns:
            Unique order item ID
        """
        import time
        import random
        # Generate unique ID using timestamp and random number
        timestamp = int(time.time() * 1000)  # milliseconds
        random_part = random.randint(1000, 9999)
        return f"item_{timestamp}_{random_part}"
    
    def _generate_add_item_message(
        self, 
        quantity: int, 
        menu_item_details: Dict[str, Any], 
        customizations: Optional[List[str]] = None,
        size: Optional[str] = None,
        special_instructions: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive message for adding item to order
        
        Args:
            quantity: Quantity being added
            menu_item_details: Menu item details from database
            customizations: List of customizations/modifiers
            size: Item size (e.g., "Large", "Small")
            special_instructions: Special cooking instructions
            
        Returns:
            Formatted message string
        """
        item_name = menu_item_details.get("name", "item")
        
        # Build size text (avoid redundancy if size is already in item name)
        size_text = ""
        if size and size.lower() not in item_name.lower():
            size_text = f" {size}"
        
        # Build customizations text
        customizations_text = ""
        if customizations:
            customizations_text = f" ({', '.join(customizations)})"
        
        # Build special instructions text
        special_text = ""
        if special_instructions:
            special_text = f" - {special_instructions}"
        
        # Construct the message
        message = f"Added {quantity}x {item_name}{size_text}{customizations_text} to order{special_text}"
        
        return message
