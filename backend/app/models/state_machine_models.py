"""
State Machine Data Models

Data classes used by the conversation state machine.
Moved from core/state_machine.py for better organization.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


class ConversationState(Enum):
    """Drive-thru conversation states"""
    ORDERING = "ordering"
    THINKING = "thinking"
    CLARIFYING = "clarifying"
    CONFIRMING = "confirming"
    CLOSING = "closing"
    IDLE = "idle"


class GlobalEvent(Enum):
    """Global events that can occur from any state"""
    BARGE_IN = "barge_in"
    SILENCE = "silence"
    OOS = "out_of_stock"
    SESSION_END = "session_end"


@dataclass
class OrderState:
    """Current order state"""
    line_items: List[Dict[str, Any]]
    last_mentioned_item_ref: Optional[str]
    totals: Dict[str, float]
    
    @property
    def has_order(self) -> bool:
        """Check if order has any items"""
        return len(self.line_items) > 0


@dataclass
class ConversationContext:
    """Conversation context and metadata"""
    turn_counter: int
    last_action_uuid: Optional[str]
    thinking_since: Optional[datetime]
    timeout_at: Optional[datetime]
    expectation: str  # "free_form_ordering", "menu_questions_or_wait", "single_answer"


@dataclass
class StateTransition:
    """Represents a state transition"""
    from_state: ConversationState
    to_state: ConversationState
    event: str
    guard: Optional[str]
    action: str
