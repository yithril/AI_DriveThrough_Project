"""
Validation interface for input safety checking
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..dto.order_result import OrderResult


class ValidationServiceInterface(ABC):
    """
    Interface for input validation services
    """
    
    @abstractmethod
    async def validate_input(self, text: str) -> OrderResult:
        """
        Validate input text for safety and appropriateness
        
        Args:
            text: User input text to validate
            
        Returns:
            OrderResult: Success if safe, error if blocked
        """
        pass
    
    @abstractmethod
    async def validate_with_context(self, text: str, context: Dict[str, Any]) -> OrderResult:
        """
        Validate input with additional context
        
        Args:
            text: User input text
            context: Additional context (user history, restaurant info, etc.)
            
        Returns:
            OrderResult: Validation result
        """
        pass
