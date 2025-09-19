"""
Base command abstract class for AI operations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from ..dto.order_result import OrderResult


class BaseCommand(ABC):
    """
    Abstract base class for all AI commands
    Provides a consistent interface for command execution
    """
    
    def __init__(self, restaurant_id: int, order_id: int = None):
        """
        Initialize command with required context
        
        Args:
            restaurant_id: Restaurant ID for the operation
            order_id: Optional order ID (for order-specific commands)
        """
        self.restaurant_id = restaurant_id
        self.order_id = order_id
    
    @abstractmethod
    async def execute(self, db) -> OrderResult:
        """
        Execute the command
        
        Args:
            db: Database session for command execution
            
        Returns:
            OrderResult: Result of the command execution
        """
        pass
    
    @property
    def command_name(self) -> str:
        """Get the name of the command"""
        return self.__class__.__name__.replace("Command", "").lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for logging/debugging"""
        return {
            "command": self.command_name,
            "restaurant_id": self.restaurant_id,
            "order_id": self.order_id,
            "parameters": self._get_parameters()
        }
    
    def _get_parameters(self) -> Dict[str, Any]:
        """Get command-specific parameters (override in subclasses)"""
        return {}
