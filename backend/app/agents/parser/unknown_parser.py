"""
Unknown Parser

Rule-based parser for UNKNOWN intent.
Provides default clarification response.
"""

from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from app.commands.intent_classification_schema import IntentType


class UnknownParser(BaseParser):
    """
    Parser for UNKNOWN intent.
    
    Provides default clarification response when intent cannot be determined.
    """
    
    def __init__(self):
        super().__init__(IntentType.UNKNOWN)
    
    def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse unknown intent into command data.
        
        Args:
            user_input: User's unclear input
            context: Additional context (conversation history, order state)
            
        Returns:
            ParserResult with unknown command data requiring clarification
        """
        # Generate appropriate clarification question based on context
        clarifying_question = self._generate_clarifying_question(context)
        
        # Create command data for unknown intent
        command_data = self._create_command_data(
            intent="UNKNOWN",
            slots={
                "user_input": user_input,
                "clarifying_question": clarifying_question
            }
        )
        
        return ParserResult.success_result(command_data)
    
    def _generate_clarifying_question(self, context: Dict[str, Any]) -> str:
        """
        Generate an appropriate clarifying question based on context.
        
        Args:
            context: Additional context (order state, conversation history)
            
        Returns:
            Clarifying question string
        """
        # Check if user has an order
        order_items = context.get("order_items", [])
        has_order = len(order_items) > 0
        
        # Check conversation state
        current_state = context.get("current_state", "IDLE")
        
        # If context is empty (no order_items key), use default message
        if "order_items" not in context:
            return "I'm sorry, I didn't understand. Could you please repeat that?"
        elif not has_order and current_state == "IDLE":
            return "What would you like to order today?"
        elif not has_order:
            return "I'm here to help with your order. What would you like?"
        elif has_order:
            return "I didn't quite catch that. Would you like to add something to your order, or are you ready to confirm?"
        else:
            return "I'm sorry, I didn't understand. Could you please repeat that?"
