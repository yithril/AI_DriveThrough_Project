"""
Confirm Order Parser

Rule-based parser for CONFIRM_ORDER intent.
No parsing needed - just creates a confirm order command.
"""

from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from app.commands.intent_classification_schema import IntentType


class ConfirmOrderParser(BaseParser):
    """
    Parser for CONFIRM_ORDER intent.
    
    No complex parsing needed - just creates a confirm order command.
    """
    
    def __init__(self):
        super().__init__(IntentType.CONFIRM_ORDER)
    
    async def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse confirm order intent into command data.
        
        Args:
            user_input: User's input (e.g., "that's it", "done", "confirm")
            context: Additional context (not used for confirm order)
            
        Returns:
            ParserResult with confirm order command data
        """
        # Confirm order has no slots - just the intent
        command_data = self._create_command_data(
            intent="CONFIRM_ORDER",
            slots={}  # No slots needed for confirm order
        )
        
        return ParserResult.success_result(command_data)
