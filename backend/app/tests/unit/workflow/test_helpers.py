"""
Test helpers for workflow node testing

Provides utilities and factories for creating test data structures
used in workflow node unit tests.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState, OrderState, ConversationContext
from app.commands.intent_classification_schema import IntentType
from app.dto.order_result import OrderResult, CommandBatchResult
from app.constants.audio_phrases import AudioPhraseType


class ConversationWorkflowStateBuilder:
    """
    Builder pattern for creating ConversationWorkflowState test instances.
    
    Provides a fluent interface for setting up test states with default values
    and easy customization.
    """
    
    def __init__(self):
        """Initialize with default test values"""
        self._session_id = "test-session-123"
        self._restaurant_id = "1"
        self._user_input = "I'd like a Big Mac"
        self._conversation_history = []
        self._current_state = ConversationState.IDLE
        self._target_state = None
        self._order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        self._conversation_context = ConversationContext(
            turn_counter=1,
            last_action_uuid=None,
            thinking_since=None,
            timeout_at=None,
            expectation="free_form_ordering"
        )
        
        # Intent data
        self._intent_type = None
        self._intent_confidence = 0.0
        self._intent_slots = {}
        
        # State machine results
        self._transition_requires_command = False
        self._transition_is_valid = True
        self._response_phrase_type = None
        
        # Commands and results
        self._commands = []
        self._command_batch_result = None
        
        # Response data
        self._response_text = ""
        self._audio_url = None
        
        # Order tracking
        self._order_state_changed = False
        
        # Error handling
        self._errors = []
    
    def with_session_id(self, session_id: str) -> 'ConversationWorkflowStateBuilder':
        """Set the session ID"""
        self._session_id = session_id
        return self
    
    def with_restaurant_id(self, restaurant_id) -> 'ConversationWorkflowStateBuilder':
        """Set the restaurant ID (can be string or int, will be converted to string)"""
        self._restaurant_id = str(restaurant_id)
        return self
    
    
    def with_user_input(self, user_input: str) -> 'ConversationWorkflowStateBuilder':
        """Set the user input"""
        self._user_input = user_input
        return self
    
    def with_current_state(self, state: ConversationState) -> 'ConversationWorkflowStateBuilder':
        """Set the current conversation state"""
        self._current_state = state
        return self
    
    def with_target_state(self, state: ConversationState) -> 'ConversationWorkflowStateBuilder':
        """Set the target conversation state"""
        self._target_state = state
        return self
    
    def with_intent(self, intent_type: IntentType, confidence: float = 0.95, slots: Dict[str, Any] = None) -> 'ConversationWorkflowStateBuilder':
        """Set intent classification data"""
        self._intent_type = intent_type
        self._intent_confidence = confidence
        self._intent_slots = slots or {}
        return self
    
    def with_intent_classification(self, intent_type: IntentType, confidence: float = 0.95, slots: Dict[str, Any] = None) -> 'ConversationWorkflowStateBuilder':
        """Set intent information"""
        self._intent_type = intent_type
        self._intent_confidence = confidence
        self._intent_slots = slots or {}
        return self
    
    def with_transition_result(self, requires_command: bool = False, is_valid: bool = True, phrase_type: AudioPhraseType = None) -> 'ConversationWorkflowStateBuilder':
        """Set state machine transition results"""
        self._transition_requires_command = requires_command
        self._transition_is_valid = is_valid
        self._response_phrase_type = phrase_type
        return self
    
    def with_commands(self, commands: List[Dict[str, Any]]) -> 'ConversationWorkflowStateBuilder':
        """Set command dictionaries"""
        self._commands = commands
        return self
    
    def with_command_batch_result(self, result: CommandBatchResult) -> 'ConversationWorkflowStateBuilder':
        """Set command batch result"""
        self._command_batch_result = result
        return self
    
    def with_response(self, text: str, audio_url: str = None) -> 'ConversationWorkflowStateBuilder':
        """Set response text and optional audio URL"""
        self._response_text = text
        if audio_url:
            self._audio_url = audio_url
        return self
    
    def with_audio_url(self, audio_url: str) -> 'ConversationWorkflowStateBuilder':
        """Set audio URL"""
        self._audio_url = audio_url
        return self
    
    def with_errors(self, errors: List[str]) -> 'ConversationWorkflowStateBuilder':
        """Set error messages"""
        self._errors = errors
        return self
    
    def with_order_state_changed(self, changed: bool = True) -> 'ConversationWorkflowStateBuilder':
        """Set whether order state was changed"""
        self._order_state_changed = changed
        return self
    
    def build(self) -> ConversationWorkflowState:
        """Build the ConversationWorkflowState instance"""
        return ConversationWorkflowState(
            session_id=self._session_id,
            restaurant_id=self._restaurant_id,
            user_input=self._user_input,
            conversation_history=self._conversation_history,
            current_state=self._current_state,
            target_state=self._target_state,
            order_state=self._order_state,
            conversation_context=self._conversation_context,
            intent_type=self._intent_type,
            intent_confidence=self._intent_confidence,
            intent_slots=self._intent_slots,
            transition_requires_command=self._transition_requires_command,
            transition_is_valid=self._transition_is_valid,
            response_phrase_type=self._response_phrase_type,
            commands=self._commands,
            command_batch_result=self._command_batch_result,
            response_text=self._response_text,
            audio_url=self._audio_url,
            order_state_changed=self._order_state_changed,
            errors=self._errors
        )


def create_test_state(**kwargs) -> ConversationWorkflowState:
    """
    Quick factory function for creating test states with common defaults.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ConversationWorkflowState: Configured test state
    """
    builder = ConversationWorkflowStateBuilder()
    
    # Apply any overrides
    for key, value in kwargs.items():
        if hasattr(builder, f'with_{key}'):
            getattr(builder, f'with_{key}')(value)
    
    return builder.build()


def create_successful_command_batch_result(commands: List[str] = None) -> CommandBatchResult:
    """
    Create a successful CommandBatchResult for testing.
    
    Args:
        commands: List of command names that were executed
        
    Returns:
        CommandBatchResult: Successful batch result
    """
    if commands is None:
        commands = ["add_item"]
    
    results = [OrderResult.success(f"{cmd} executed successfully") for cmd in commands]
    
    return CommandBatchResult(
        results=results,
        total_commands=len(commands),
        successful_commands=len(commands),
        failed_commands=0,
        warnings_count=0,
        errors_by_category={},
        errors_by_code={},
        summary_message=f"Successfully executed {len(commands)} command(s)",
        command_family="ADD_ITEM",
        batch_outcome="ALL_SUCCESS",
        first_error_code=None,
        response_payload=None
    )


def create_failed_command_batch_result(error_message: str = "Command failed") -> CommandBatchResult:
    """
    Create a failed CommandBatchResult for testing.
    
    Args:
        error_message: Error message for the failure
        
    Returns:
        CommandBatchResult: Failed batch result
    """
    return CommandBatchResult(
        results=[OrderResult.error(error_message)],
        total_commands=1,
        successful_commands=0,
        failed_commands=1,
        warnings_count=0,
        errors_by_category={},
        errors_by_code={},
        summary_message=error_message,
        command_family="ADD_ITEM",
        batch_outcome="ALL_FAILED",
        first_error_code="ITEM_UNAVAILABLE",
        response_payload=None
    )


def create_add_item_command_dict(menu_item_id: int = 1, quantity: int = 1, size: str = None) -> Dict[str, Any]:
    """
    Create a typical ADD_ITEM command dictionary for testing.
    
    Args:
        menu_item_id: Menu item ID to add
        quantity: Quantity to add
        size: Optional size
        
    Returns:
        Dict: Command dictionary
    """
    command = {
        "intent": "ADD_ITEM",
        "menu_item_id": menu_item_id,
        "quantity": quantity
    }
    
    if size:
        command["size"] = size
    
    return command


def create_remove_item_command_dict(order_item_id: int = 1) -> Dict[str, Any]:
    """
    Create a typical REMOVE_ITEM command dictionary for testing.
    
    Args:
        order_item_id: Order item ID to remove
        
    Returns:
        Dict: Command dictionary
    """
    return {
        "intent": "REMOVE_ITEM",
        "order_item_id": order_item_id
    }


def create_confirm_order_command_dict() -> Dict[str, Any]:
    """
    Create a typical CONFIRM_ORDER command dictionary for testing.
    
    Returns:
        Dict: Command dictionary
    """
    return {
        "intent": "CONFIRM_ORDER"
    }


def create_clear_order_command_dict() -> Dict[str, Any]:
    """
    Create a typical CLEAR_ORDER command dictionary for testing.
    
    Returns:
        Dict: Command dictionary
    """
    return {
        "intent": "CLEAR_ORDER"
    }


# Common test scenarios
def create_ordering_state() -> ConversationWorkflowState:
    """Create a state representing a customer in the ordering process"""
    return (ConversationWorkflowStateBuilder()
            .with_current_state(ConversationState.ORDERING)
            .with_intent(IntentType.ADD_ITEM, confidence=0.95)
            .with_transition_result(requires_command=True)
            .with_commands([create_add_item_command_dict()])
            .build())


def create_confirmation_state() -> ConversationWorkflowState:
    """Create a state representing a customer confirming their order"""
    return (ConversationWorkflowStateBuilder()
            .with_current_state(ConversationState.CONFIRMING)
            .with_intent(IntentType.CONFIRM_ORDER, confidence=0.98)
            .with_transition_result(requires_command=True)
            .with_commands([create_confirm_order_command_dict()])
            .build())


def create_greeting_state() -> ConversationWorkflowState:
    """Create a state representing a greeting scenario"""
    return (ConversationWorkflowStateBuilder()
            .with_current_state(ConversationState.IDLE)
            .with_intent(IntentType.SMALL_TALK, confidence=0.85)
            .with_transition_result(requires_command=False, phrase_type=AudioPhraseType.GREETING)
            .build())


def create_error_state(error_message: str = "Something went wrong") -> ConversationWorkflowState:
    """Create a state representing an error scenario"""
    return (ConversationWorkflowStateBuilder()
            .with_errors([error_message])
            .with_transition_result(is_valid=False, phrase_type=AudioPhraseType.ERROR_MESSAGE)
            .build())
