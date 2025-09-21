"""
Command contract schema for LLM intent classification
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Supported intent types"""
    ADD_ITEM = "ADD_ITEM"
    REMOVE_ITEM = "REMOVE_ITEM"
    CLEAR_ORDER = "CLEAR_ORDER"
    MODIFY_ITEM = "MODIFY_ITEM"
    SET_QUANTITY = "SET_QUANTITY"
    CONFIRM_ORDER = "CONFIRM_ORDER"
    REPEAT = "REPEAT"
    QUESTION = "QUESTION"
    SMALL_TALK = "SMALL_TALK"
    UNKNOWN = "UNKNOWN"


class ChangeOperation(BaseModel):
    """Individual change operation for MODIFY_ITEM"""
    op: str = Field(..., description="Operation type: set_size, add_modifier, remove_modifier, set_quantity, add_special_instruction")
    value: str = Field(..., description="Value for the operation")


class IntentClassificationResult(BaseModel):
    """
    Simple JSON schema for LLM intent classification output
    
    Just classify the intent - no complex parsing needed
    """
    intent: IntentType = Field(..., description="The classified intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class AddItemSlots(BaseModel):
    """Slots for ADD_ITEM intent"""
    item_name_raw: Optional[str] = Field(None, description="User's original words for the item")
    item_id: Optional[int] = Field(None, description="Canonical menu item ID")
    quantity: int = Field(default=1, description="Quantity to add")
    size: Optional[str] = Field(None, description="Size: small/medium/large or null")
    modifiers: List[str] = Field(default_factory=list, description="Modifiers like no_pickles, extra_ketchup")
    combo: bool = Field(default=False, description="Whether this is a combo meal")
    drink_id: Optional[int] = Field(None, description="Drink ID if combo")
    sides: List[int] = Field(default_factory=list, description="Side item IDs if combo")
    special_instructions: Optional[str] = Field(None, description="Special cooking instructions")


class RemoveItemSlots(BaseModel):
    """Slots for REMOVE_ITEM intent"""
    order_item_id: Optional[int] = Field(None, description="Direct order item ID to remove")
    target_ref: Optional[str] = Field(None, description="Target reference: last_item, line_1, etc.")


class ModifyItemSlots(BaseModel):
    """Slots for MODIFY_ITEM intent"""
    target_ref: str = Field(default="last_item", description="Target reference to modify")
    changes: List[ChangeOperation] = Field(..., description="List of changes to apply")


class SetQuantitySlots(BaseModel):
    """Slots for SET_QUANTITY intent"""
    target_ref: str = Field(default="last_item", description="Target reference to modify")
    quantity: int = Field(..., ge=1, description="New quantity")


class RepeatSlots(BaseModel):
    """Slots for REPEAT intent"""
    target_ref: str = Field(default="last_item", description="Target reference to repeat")
    scope: str = Field(default="last_item", description="Scope: last_item or full_order")


class QuestionSlots(BaseModel):
    """Slots for QUESTION/SMALL_TALK/UNKNOWN intents"""
    question: str = Field(default="How can I help you?", description="Question or response to user")


# Slot validation schemas for each intent
SLOT_SCHEMAS = {
    IntentType.ADD_ITEM: AddItemSlots,
    IntentType.REMOVE_ITEM: RemoveItemSlots,
    IntentType.CLEAR_ORDER: dict,  # No slots needed
    IntentType.MODIFY_ITEM: ModifyItemSlots,
    IntentType.SET_QUANTITY: SetQuantitySlots,
    IntentType.CONFIRM_ORDER: dict,  # No slots needed
    IntentType.REPEAT: RepeatSlots,
    IntentType.QUESTION: QuestionSlots,
    IntentType.SMALL_TALK: QuestionSlots,
    IntentType.UNKNOWN: QuestionSlots,
}


def validate_command_contract(data: Dict[str, Any]) -> IntentClassificationResult:
    """
    Validate and parse command contract from LLM output
    
    Args:
        data: Raw JSON data from LLM
        
    Returns:
        Validated CommandContract
        
    Raises:
        ValueError: If validation fails
    """
    try:
        # Parse the main contract
        contract = IntentClassificationResult(**data)
        
        # Validate slots against intent-specific schema
        if contract.intent in SLOT_SCHEMAS:
            slot_schema = SLOT_SCHEMAS[contract.intent]
            if slot_schema != dict:  # Skip validation for intents with no slots
                slot_schema(**contract.slots)
        
        return contract
        
    except Exception as e:
        raise ValueError(f"Invalid command contract: {str(e)}")


def get_command_contract_schema() -> Dict[str, Any]:
    """
    Get the JSON schema for the command contract
    
    Returns:
        JSON schema that can be used in LLM prompts
    """
    return {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [intent.value for intent in IntentType],
                "description": "The classified intent"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score between 0 and 1"
            },
            "slots": {
                "type": "object",
                "description": "Intent-specific parameters",
                "additionalProperties": False
            },
            "needs_clarification": {
                "type": "boolean",
                "description": "Whether clarification is needed"
            },
            "clarifying_question": {
                "type": "string",
                "description": "Question to ask for clarification"
            },
            "notes": {
                "type": "string",
                "description": "Internal notes for logging"
            }
        },
        "required": ["intent", "confidence"],
        "additionalProperties": False
    }
