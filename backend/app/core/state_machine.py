"""
Drive-Thru Conversation State Machine

Manages conversation flow and order processing with clear states, transitions, and guardrails.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import json


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


class DriveThruStateMachine:
    """
    State machine for managing drive-thru conversations
    
    Handles state transitions, guards, and global events for order processing.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.current_state = ConversationState.IDLE
        self.order_state = OrderState(line_items=[], last_mentioned_item_ref=None, totals={})
        self.conversation_context = ConversationContext(
            turn_counter=0,
            last_action_uuid=None,
            thinking_since=None,
            timeout_at=None,
            expectation=""
        )
        
        # Define state transitions
        self.transitions = self._build_transition_table()
    
    def _build_transition_table(self) -> List[StateTransition]:
        """Build the state transition table"""
        return [
            # Ordering state transitions
            StateTransition(ConversationState.ORDERING, ConversationState.ORDERING, "UTTERANCE_OK", None, "apply_diffs_set_referent"),
            StateTransition(ConversationState.ORDERING, ConversationState.CLARIFYING, "UTTERANCE_UNCLEAR", "low_confidence", "ask_targeted_question"),
            StateTransition(ConversationState.ORDERING, ConversationState.CONFIRMING, "USER_SAYS_DONE", "has_order", "summarize"),
            StateTransition(ConversationState.ORDERING, ConversationState.CLARIFYING, "USER_SAYS_DONE", "no_order", "ask_start_order_prompt"),
            StateTransition(ConversationState.ORDERING, ConversationState.THINKING, "USER_NEEDS_TIME", None, "set_thinking"),
            StateTransition(ConversationState.ORDERING, ConversationState.CLARIFYING, "E.OOS", None, "propose_alternative"),
            
            # Thinking state transitions
            StateTransition(ConversationState.THINKING, ConversationState.ORDERING, "USER_STARTS_ORDER", None, "enable_parsing"),
            StateTransition(ConversationState.THINKING, ConversationState.THINKING, "MENU_QUESTION", None, "answer_menu"),
            StateTransition(ConversationState.THINKING, ConversationState.THINKING, "E.SILENCE", None, "nudge"),
            
            # Clarifying state transitions
            StateTransition(ConversationState.CLARIFYING, ConversationState.ORDERING, "USER_CLARIFIES_OK", None, "apply_if_actionable"),
            StateTransition(ConversationState.CLARIFYING, ConversationState.ORDERING, "USER_SAYS_NEVER_MIND", "has_order", "resume_order"),
            StateTransition(ConversationState.CLARIFYING, ConversationState.THINKING, "USER_SAYS_NEVER_MIND", "no_order", "return_to_thinking"),
            StateTransition(ConversationState.CLARIFYING, ConversationState.THINKING, "STILL_UNCLEAR", None, "give_pattern_hint"),
            StateTransition(ConversationState.CLARIFYING, ConversationState.CLARIFYING, "E.OOS", None, "propose_alternative"),
            
            # Confirming state transitions
            StateTransition(ConversationState.CONFIRMING, ConversationState.CLOSING, "USER_CONFIRMS", None, "finalize_ticket"),
            StateTransition(ConversationState.CONFIRMING, ConversationState.ORDERING, "USER_WANTS_CHANGES", None, "apply_diffs"),
            StateTransition(ConversationState.CONFIRMING, ConversationState.CLARIFYING, "USER_SAYS_NOT_RIGHT", None, "ask_disambiguation"),
            StateTransition(ConversationState.CONFIRMING, ConversationState.CONFIRMING, "BIG_CHANGE", "unsafe_change", "re_summary"),
            
            # Closing state transitions
            StateTransition(ConversationState.CLOSING, ConversationState.IDLE, "ORDER_COMPLETE", None, "cleanup"),
            StateTransition(ConversationState.CLOSING, ConversationState.ORDERING, "ADD_MORE", None, "resume_order"),
        ]
    
    async def process_turn(self, session_id: str, user_input: str, agent_outputs: Dict[str, Any]) -> ConversationState:
        """
        Process a conversation turn and determine next state
        
        Args:
            session_id: Unique session identifier
            user_input: User's speech input
            agent_outputs: Results from agents (parser, order updater, etc.)
            
        Returns:
            Next conversation state
        """
        # Load current state from Redis if available
        if self.redis:
            await self._load_state(session_id)
        
        # Determine event type from user input and agent outputs
        event = self._determine_event(user_input, agent_outputs)
        
        # Find applicable transition
        transition = self._find_transition(event, agent_outputs)
        
        if transition:
            # Execute transition
            await self._execute_transition(transition, user_input, agent_outputs)
            
            # Update state
            self.current_state = transition.to_state
            
            # Save state to Redis if available
            if self.redis:
                await self._save_state(session_id)
        
        return self.current_state
    
    def _determine_event(self, user_input: str, agent_outputs: Dict[str, Any]) -> str:
        """Determine the event type from user input and agent outputs"""
        user_lower = user_input.lower()
        
        # Check for specific phrases
        if any(phrase in user_lower for phrase in ["that's it", "that's all", "done", "finished"]):
            return "USER_SAYS_DONE"
        elif any(phrase in user_lower for phrase in ["give me a minute", "looking", "let me think"]):
            return "USER_NEEDS_TIME"
        elif any(phrase in user_lower for phrase in ["never mind", "skip it", "forget it"]):
            return "USER_SAYS_NEVER_MIND"
        elif any(phrase in user_lower for phrase in ["that's not right", "that's wrong", "no"]):
            return "USER_SAYS_NOT_RIGHT"
        elif any(phrase in user_lower for phrase in ["yes", "correct", "that's right"]):
            return "USER_CONFIRMS"
        elif any(phrase in user_lower for phrase in ["add", "change", "modify"]):
            return "USER_WANTS_CHANGES"
        elif agent_outputs.get("needs_clarification", False):
            return "UTTERANCE_UNCLEAR"
        elif agent_outputs.get("confidence", 1.0) < 0.7:
            return "UTTERANCE_UNCLEAR"
        elif agent_outputs.get("out_of_stock", False):
            return "E.OOS"
        else:
            return "UTTERANCE_OK"
    
    def _find_transition(self, event: str, agent_outputs: Dict[str, Any]) -> Optional[StateTransition]:
        """Find the applicable transition for the current state and event"""
        for transition in self.transitions:
            if (transition.from_state == self.current_state and 
                transition.event == event):
                
                # Check guard conditions
                if transition.guard and not self._check_guard(transition.guard, agent_outputs):
                    continue
                
                return transition
        
        return None
    
    def _check_guard(self, guard: str, agent_outputs: Dict[str, Any]) -> bool:
        """Check guard conditions"""
        if guard == "low_confidence":
            return agent_outputs.get("confidence", 1.0) < 0.7
        elif guard == "has_order":
            return self.order_state.has_order
        elif guard == "no_order":
            return not self.order_state.has_order
        elif guard == "unsafe_change":
            # Check if the change is high-risk (e.g., removing many items)
            return agent_outputs.get("unsafe_change", False)
        
        return True
    
    async def _execute_transition(self, transition: StateTransition, user_input: str, agent_outputs: Dict[str, Any]):
        """Execute the transition action"""
        if transition.action == "apply_diffs_set_referent":
            await self._apply_diffs_set_referent(agent_outputs)
        elif transition.action == "ask_targeted_question":
            await self._ask_targeted_question(agent_outputs)
        elif transition.action == "summarize":
            await self._summarize_order()
        elif transition.action == "ask_start_order_prompt":
            await self._ask_start_order_prompt()
        elif transition.action == "set_thinking":
            await self._set_thinking()
        elif transition.action == "propose_alternative":
            await self._propose_alternative(agent_outputs)
        elif transition.action == "enable_parsing":
            await self._enable_parsing()
        elif transition.action == "answer_menu":
            await self._answer_menu(user_input)
        elif transition.action == "nudge":
            await self._nudge_customer()
        elif transition.action == "apply_if_actionable":
            await self._apply_if_actionable(agent_outputs)
        elif transition.action == "resume_order":
            await self._resume_order()
        elif transition.action == "return_to_thinking":
            await self._return_to_thinking()
        elif transition.action == "give_pattern_hint":
            await self._give_pattern_hint()
        elif transition.action == "finalize_ticket":
            await self._finalize_ticket()
        elif transition.action == "apply_diffs":
            await self._apply_diffs(agent_outputs)
        elif transition.action == "ask_disambiguation":
            await self._ask_disambiguation(agent_outputs)
        elif transition.action == "re_summary":
            await self._re_summary()
        elif transition.action == "cleanup":
            await self._cleanup()
    
    # Action implementations (stubs for now)
    async def _apply_diffs_set_referent(self, agent_outputs: Dict[str, Any]):
        """Apply order diffs and set referent"""
        self.conversation_context.turn_counter += 1
        self.conversation_context.last_action_uuid = agent_outputs.get("action_uuid")
        # TODO: Implement actual order state updates
    
    async def _ask_targeted_question(self, agent_outputs: Dict[str, Any]):
        """Ask one targeted question for clarification"""
        self.conversation_context.expectation = "single_answer"
        # TODO: Implement question generation
    
    async def _summarize_order(self):
        """Summarize current order"""
        # TODO: Implement order summarization
    
    async def _ask_start_order_prompt(self):
        """Ask customer to start ordering"""
        # TODO: Implement start order prompt
    
    async def _set_thinking(self):
        """Set thinking mode"""
        self.conversation_context.thinking_since = datetime.now()
        self.conversation_context.expectation = "menu_questions_or_wait"
    
    async def _propose_alternative(self, agent_outputs: Dict[str, Any]):
        """Propose alternative for out-of-stock item"""
        # TODO: Implement alternative proposal
    
    async def _enable_parsing(self):
        """Enable parsing mode"""
        self.conversation_context.expectation = "free_form_ordering"
    
    async def _answer_menu(self, user_input: str):
        """Answer menu question"""
        # TODO: Implement menu question answering
    
    async def _nudge_customer(self):
        """Nudge customer who hasn't responded"""
        # TODO: Implement customer nudge
    
    async def _apply_if_actionable(self, agent_outputs: Dict[str, Any]):
        """Apply changes if actionable"""
        # TODO: Implement actionable change application
    
    async def _resume_order(self):
        """Resume order building"""
        self.conversation_context.expectation = "free_form_ordering"
    
    async def _return_to_thinking(self):
        """Return to thinking mode"""
        self.conversation_context.expectation = "menu_questions_or_wait"
    
    async def _give_pattern_hint(self):
        """Give pattern hint for unclear input"""
        # TODO: Implement pattern hint generation
    
    async def _finalize_ticket(self):
        """Finalize order ticket"""
        # TODO: Implement ticket finalization
    
    async def _apply_diffs(self, agent_outputs: Dict[str, Any]):
        """Apply order diffs"""
        # TODO: Implement diff application
    
    async def _ask_disambiguation(self, agent_outputs: Dict[str, Any]):
        """Ask for disambiguation"""
        # TODO: Implement disambiguation question
    
    async def _re_summary(self):
        """Re-summarize after unsafe change"""
        # TODO: Implement re-summarization
    
    async def _cleanup(self):
        """Cleanup session resources"""
        self.current_state = ConversationState.IDLE
        self.order_state = OrderState(line_items=[], last_mentioned_item_ref=None, totals={})
        self.conversation_context = ConversationContext(
            turn_counter=0,
            last_action_uuid=None,
            thinking_since=None,
            timeout_at=None,
            expectation=""
        )
    
    async def _load_state(self, session_id: str):
        """Load state from Redis"""
        # TODO: Implement Redis state loading
        pass
    
    async def _save_state(self, session_id: str):
        """Save state to Redis"""
        # TODO: Implement Redis state saving
        pass
    
    def get_current_state(self) -> ConversationState:
        """Get current conversation state"""
        return self.current_state
    
    def get_order_state(self) -> OrderState:
        """Get current order state"""
        return self.order_state
    
    def get_conversation_context(self) -> ConversationContext:
        """Get current conversation context"""
        return self.conversation_context
