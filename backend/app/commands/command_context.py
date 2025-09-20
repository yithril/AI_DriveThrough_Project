"""
Command context that provides scoped services to commands
"""

from typing import Optional
from ..services.order_session_interface import OrderSessionInterface
from ..services.order_service import OrderService


class CommandContext:
    """
    Context object that provides scoped services to commands
    
    Encapsulates all the services a command needs, scoped to the current
    order/session/tenant. Built by the CommandInvoker from DI container.
    """
    
    def __init__(
        self,
        order_session_service: OrderSessionInterface,
        order_service: OrderService,
        restaurant_id: int,
        order_id: Optional[int] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize command context with scoped services
        
        Args:
            order_session_service: Service for order/session operations
            order_service: Order service for business logic operations
            restaurant_id: Restaurant ID for this context
            order_id: Optional order ID for order-specific operations
            session_id: Optional session ID for session-specific operations
        """
        self.order_session_service = order_session_service
        self.order_service = order_service
        self.restaurant_id = restaurant_id
        self.order_id = order_id
        self.session_id = session_id
    
    @property
    def is_order_scoped(self) -> bool:
        """Check if this context is scoped to a specific order"""
        return self.order_id is not None
    
    @property
    def is_session_scoped(self) -> bool:
        """Check if this context is scoped to a specific session"""
        return self.session_id is not None
    
    def get_order_id(self) -> int:
        """
        Get the order ID for this context
        
        Returns:
            int: Order ID
            
        Raises:
            ValueError: If no order ID is set
        """
        if self.order_id is None:
            raise ValueError("Command context is not scoped to an order")
        return self.order_id
    
    def get_session_id(self) -> str:
        """
        Get the session ID for this context
        
        Returns:
            str: Session ID
            
        Raises:
            ValueError: If no session ID is set
        """
        if self.session_id is None:
            raise ValueError("Command context is not scoped to a session")
        return self.session_id
    
    def with_order_id(self, order_id: int) -> 'CommandContext':
        """
        Create a new context scoped to a specific order
        
        Args:
            order_id: Order ID to scope to
            
        Returns:
            CommandContext: New context with order ID
        """
        return CommandContext(
            order_session_service=self.order_session_service,
            order_service=self.order_service,
            restaurant_id=self.restaurant_id,
            order_id=order_id,
            session_id=self.session_id
        )
    
    def with_session_id(self, session_id: str) -> 'CommandContext':
        """
        Create a new context scoped to a specific session
        
        Args:
            session_id: Session ID to scope to
            
        Returns:
            CommandContext: New context with session ID
        """
        return CommandContext(
            order_session_service=self.order_session_service,
            order_service=self.order_service,
            restaurant_id=self.restaurant_id,
            order_id=self.order_id,
            session_id=session_id
        )
