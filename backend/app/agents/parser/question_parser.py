"""
Question Parser

Rule-based parser for QUESTION intent.
Maps questions to FAQ categories for appropriate responses.
"""

from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from app.commands.intent_classification_schema import IntentType


class QuestionParser(BaseParser):
    """
    Parser for QUESTION intent.
    
    Maps user questions to FAQ categories for appropriate responses.
    """
    
    def __init__(self):
        super().__init__(IntentType.QUESTION)
    
    def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse question intent into command data.
        
        Args:
            user_input: User's question
            context: Additional context (restaurant info, menu, etc.)
            
        Returns:
            ParserResult with question command data
        """
        # Convert to lowercase for keyword matching
        input_lower = user_input.lower()
        
        # Detect question category
        category = self._detect_question_category(input_lower)
        
        # Create command data for question intent
        command_data = self._create_command_data(
            intent="QUESTION",
            slots={
                "question": user_input,
                "category": category
            }
        )
        
        return ParserResult.success_result(command_data)
    
    def _detect_question_category(self, input_lower: str) -> str:
        """
        Detect the category of the question.
        
        Args:
            input_lower: Lowercase user input
            
        Returns:
            Question category string
        """
        # Pricing questions
        pricing_keywords = [
            "price", "cost", "how much", "expensive", "cheap", "dollar",
            "total", "amount", "charge", "fee"
        ]
        
        # Menu questions
        menu_keywords = [
            "menu", "food", "item", "combo",
            "special", "available", "have", "serve", "offer"
        ]
        
        # Hours questions
        hours_keywords = [
            "hours", "open", "close", "time", "when", "today", "tomorrow",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
        ]
        
        # Location questions
        location_keywords = [
            "location", "address", "where", "find", "near", "directions",
            "drive", "walk", "distance"
        ]
        
        # Ingredients questions
        ingredients_keywords = [
            "ingredient", "allergen", "gluten", "dairy", "nuts", "vegetarian",
            "vegan", "contains", "made with", "what's in"
        ]
        
        # Check each category
        if any(keyword in input_lower for keyword in pricing_keywords):
            return "pricing"
        elif any(keyword in input_lower for keyword in menu_keywords):
            return "menu"
        elif any(keyword in input_lower for keyword in hours_keywords):
            return "hours"
        elif any(keyword in input_lower for keyword in location_keywords):
            return "location"
        elif any(keyword in input_lower for keyword in ingredients_keywords):
            return "ingredients"
        else:
            return "general"
