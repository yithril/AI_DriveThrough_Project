"""
Clear Order Parser

Rule-based parser for CLEAR_ORDER intent.
No parsing needed - just creates a clear order command.
"""

from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from app.commands.intent_classification_schema import IntentType


class ClearOrderParser(BaseParser):
    """
    Parser for CLEAR_ORDER intent.
    
    No complex parsing needed - just creates a clear order command.
    """
    
    def __init__(self):
        super().__init__(IntentType.CLEAR_ORDER)
    
    async def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse clear order intent into command data.
        
        Args:
            user_input: User's input (e.g., "clear my order", "start over")
            context: Additional context (not used for clear order)
            
        Returns:
            ParserResult with clear order command data
        """
        # Clear order has no slots - just the intent
        command_data = self._create_command_data(
            intent="CLEAR_ORDER",
            slots={}  # No slots needed for clear order
        )
        
        return ParserResult.success_result(command_data)
