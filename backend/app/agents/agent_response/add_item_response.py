"""
Pydantic models for ADD_ITEM agent input and output
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.constants.audio_phrases import AudioPhraseType


class ItemToAdd(BaseModel):
    """
    Individual item to add to the order
    """
    menu_item_id: int = Field(description="ID of the menu item to add")
    quantity: int = Field(description="Quantity to add", ge=1, le=100)
    size: Optional[str] = Field(default=None, description="Size of the item (e.g., 'large', 'medium', 'small')")
    modifiers: List[str] = Field(default_factory=list, description="List of modifiers (e.g., 'extra cheese', 'no pickles')")
    special_instructions: Optional[str] = Field(default=None, description="Special cooking instructions")
    
    # Ambiguity fields (used when menu_item_id = 0)
    ambiguous_item: Optional[str] = Field(default=None, description="The ambiguous item name (e.g., 'burger')")
    suggested_options: List[str] = Field(default_factory=list, description="List of suggested menu items for clarification")
    clarification_question: Optional[str] = Field(default=None, description="Custom clarification question")
    
    @field_validator('modifiers')
    @classmethod
    def validate_modifiers(cls, v):
        """Ensure modifiers are not empty strings"""
        return [mod for mod in v if mod and mod.strip()]
    
    @field_validator('special_instructions')
    @classmethod
    def validate_special_instructions(cls, v):
        """Ensure special instructions are not empty strings"""
        if v and not v.strip():
            return None
        return v


class AddItemResponse(BaseModel):
    """
    Response from ADD_ITEM agent
    """
    response_type: str = Field(description="Type of response: 'success' or 'error'")
    phrase_type: AudioPhraseType = Field(description="Audio phrase type for voice generation")
    response_text: str = Field(description="Text response to the customer")
    confidence: float = Field(description="Confidence in the parsing (0.0 to 1.0)", ge=0.0, le=1.0)
    items_to_add: List[ItemToAdd] = Field(description="List of items to add to the order")
    # relevant_data: Dict[str, Any] = Field(default_factory=dict, description="Additional relevant data")  # Removed for OpenAI compatibility
    
    @field_validator('items_to_add')
    @classmethod
    def validate_items_to_add(cls, v):
        """Ensure at least one item is provided for success responses"""
        if not v:
            raise ValueError("At least one item must be provided")
        return v
    
    def to_audio_params(self) -> Dict[str, Any]:
        """Convert to audio generation parameters"""
        return {
            "phrase_type": self.phrase_type,
            "text": self.response_text,
            "confidence": self.confidence
        }


class AddItemContext(BaseModel):
    """
    Context for ADD_ITEM agent
    """
    restaurant_id: str = Field(description="Restaurant ID")
    user_input: str = Field(description="Original user input")
    normalized_user_input: str = Field(description="Normalized user input")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation history")
    order_state: Dict[str, Any] = Field(default_factory=dict, description="Current order state")
    available_menu_items: List[str] = Field(default_factory=list, description="Available menu items")
    menu_categories: List[str] = Field(default_factory=list, description="Menu categories")
    menu_items_by_category: Dict[str, List[str]] = Field(default_factory=dict, description="Menu items organized by category")
    menu_items_with_ingredients: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Menu items with their ingredients")
    available_ingredients: List[Dict[str, Any]] = Field(default_factory=list, description="All available ingredients with costs")
