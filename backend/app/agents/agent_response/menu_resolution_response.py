"""
Pydantic models for Menu Resolution Agent (second agent in the pipeline)
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ResolvedItem(BaseModel):
    """
    Item after menu resolution (with menu_item_id)
    """
    # Original extraction data
    item_name: str = Field(description="Original item name from extraction")
    quantity: int = Field(description="Quantity requested", ge=1, le=100)
    size: Optional[str] = Field(default=None, description="Size requested")
    modifiers: List[str] = Field(default_factory=list, description="Modifiers requested")
    special_instructions: Optional[str] = Field(default=None, description="Special instructions")
    
    # Resolution results
    menu_item_id: int = Field(description="Resolved menu item ID (0 if ambiguous)")
    resolved_name: Optional[str] = Field(default=None, description="Resolved menu item name")
    confidence: float = Field(description="Confidence in resolution (0.0 to 1.0)", ge=0.0, le=1.0)
    
    # Ambiguity and availability handling
    is_ambiguous: bool = Field(default=False, description="Whether this item is ambiguous")
    is_unavailable: bool = Field(default=False, description="Whether this item is unavailable")
    suggested_options: List[str] = Field(default_factory=list, description="Suggested menu items for clarification")
    clarification_question: Optional[str] = Field(default=None, description="Question to ask for clarification")
    
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


class MenuResolutionResponse(BaseModel):
    """
    Response from Menu Resolution Agent (second agent)
    """
    success: bool = Field(description="Whether resolution was successful")
    confidence: float = Field(description="Overall confidence in the resolution (0.0 to 1.0)", ge=0.0, le=1.0)
    resolved_items: List[ResolvedItem] = Field(description="List of items after menu resolution")
    needs_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions to ask for clarification")
    resolution_notes: Optional[str] = Field(default=None, description="Notes about the resolution process")
    
    @field_validator('resolved_items')
    @classmethod
    def validate_resolved_items(cls, v):
        """Ensure at least one item is provided for successful resolutions"""
        # Only validate for successful resolutions - allow empty list for error cases
        return v
    
    def has_ambiguous_items(self) -> bool:
        """Check if any items are ambiguous"""
        return any(item.is_ambiguous for item in self.resolved_items)
    
    def get_clear_items(self) -> List[ResolvedItem]:
        """Get items that were successfully resolved (not ambiguous)"""
        return [item for item in self.resolved_items if not item.is_ambiguous and item.menu_item_id > 0]
    
    def get_ambiguous_items(self) -> List[ResolvedItem]:
        """Get items that are ambiguous and need clarification"""
        return [item for item in self.resolved_items if item.is_ambiguous]
