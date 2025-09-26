"""
Base parser classes and interfaces for intent parsing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from app.commands.intent_classification_schema import IntentType


@dataclass
class ParserResult:
    """
    Standard result from any parser.
    
    Contains the parsed command data that can be used by CommandFactory.
    Supports both single commands and multiple commands.
    """
    success: bool
    command_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_result(cls, command_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> "ParserResult":
        """Create a successful parser result with command data (single or multiple)."""
        return cls(
            success=True,
            command_data=command_data
        )
    
    @classmethod
    def success_single_command(cls, command_data: Dict[str, Any]) -> "ParserResult":
        """Create a successful parser result with a single command."""
        return cls(
            success=True,
            command_data=command_data
        )
    
    @classmethod
    def success_multiple_commands(cls, command_data: List[Dict[str, Any]]) -> "ParserResult":
        """Create a successful parser result with multiple commands."""
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
    
    def is_multiple_commands(self) -> bool:
        """Check if this result contains multiple commands."""
        return isinstance(self.command_data, list)
    
    def get_commands_list(self) -> List[Dict[str, Any]]:
        """Get commands as a list (handles both single and multiple commands)."""
        if self.command_data is None:
            return []
        elif isinstance(self.command_data, list):
            return self.command_data
        else:
            return [self.command_data]


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
