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
from ..models.session_models import ConversationSessionData
from ..agents.state import ConversationWorkflowState
from ..core.state_machine import ConversationState, OrderState, ConversationContext
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

    # =============================================================================
    # WORKFLOW STATE METHODS - New methods for ConversationWorkflow integration
    # =============================================================================

    async def get_conversation_workflow_state(self, session_id: str, user_input: str) -> ConversationWorkflowState:
        """
        Get session data and convert to ConversationWorkflowState for workflow processing.
        
        Args:
            session_id: Session ID to retrieve
            user_input: User's speech input for this turn
            
        Returns:
            ConversationWorkflowState: Workflow state ready for processing
            
        Raises:
            ValueError: If session doesn't exist or is invalid
        """
        # Get session data from Redis
        session_data = await self.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        # Validate session data structure
        try:
            validated_session = ConversationSessionData(**session_data)
        except Exception as e:
            raise ValueError(f"Invalid session data for {session_id}: {e}")
        
        # Convert session data to ConversationWorkflowState
        workflow_state = self._session_data_to_workflow_state(validated_session.dict(), user_input)
        return workflow_state

    async def update_conversation_workflow_state(self, session_id: str, workflow_state: ConversationWorkflowState) -> bool:
        """
        Update session data from completed ConversationWorkflowState.
        
        Args:
            session_id: Session ID to update
            workflow_state: Completed workflow state to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert workflow state back to session data
            session_data = self._workflow_state_to_session_data(workflow_state)
            
            # Validate session data before storing
            try:
                validated_session = ConversationSessionData(**session_data)
            except Exception as e:
                logger.error(f"Invalid session data for {session_id}: {e}")
                return False
            
            # Update session in Redis
            session_json = json.dumps(validated_session.dict())
            success = await self.redis.set(f"session:{session_id}", session_json, ttl=900)
            
            if success:
                logger.info(f"Updated session {session_id} with workflow state")
                return True
            else:
                logger.error(f"Failed to update session {session_id} in Redis")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update session {session_id} with workflow state: {e}")
            return False

    async def create_new_conversation_session(self, session_id: str, restaurant_id: int, customer_name: Optional[str] = None) -> bool:
        """
        Create a new session with default conversation state for workflow processing.
        
        Args:
            session_id: Session ID to create
            restaurant_id: Restaurant ID for this session
            customer_name: Optional customer name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create default session data with new structure
            session_data = {
                "id": session_id,
                "restaurant_id": restaurant_id,
                "customer_name": customer_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                
                # New workflow fields
                "conversation_state": ConversationState.IDLE.value,
                "conversation_history": [],
                "conversation_context": {
                    "turn_counter": 0,
                    "last_action_uuid": None,
                    "thinking_since": None,
                    "timeout_at": None,
                    "expectation": "free_form_ordering"
                },
                "order_state": {
                    "line_items": [],
                    "last_mentioned_item_ref": None,
                    "totals": {}
                }
            }
            
            # Validate session data before storing
            try:
                validated_session = ConversationSessionData(**session_data)
            except Exception as e:
                logger.error(f"Invalid session data for {session_id}: {e}")
                return False
            
            # Create session in Redis
            session_json = json.dumps(validated_session.dict())
            success = await self.redis.set(f"session:{session_id}", session_json, ttl=900)
            
            if success:
                logger.info(f"Created new conversation session {session_id}")
                return True
            else:
                logger.error(f"Failed to create session {session_id} in Redis")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create new conversation session {session_id}: {e}")
            return False

    def _session_data_to_workflow_state(self, session_data: Dict[str, Any], user_input: str) -> ConversationWorkflowState:
        """
        Convert session data to ConversationWorkflowState.
        
        Args:
            session_data: Session data from Redis
            user_input: User's speech input
            
        Returns:
            ConversationWorkflowState: Converted workflow state
        """
        # Extract basic session info
        session_id = session_data["id"]
        restaurant_id = session_data["restaurant_id"]
        
        # Extract conversation state
        conversation_state = ConversationState(session_data.get("conversation_state", ConversationState.IDLE.value))
        
        # Extract conversation history
        conversation_history = session_data.get("conversation_history", [])
        
        # Extract conversation context
        context_data = session_data.get("conversation_context", {})
        conversation_context = ConversationContext(
            turn_counter=context_data.get("turn_counter", 0),
            last_action_uuid=context_data.get("last_action_uuid"),
            thinking_since=context_data.get("thinking_since"),
            timeout_at=context_data.get("timeout_at"),
            expectation=context_data.get("expectation", "free_form_ordering")
        )
        
        # Extract order state
        order_data = session_data.get("order_state", {})
        order_state = OrderState(
            line_items=order_data.get("line_items", []),
            last_mentioned_item_ref=order_data.get("last_mentioned_item_ref"),
            totals=order_data.get("totals", {})
        )
        
        # Create workflow state
        workflow_state = ConversationWorkflowState(
            session_id=session_id,
            restaurant_id=restaurant_id,
            user_input=user_input,
            conversation_history=conversation_history,
            current_state=conversation_state,
            order_state=order_state,
            conversation_context=conversation_context
        )
        
        return workflow_state

    def _workflow_state_to_session_data(self, workflow_state: ConversationWorkflowState) -> Dict[str, Any]:
        """
        Convert ConversationWorkflowState back to session data for storage.
        
        Args:
            workflow_state: Completed workflow state
            
        Returns:
            Dict: Session data ready for Redis storage
        """
        # Build session data with updated workflow state
        session_data = {
            "id": workflow_state.session_id,
            "restaurant_id": workflow_state.restaurant_id,
            "customer_name": None,  # Will be set from original session if needed
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            
            # Updated workflow fields
            "conversation_state": workflow_state.current_state.value,
            "conversation_history": workflow_state.conversation_history,
            "conversation_context": {
                "turn_counter": workflow_state.conversation_context.turn_counter,
                "last_action_uuid": workflow_state.conversation_context.last_action_uuid,
                "thinking_since": workflow_state.conversation_context.thinking_since,
                "timeout_at": workflow_state.conversation_context.timeout_at,
                "expectation": workflow_state.conversation_context.expectation
            },
            "order_state": {
                "line_items": workflow_state.order_state.line_items,
                "last_mentioned_item_ref": workflow_state.order_state.last_mentioned_item_ref,
                "totals": workflow_state.order_state.totals
            }
        }
        
        return session_data

    async def set_current_session_id(self, session_id: str) -> bool:
        """
        Set the current active session ID.
        
        Args:
            session_id: Session ID to set as current
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = await self.redis.set("current_session", session_id, ttl=900)
            if success:
                logger.info(f"Set current session to {session_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to set current session {session_id}: {e}")
            return False

    async def get_current_session_id(self) -> Optional[str]:
        """
        Get the current active session ID.
        
        Returns:
            Optional[str]: Current session ID if found, None otherwise
        """
        try:
            session_id = await self.redis.get("current_session")
            return session_id
        except Exception as e:
            logger.error(f"Failed to get current session: {e}")
            return None

    async def clear_current_session_id(self) -> bool:
        """
        Clear the current active session ID.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = await self.redis.delete("current_session")
            if success:
                logger.info("Cleared current session")
            return success
        except Exception as e:
            logger.error(f"Failed to clear current session: {e}")
            return False

    async def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the current active session data.
        
        Returns:
            Optional[Dict[str, Any]]: Current session data if found, None otherwise
        """
        try:
            current_session_id = await self.get_current_session_id()
            if not current_session_id:
                return None
            
            session_data = await self.get_session(current_session_id)
            return session_data
        except Exception as e:
            logger.error(f"Failed to get current session data: {e}")
            return None
    
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            bool: True if session exists, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            return session is not None
        except Exception as e:
            logger.error(f"Failed to check if session exists: {e}")
            return False
