"""
Order Intent Processor for processing user intents and generating appropriate responses
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from ..dto.order_result import OrderResult
from ..commands import (
    CommandFactory, 
    CommandInvoker, 
    validate_command_contract,
    IntentType
)
from ..agents.prompts.intent_classification import get_intent_classification_prompt


class OrderIntentProcessor:
    """
    Order Intent Processor that processes user intents and determines appropriate actions
    """
    
    def __init__(self):
        """Initialize Order Intent Processor"""
        self.command_factory = CommandFactory()
        self.command_invoker = None  # Will be set with database session
    
    async def process_intent(
        self, 
        text: str, 
        restaurant_id: int, 
        order_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> OrderResult:
        """
        Process user intent and determine appropriate response
        
        Args:
            text: User input text
            restaurant_id: Restaurant ID for context
            order_id: Optional order ID for order-specific operations
            context: Additional context information
            db: Database session for command execution
            
        Returns:
            OrderResult: Response with commands executed
        """
        try:
            if not db:
                return OrderResult.error("Database session required for intent processing")
            
            if not order_id:
                return OrderResult.error("Order ID required for intent processing")
            
            # Set up command invoker with database session
            self.command_invoker = CommandInvoker(db)
            
            # Build context for intent classification
            classification_context = self._build_classification_context(context)
            
            # Classify intent (for now using simple logic, can be upgraded to LLM later)
            intent_data = self._classify_intent(text, classification_context)
            
            # Validate intent contract
            try:
                contract = validate_command_contract(intent_data)
            except Exception as e:
                return OrderResult.error(f"Invalid intent classification: {str(e)}")
            
            # Create command from intent
            command = self.command_factory.create_command(intent_data, restaurant_id, order_id)
            if not command:
                return OrderResult.error("Failed to create command from intent")
            
            # Execute command
            result = await self.command_invoker.execute_command(command)
            return result
                
        except Exception as e:
            return OrderResult.error(f"Intent processing failed: {str(e)}")
    
    def _build_classification_context(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context for intent classification"""
        return {
            "order_items": context.get("order_items", []) if context else [],
            "conversation_state": context.get("conversation_state", "Ordering") if context else "Ordering"
        }
    
    def _classify_intent(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple intent classification (can be upgraded to LLM later)
        
        Args:
            text: User input text
            context: Classification context
            
        Returns:
            Dict: Intent classification data
        """
        text_lower = text.lower()
        
        # ADD_ITEM intent
        if any(word in text_lower for word in ["want", "get", "add", "order", "have", "i'll have"]):
            if any(word in text_lower for word in ["burger", "fries", "drink", "coke", "coffee"]):
                return {
                    "intent": "ADD_ITEM",
                    "confidence": 0.8,
                    "slots": {
                        "item_name_raw": text,
                        "quantity": 1
                    }
                }
        
        # REMOVE_ITEM intent
        if any(word in text_lower for word in ["remove", "delete", "take off", "cancel"]):
            return {
                "intent": "REMOVE_ITEM",
                "confidence": 0.8,
                "slots": {
                    "target_ref": "last_item"
                }
            }
        
        # CLEAR_ORDER intent
        if any(word in text_lower for word in ["clear", "start over", "reset", "cancel order"]):
            return {
                "intent": "CLEAR_ORDER",
                "confidence": 0.9,
                "slots": {}
            }
        
        # CONFIRM_ORDER intent
        if any(word in text_lower for word in ["done", "that's it", "finish", "confirm", "that's all"]):
            return {
                "intent": "CONFIRM_ORDER",
                "confidence": 0.9,
                "slots": {}
            }
        
        # QUESTION intent
        if any(word in text_lower for word in ["what", "how", "when", "where", "menu", "price", "?"]):
            return {
                "intent": "QUESTION",
                "confidence": 0.8,
                "slots": {
                    "question": text
                }
            }
        
        # Default to UNKNOWN
        return {
            "intent": "UNKNOWN",
            "confidence": 0.3,
            "slots": {
                "question": "I'm not sure I understand. Could you please rephrase?"
            }
        }
    
    
    async def get_restaurant_context(self, restaurant_id: int) -> Dict[str, Any]:
        """
        Get restaurant-specific context for better AI responses
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            Dict: Restaurant context information
        """
        # TODO: Implement restaurant context retrieval
        # This would fetch menu items, common phrases, etc.
        
        return {
            "restaurant_id": restaurant_id,
            "menu_items": ["Big Mac", "Quarter Pounder", "Fries", "Coke"],  # Placeholder
            "common_phrases": ["I want", "Can I get", "Add to order"],  # Placeholder
            "special_instructions": ["no cheese", "extra lettuce", "well done"]  # Placeholder
        }
