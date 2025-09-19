"""
Command factory for creating commands from LLM intent classification
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .base_command import BaseCommand
from .add_item_command import AddItemCommand
from .remove_item_command import RemoveItemCommand
from .clear_order_command import ClearOrderCommand
from .answer_question_command import AnswerQuestionCommand
from .modify_item_command import ModifyItemCommand
from .set_quantity_command import SetQuantityCommand
from .confirm_order_command import ConfirmOrderCommand
from .repeat_command import RepeatCommand


class CommandFactory:
    """
    Factory class to create commands from LLM intent classification results
    """
    
    # Map of intent names to command classes
    INTENT_TO_COMMAND = {
        "ADD_ITEM": AddItemCommand,
        "REMOVE_ITEM": RemoveItemCommand,
        "CLEAR_ORDER": ClearOrderCommand,
        "MODIFY_ITEM": ModifyItemCommand,
        "SET_QUANTITY": SetQuantityCommand,
        "CONFIRM_ORDER": ConfirmOrderCommand,
        "REPEAT": RepeatCommand,
        "QUESTION": AnswerQuestionCommand,
        "SMALL_TALK": AnswerQuestionCommand,  # Route small talk to question handler
        "UNKNOWN": AnswerQuestionCommand,     # Route unknown to question handler
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
            # Default to AnswerQuestionCommand for unsupported intents
            return AnswerQuestionCommand(
                restaurant_id=restaurant_id,
                order_id=order_id,
                question=f"Sorry, I don't understand '{intent}'. Could you please rephrase?"
            )
        
        command_class = cls.INTENT_TO_COMMAND[intent]
        
        try:
            # Create command based on intent type
            if intent == "ADD_ITEM":
                return cls._create_add_item_command(command_class, slots, restaurant_id, order_id)
            elif intent == "REMOVE_ITEM":
                return cls._create_remove_item_command(command_class, slots, restaurant_id, order_id)
            elif intent == "CLEAR_ORDER":
                return cls._create_clear_order_command(command_class, restaurant_id, order_id)
            elif intent == "MODIFY_ITEM":
                return cls._create_modify_item_command(command_class, slots, restaurant_id, order_id)
            elif intent == "SET_QUANTITY":
                return cls._create_set_quantity_command(command_class, slots, restaurant_id, order_id)
            elif intent == "CONFIRM_ORDER":
                return cls._create_confirm_order_command(command_class, restaurant_id, order_id)
            elif intent == "REPEAT":
                return cls._create_repeat_command(command_class, slots, restaurant_id, order_id)
            elif intent in ["QUESTION", "SMALL_TALK", "UNKNOWN"]:
                return cls._create_question_command(command_class, slots, restaurant_id, order_id)
            else:
                return None
                
        except Exception as e:
            # If command creation fails, return a question command asking for clarification
            return AnswerQuestionCommand(
                restaurant_id=restaurant_id,
                order_id=order_id,
                question=f"I had trouble processing that request. Could you please try again? ({str(e)})"
            )
    
    @classmethod
    def _create_add_item_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create AddItemCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            menu_item_id=slots.get("item_id"),
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
    def _create_modify_item_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create ModifyItemCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            target_ref=slots.get("target_ref", "last_item"),
            changes=slots.get("changes", [])
        )
    
    @classmethod
    def _create_set_quantity_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create SetQuantityCommand from slots"""
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            target_ref=slots.get("target_ref", "last_item"),
            quantity=slots.get("quantity", 1)
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
            target_ref=slots.get("target_ref", "last_item"),
            scope=slots.get("scope", "last_item")
        )
    
    @classmethod
    def _create_question_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
        """Create AnswerQuestionCommand from slots"""
        question = slots.get("question", "How can I help you?")
        return command_class(
            restaurant_id=restaurant_id,
            order_id=order_id,
            question=question
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
