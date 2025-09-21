"""
Small Talk Parser

Rule-based parser for SMALL_TALK intent.
Detects response type for appropriate canned responses.
"""

from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from app.commands.intent_classification_schema import IntentType


class SmallTalkParser(BaseParser):
    """
    Parser for SMALL_TALK intent.
    
    Detects the type of small talk for appropriate responses.
    """
    
    def __init__(self):
        super().__init__(IntentType.SMALL_TALK)
    
    def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse small talk intent into command data.
        
        Args:
            user_input: User's small talk input
            context: Additional context (conversation history, etc.)
            
        Returns:
            ParserResult with small talk command data
        """
        # Convert to lowercase for keyword matching
        input_lower = user_input.lower()
        
        # Detect response type
        response_type = self._detect_response_type(input_lower)
        
        # Create command data for small talk intent
        command_data = self._create_command_data(
            intent="SMALL_TALK",
            slots={
                "response_type": response_type,
                "user_input": user_input
            }
        )
        
        return ParserResult.success_result(command_data)
    
    def _detect_response_type(self, input_lower: str) -> str:
        """
        Detect the type of small talk response needed.
        
        Args:
            input_lower: Lowercase user input
            
        Returns:
            Response type string
        """
        # Greeting keywords
        greeting_keywords = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "greetings", "howdy"
        ]
        
        # Thanks keywords
        thanks_keywords = [
            "thank you", "thanks", "appreciate", "grateful", "much obliged"
        ]
        
        # Goodbye keywords
        goodbye_keywords = [
            "goodbye", "bye", "see you", "later", "farewell", "take care"
        ]
        
        # Compliment keywords
        compliment_keywords = [
            "good", "great", "excellent", "wonderful", "amazing", "fantastic",
            "love", "like", "enjoy", "delicious", "tasty"
        ]
        
        # Check each type
        if any(keyword in input_lower for keyword in greeting_keywords):
            return "greeting"
        elif any(keyword in input_lower for keyword in thanks_keywords):
            return "thanks"
        elif any(keyword in input_lower for keyword in goodbye_keywords):
            return "goodbye"
        elif any(keyword in input_lower for keyword in compliment_keywords):
            return "compliment"
        else:
            return "general"
