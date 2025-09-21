"""
Conversation State for LangGraph Workflow

This module defines the simple state object that flows through the LangGraph nodes.
Contains only the essential data needed for conversation flow.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.state_machine import ConversationState, OrderState, ConversationContext
from app.commands.command_contract import IntentType
from app.dto.order_result import CommandBatchResult


@dataclass
class ConversationWorkflowState:
    """
    Simple state object that flows through the LangGraph workflow.
    
    Contains only the essential data needed for conversation flow:
    - Conversation history and context
    - Current and target states
    - User input
    - Intermediate results
    """
    
    # Core conversation data
    session_id: str
    restaurant_id: str
    user_input: str = ""  # What the person said
    
    # Conversation context
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_state: ConversationState = ConversationState.IDLE
    target_state: Optional[ConversationState] = None
    order_state: OrderState = field(default_factory=OrderState)
    conversation_context: ConversationContext = field(default_factory=ConversationContext)
    
    # Intermediate results that get populated as we go through nodes
    intent_type: Optional[IntentType] = None
    intent_confidence: float = 0.0
    intent_slots: Dict[str, Any] = field(default_factory=dict)
    
    commands: List[Dict[str, Any]] = field(default_factory=list)
    command_batch_result: Optional[CommandBatchResult] = None
    
    response_text: str = ""
    audio_url: Optional[str] = None
    
    # Simple error tracking
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
