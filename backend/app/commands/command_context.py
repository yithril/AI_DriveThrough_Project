"""
Command Context - Pure Data Holder

This is a simple data container that holds all the information commands need.
No service imports, no logic, just data.
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass, field


@dataclass
class CommandContext:
    """
    Pure data holder for command execution context.
    
    Contains:
    - Database session
    - Session/tenant identifiers  
    - Service placeholders (populated by executor)
    - Any other runtime data commands need
    """
    
    # Core identifiers
    session_id: str
    restaurant_id: int
    user_id: Optional[str] = None
    order_id: Optional[int] = None
    
    # Database session (populated by executor)
    db_session: Optional[Any] = None
    
    # Service placeholders (populated by executor)
    order_service: Optional[Any] = None
    order_session_service: Optional[Any] = None
    customization_validator: Optional[Any] = None
    
    # Runtime data
    current_order: Optional[Dict[str, Any]] = None
    conversation_context: Optional[Dict[str, Any]] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def set_order_service(self, service: Any) -> None:
        """Set the order service (called by executor)"""
        self.order_service = service
    
    def set_order_session_service(self, service: Any) -> None:
        """Set the order session service (called by executor)"""
        self.order_session_service = service
    
    def set_customization_validator(self, validator: Any) -> None:
        """Set the customization validator (called by executor)"""
        self.customization_validator = validator
    
    def set_db_session(self, session: Any) -> None:
        """Set the database session (called by executor)"""
        self.db_session = session
    
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
            session_id=self.session_id,
            restaurant_id=self.restaurant_id,
            user_id=self.user_id,
            order_id=order_id,
            db_session=self.db_session,
            order_service=self.order_service,
            order_session_service=self.order_session_service,
            customization_validator=self.customization_validator,
            current_order=self.current_order,
            conversation_context=self.conversation_context,
            metadata=self.metadata.copy()
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
            session_id=session_id,
            restaurant_id=self.restaurant_id,
            user_id=self.user_id,
            order_id=self.order_id,
            db_session=self.db_session,
            order_service=self.order_service,
            order_session_service=self.order_session_service,
            customization_validator=self.customization_validator,
            current_order=self.current_order,
            conversation_context=self.conversation_context,
            metadata=self.metadata.copy()
        )
