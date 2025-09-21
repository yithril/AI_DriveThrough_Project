"""
Session validation models for conversation workflow state management.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models.state_machine_models import ConversationState


class ConversationContextData(BaseModel):
    """Validation model for conversation context data"""
    turn_counter: int = Field(ge=0, description="Turn counter must be non-negative")
    last_action_uuid: Optional[str] = None
    thinking_since: Optional[str] = None  # ISO datetime string
    timeout_at: Optional[str] = None  # ISO datetime string
    expectation: str = Field(default="free_form_ordering", description="Current expectation")

    @validator('expectation')
    def validate_expectation(cls, v):
        valid_expectations = [
            "free_form_ordering", "single_answer", "menu_questions_or_wait", 
            "single_targeted_question", "yes_no_confirmation"
        ]
        if v not in valid_expectations:
            raise ValueError(f"Invalid expectation: {v}. Must be one of: {valid_expectations}")
        return v


class OrderStateData(BaseModel):
    """Validation model for order state data"""
    line_items: List[Dict[str, Any]] = Field(default_factory=list, description="Order line items")
    last_mentioned_item_ref: Optional[str] = None
    totals: Dict[str, Any] = Field(default_factory=dict, description="Order totals")


class ConversationSessionData(BaseModel):
    """Validation model for complete session data"""
    id: str = Field(..., description="Session ID")
    restaurant_id: int = Field(..., gt=0, description="Restaurant ID must be positive")
    customer_name: Optional[str] = Field(None, max_length=100, description="Customer name")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    
    # Workflow fields
    conversation_state: str = Field(..., description="Current conversation state")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    conversation_context: ConversationContextData = Field(..., description="Conversation context")
    order_state: OrderStateData = Field(..., description="Order state")

    @validator('conversation_state')
    def validate_conversation_state(cls, v):
        valid_states = [state.value for state in ConversationState]
        if v not in valid_states:
            raise ValueError(f"Invalid conversation state: {v}. Must be one of: {valid_states}")
        return v

    @validator('created_at', 'updated_at')
    def validate_timestamps(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {v}. Must be ISO format")
        return v

    @validator('conversation_history')
    def validate_conversation_history(cls, v):
        if not isinstance(v, list):
            raise ValueError("Conversation history must be a list")
        
        for i, turn in enumerate(v):
            if not isinstance(turn, dict):
                raise ValueError(f"Conversation history turn {i} must be a dictionary")
            
            required_fields = ['turn', 'user_input', 'response', 'timestamp']
            for field in required_fields:
                if field not in turn:
                    raise ValueError(f"Conversation history turn {i} missing required field: {field}")
        
        return v
