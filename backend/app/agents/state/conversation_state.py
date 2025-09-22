"""
Conversation State for LangGraph Workflow

This module defines the simple state object that flows through the LangGraph nodes.
Contains only the essential data needed for conversation flow.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.models.state_machine_models import ConversationState, OrderState, ConversationContext
from app.commands.intent_classification_schema import IntentType
from app.dto.order_result import CommandBatchResult
from app.constants.audio_phrases import AudioPhraseType


@dataclass
class ConversationWorkflowState:
    """
    State object that flows through the LangGraph workflow.
    
    Organized by which nodes use which properties for easier understanding.
    """
    
    # =============================================================================
    # CORE DATA (used by all nodes)
    # =============================================================================
    session_id: str
    restaurant_id: str
    user_input: str = ""  # What the person said
    
    # =============================================================================
    # INTENT CLASSIFIER NODE (populates these)
    # =============================================================================
    intent_type: Optional[IntentType] = None
    intent_confidence: float = 0.0
    intent_slots: Dict[str, Any] = field(default_factory=dict)
    
    # =============================================================================
    # STATE MACHINE NODE (uses intent data, populates transition results)
    # =============================================================================
    current_state: ConversationState = ConversationState.IDLE
    target_state: Optional[ConversationState] = None
    transition_requires_command: bool = False
    transition_is_valid: bool = True
    
    # =============================================================================
    # INTENT PARSER ROUTER NODE (uses intent data, populates commands)
    # =============================================================================
    commands: List[Dict[str, Any]] = field(default_factory=list)
    
    # =============================================================================
    # COMMAND EXECUTOR NODE (uses commands, populates batch result)
    # =============================================================================
    command_batch_result: Optional[CommandBatchResult] = None
    order_state_changed: bool = False  # True if order was modified during this turn
    
    # =============================================================================
    # RESPONSE ROUTER NODE (uses batch result, populates routing context)
    # =============================================================================
    next_node: Optional[str] = None  # "canned_response", "follow_up_agent", "dynamic_voice_response"
    response_context: Dict[str, Any] = field(default_factory=dict)  # Context for next node
    
    # =============================================================================
    # VOICE GENERATION NODE (uses phrase type and custom text to generate audio)
    # =============================================================================
    # Required for voice generation:
    response_phrase_type: Optional[AudioPhraseType] = None  # Set by response router
    # Optional for voice generation:
    custom_response_text: Optional[str] = None  # Custom text for dynamic phrases
    
    # =============================================================================
    # RESPONSE NODES OUTPUT (populated by voice generation and clarification agent)
    # =============================================================================
    response_text: str = ""  # Text content of the response
    audio_url: Optional[str] = None  # S3 URL to the generated audio file
    
    # =============================================================================
    # CONVERSATION CONTEXT (used by multiple nodes)
    # =============================================================================
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    order_state: OrderState = field(default_factory=lambda: OrderState(
        line_items=[],
        last_mentioned_item_ref=None,
        totals={}
    ))
    conversation_context: ConversationContext = field(default_factory=lambda: ConversationContext(
        turn_counter=0,
        last_action_uuid=None,
        thinking_since=None,
        timeout_at=None,
        expectation="free_form_ordering"
    ))
    
    # =============================================================================
    # ERROR TRACKING (used by all nodes)
    # =============================================================================
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
