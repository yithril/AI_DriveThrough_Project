"""
Base parser classes and interfaces for intent parsing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.commands.intent_classification_schema import IntentType


@dataclass
class ParserResult:
    """
    Standard result from any parser.
    
    Contains the parsed command data that can be used by CommandFactory.
    """
    success: bool
    command_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_result(cls, command_data: Dict[str, Any]) -> "ParserResult":
        """Create a successful parser result with command data."""
        return cls(
            success=True,
            command_data=command_data
        )
    
    
    @classmethod
    def error_result(cls, error_message: str) -> "ParserResult":
        """Create an error result."""
        return cls(
            success=False,
            error_message=error_message
        )


class BaseParser(ABC):
    """
    Base class for all intent parsers.
    
    Each parser handles a specific intent type and converts it into
    command data that can be consumed by CommandFactory.
    """
    
    def __init__(self, intent_type: IntentType):
        self.intent_type = intent_type
    
    @abstractmethod
    async def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse user input and context into command data.
        
        Args:
            user_input: The original user input text
            context: Additional context (order state, conversation history, etc.)
            
        Returns:
            ParserResult with command data or error information
        """
        pass
    
    def _create_command_data(self, intent: str, slots: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Create standardized command data for CommandFactory.
        
        This ensures all parsers output the same format that CommandFactory expects.
        """
        return {
            "intent": intent,
            "confidence": 1.0,  # Rule-based parsers are always confident
            "slots": slots,
            "notes": f"Parsed by {self.__class__.__name__}",
            **kwargs
        }
