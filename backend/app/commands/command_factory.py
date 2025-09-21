"""
Command factory for creating commands from LLM intent classification
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .base_command import BaseCommand
from .add_item_command import AddItemCommand
from .remove_item_command import RemoveItemCommand
from .clear_order_command import ClearOrderCommand
from .confirm_order_command import ConfirmOrderCommand
from .repeat_command import RepeatCommand
from .question_command import QuestionCommand
from .small_talk_command import SmallTalkCommand
from .unknown_command import UnknownCommand


class CommandFactory:
    """
    Factory class to create commands from LLM intent classification results
    """
    
    # Map of intent names to command classes
    INTENT_TO_COMMAND = {
        "ADD_ITEM": AddItemCommand,
        "REMOVE_ITEM": RemoveItemCommand,
        "CLEAR_ORDER": ClearOrderCommand,
        "CONFIRM_ORDER": ConfirmOrderCommand,
        "REPEAT": RepeatCommand,
        "QUESTION": QuestionCommand,
        "SMALL_TALK": SmallTalkCommand,
        "UNKNOWN": UnknownCommand,
        # These intents are kept but don't create commands (handled elsewhere):
        # "MODIFY_ITEM": Handled as RemoveItemCommand + AddItemCommand
        # "SET_QUANTITY": Handled as RemoveItemCommand + AddItemCommand  
    }
    
    @classmethod
    def create_command(
        cls, 
        intent_data: Dict[str, Any], 
        restaurant_id: int, 
        order_id: int
    ) -> Optional[BaseCommand]:
        """
        Create a command from LLM intent classification data
        
        Args:
            intent_data: Dictionary containing intent classification results
                        Expected keys: intent, confidence, slots, needs_clarification
            restaurant_id: Restaurant ID for the command
            order_id: Order ID for the command
            
        Returns:
            BaseCommand instance or None if intent not supported
        """
        intent = intent_data.get("intent", "").upper()
        slots = intent_data.get("slots", {})
        
        if intent not in cls.INTENT_TO_COMMAND:
            # These intents don't create commands - they're handled elsewhere
            return None
        
        command_class = cls.INTENT_TO_COMMAND[intent]
        
        try:
            # Create command based on intent type
            if intent == "ADD_ITEM":
                return cls._create_add_item_command(command_class, slots, restaurant_id, order_id)
            elif intent == "REMOVE_ITEM":
                return cls._create_remove_item_command(command_class, slots, restaurant_id, order_id)
            elif intent == "CLEAR_ORDER":
                return cls._create_clear_order_command(command_class, restaurant_id, order_id)
            elif intent == "CONFIRM_ORDER":
                return cls._create_confirm_order_command(command_class, restaurant_id, order_id)
            elif intent == "REPEAT":
                return cls._create_repeat_command(command_class, slots, restaurant_id, order_id)
            elif intent == "QUESTION":
                return cls._create_question_command(command_class, slots, restaurant_id, order_id)
            elif intent == "SMALL_TALK":
                return cls._create_small_talk_command(command_class, slots, restaurant_id, order_id)
            elif intent == "UNKNOWN":
                return cls._create_unknown_command(command_class, slots, restaurant_id, order_id)
            else:
                return None
                
        except Exception as e:
            # If command creation fails, return None (handled elsewhere)
            return None
    
    @classmethod
    def _create_add_item_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create AddItemCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            menu_item_id=slots.get("menu_item_id"),
            quantity=slots.get("quantity", 1),
            size=slots.get("size"),
            modifiers=slots.get("modifiers", []),
            special_instructions=slots.get("special_instructions")
        )
    
    @classmethod
    def _create_remove_item_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create RemoveItemCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            order_item_id=slots.get("order_item_id"),
            target_ref=slots.get("target_ref")
        )
    
    @classmethod
    def _create_clear_order_command(cls, command_class, restaurant_id: int, order_id: int):
        """Create ClearOrderCommand"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id
        )
    
    
    @classmethod
    def _create_confirm_order_command(cls, command_class, restaurant_id: int, order_id: int):
        """Create ConfirmOrderCommand"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id
        )
    
    @classmethod
    def _create_repeat_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create RepeatCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            scope=slots.get("scope", "full_order"),
            target_ref=slots.get("target_ref", "last_item")
        )
    
    @classmethod
    def _create_question_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create QuestionCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            question=slots.get("question", "How can I help you?"),
            category=slots.get("category", "general")
        )
    
    @classmethod
    def _create_small_talk_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create SmallTalkCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            user_input=slots.get("user_input", ""),
            response_type=slots.get("response_type", "general")
        )
    
    @classmethod
    def _create_unknown_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create UnknownCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            user_input=slots.get("user_input", ""),
            clarifying_question=slots.get("clarifying_question", "I'm sorry, I didn't understand. Could you please repeat that?")
        )
    
    
    @classmethod
    def get_supported_intents(cls) -> List[str]:
        """Get list of supported intent names"""
        return list(cls.INTENT_TO_COMMAND.keys())
    
    @classmethod
    def validate_intent_data(cls, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize intent data from LLM
        
        Args:
            intent_data: Raw intent data from LLM
            
        Returns:
            Validated and normalized intent data
        """
        validated = {
            "intent": intent_data.get("intent", "UNKNOWN").upper(),
            "confidence": float(intent_data.get("confidence", 0.0)),
            "slots": intent_data.get("slots", {}),
            "needs_clarification": bool(intent_data.get("needs_clarification", False)),
            "clarifying_question": intent_data.get("clarifying_question", ""),
            "notes": intent_data.get("notes", "")
        }
        
        # Ensure confidence is between 0 and 1
        validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))
        
        # Normalize intent name
        if validated["intent"] not in cls.INTENT_TO_COMMAND:
            validated["intent"] = "UNKNOWN"
        
        return validated
