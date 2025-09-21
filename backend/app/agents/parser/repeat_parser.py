"""
Repeat Parser

Rule-based parser for REPEAT intent.
Detects scope (last_item vs full_order) based on keywords.
"""

from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from app.commands.intent_classification_schema import IntentType


class RepeatParser(BaseParser):
    """
    Parser for REPEAT intent.
    
    Detects scope based on keywords in user input.
    """
    
    def __init__(self):
        super().__init__(IntentType.REPEAT)
    
    def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse repeat intent into command data.
        
        Args:
            user_input: User's input (e.g., "repeat that", "what did I order")
            context: Additional context (order state, conversation history)
            
        Returns:
            ParserResult with repeat command data or clarification needed
        """
        # Convert to lowercase for keyword matching
        input_lower = user_input.lower()
        
        # Determine scope based on keywords
        scope = self._detect_scope(input_lower)
        target_ref = self._detect_target_reference(input_lower, context)
        
        # Create command data for repeat intent
        command_data = self._create_command_data(
            intent="REPEAT",
            slots={
                "target_ref": target_ref,
                "scope": scope
            }
        )
        
        return ParserResult.success_result(command_data)
    
    def _detect_scope(self, input_lower: str) -> str:
        """
        Detect whether user wants to repeat last item or full order.
        
        Args:
            input_lower: Lowercase user input
            
        Returns:
            "last_item" or "full_order"
        """
        # Keywords that suggest full order
        full_order_keywords = [
            "order", "everything", "all", "my order", "what did i order",
            "repeat my order", "repeat everything", "repeat all"
        ]
        
        # Keywords that suggest last item
        last_item_keywords = [
            "that", "last", "previous", "repeat that", "repeat last",
            "what was that", "what did i just say"
        ]
        
        # Check for full order keywords first
        for keyword in full_order_keywords:
            if keyword in input_lower:
                return "full_order"
        
        # Check for last item keywords
        for keyword in last_item_keywords:
            if keyword in input_lower:
                return "last_item"
        
        # Default to full order if unclear
        return "full_order"
    
    def _detect_target_reference(self, input_lower: str, context: Dict[str, Any]) -> str:
        """
        Detect target reference for the repeat operation.
        
        Args:
            input_lower: Lowercase user input
            context: Additional context
            
        Returns:
            Target reference string
        """
        # Check if there's a specific line number mentioned
        import re
        line_match = re.search(r'line\s*(\d+)', input_lower)
        if line_match:
            line_num = line_match.group(1)
            return f"line_{line_num}"
        
        # Check for "last item" references
        if any(keyword in input_lower for keyword in ["last", "previous", "that"]):
            return "last_item"
        
        # Default to last item
        return "last_item"
