"""
Drive-Thru Conversation State Machine

Simple transition table that validates state+intent combinations.
Answers: "Given current state + intent, what should happen next?"
"""

from typing import Dict, Tuple
from dataclasses import dataclass

from ..models.state_machine_models import ConversationState
from ..commands.intent_classification_schema import IntentType
from ..constants.audio_phrases import AudioPhraseConstants, AudioPhraseType


@dataclass
class StateTransition:
    """Represents a state transition decision"""
    current_state: ConversationState
    intent: IntentType
    target_state: ConversationState
    is_valid: bool
    requires_command: bool
    response_phrase_type: AudioPhraseType


class DriveThruStateMachine:
    """
    Simple state machine that validates transitions based on state + intent combinations.
    
    Provides a lookup table for all possible state+intent pairs and determines:
    - What target state to transition to
    - Whether the transition is valid
    - Whether commands are needed
    - What response message to use
    """
    
    def __init__(self):
        """Initialize the state machine with transition table"""
        self.transitions = self._build_transition_table()
    
    def _build_transition_table(self) -> Dict[Tuple[ConversationState, IntentType], StateTransition]:
        """Build the complete transition table"""
        transitions = {}
        
        # From ORDERING state
        transitions[(ConversationState.ORDERING, IntentType.ADD_ITEM)] = StateTransition(
            ConversationState.ORDERING, IntentType.ADD_ITEM, ConversationState.ORDERING, 
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.ORDERING, IntentType.REMOVE_ITEM)] = StateTransition(
            ConversationState.ORDERING, IntentType.REMOVE_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.ORDERING, IntentType.MODIFY_ITEM)] = StateTransition(
            ConversationState.ORDERING, IntentType.MODIFY_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.ORDERING, IntentType.SET_QUANTITY)] = StateTransition(
            ConversationState.ORDERING, IntentType.SET_QUANTITY, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.ORDERING, IntentType.CLEAR_ORDER)] = StateTransition(
            ConversationState.ORDERING, IntentType.CLEAR_ORDER, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.ORDERING, IntentType.CONFIRM_ORDER)] = StateTransition(
            ConversationState.ORDERING, IntentType.CONFIRM_ORDER, ConversationState.CONFIRMING,
            True, False, AudioPhraseType.ORDER_SUMMARY
        )
        transitions[(ConversationState.ORDERING, IntentType.REPEAT)] = StateTransition(
            ConversationState.ORDERING, IntentType.REPEAT, ConversationState.ORDERING,
            True, False, AudioPhraseType.ORDER_REPEAT
        )
        transitions[(ConversationState.ORDERING, IntentType.QUESTION)] = StateTransition(
            ConversationState.ORDERING, IntentType.QUESTION, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.GREETING  # Will be overridden by question response
        )
        transitions[(ConversationState.ORDERING, IntentType.SMALL_TALK)] = StateTransition(
            ConversationState.ORDERING, IntentType.SMALL_TALK, ConversationState.ORDERING,
            True, False, AudioPhraseType.CONTINUE_ORDERING
        )
        transitions[(ConversationState.ORDERING, IntentType.UNKNOWN)] = StateTransition(
            ConversationState.ORDERING, IntentType.UNKNOWN, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.COME_AGAIN
        )
        
        # From THINKING state
        transitions[(ConversationState.THINKING, IntentType.ADD_ITEM)] = StateTransition(
            ConversationState.THINKING, IntentType.ADD_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.THINKING, IntentType.REMOVE_ITEM)] = StateTransition(
            ConversationState.THINKING, IntentType.REMOVE_ITEM, ConversationState.THINKING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.THINKING, IntentType.MODIFY_ITEM)] = StateTransition(
            ConversationState.THINKING, IntentType.MODIFY_ITEM, ConversationState.THINKING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.THINKING, IntentType.SET_QUANTITY)] = StateTransition(
            ConversationState.THINKING, IntentType.SET_QUANTITY, ConversationState.THINKING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.THINKING, IntentType.CLEAR_ORDER)] = StateTransition(
            ConversationState.THINKING, IntentType.CLEAR_ORDER, ConversationState.THINKING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.THINKING, IntentType.CONFIRM_ORDER)] = StateTransition(
            ConversationState.THINKING, IntentType.CONFIRM_ORDER, ConversationState.THINKING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.THINKING, IntentType.REPEAT)] = StateTransition(
            ConversationState.THINKING, IntentType.REPEAT, ConversationState.THINKING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.THINKING, IntentType.QUESTION)] = StateTransition(
            ConversationState.THINKING, IntentType.QUESTION, ConversationState.THINKING,
            True, False, AudioPhraseType.GREETING  # Will be overridden by question response
        )
        transitions[(ConversationState.THINKING, IntentType.SMALL_TALK)] = StateTransition(
            ConversationState.THINKING, IntentType.SMALL_TALK, ConversationState.THINKING,
            True, False, AudioPhraseType.TAKE_YOUR_TIME
        )
        transitions[(ConversationState.THINKING, IntentType.UNKNOWN)] = StateTransition(
            ConversationState.THINKING, IntentType.UNKNOWN, ConversationState.THINKING,
            True, False, AudioPhraseType.READY_TO_ORDER
        )
        
        # From CLARIFYING state
        transitions[(ConversationState.CLARIFYING, IntentType.ADD_ITEM)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.ADD_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CLARIFYING, IntentType.REMOVE_ITEM)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.REMOVE_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CLARIFYING, IntentType.MODIFY_ITEM)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.MODIFY_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CLARIFYING, IntentType.SET_QUANTITY)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.SET_QUANTITY, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CLARIFYING, IntentType.CLEAR_ORDER)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.CLEAR_ORDER, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CLARIFYING, IntentType.CONFIRM_ORDER)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.CONFIRM_ORDER, ConversationState.CLARIFYING,
            False, False, AudioPhraseType.ADD_ITEMS_FIRST
        )
        transitions[(ConversationState.CLARIFYING, IntentType.REPEAT)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.REPEAT, ConversationState.CLARIFYING,
            False, False, AudioPhraseType.NO_ORDER_YET
        )
        transitions[(ConversationState.CLARIFYING, IntentType.QUESTION)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.QUESTION, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.GREETING  # Will be overridden by question response
        )
        transitions[(ConversationState.CLARIFYING, IntentType.SMALL_TALK)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.SMALL_TALK, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.HOW_CAN_I_HELP
        )
        transitions[(ConversationState.CLARIFYING, IntentType.UNKNOWN)] = StateTransition(
            ConversationState.CLARIFYING, IntentType.UNKNOWN, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.DIDNT_UNDERSTAND
        )
        
        # From CONFIRMING state
        transitions[(ConversationState.CONFIRMING, IntentType.ADD_ITEM)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.ADD_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CONFIRMING, IntentType.REMOVE_ITEM)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.REMOVE_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CONFIRMING, IntentType.MODIFY_ITEM)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.MODIFY_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CONFIRMING, IntentType.SET_QUANTITY)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.SET_QUANTITY, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CONFIRMING, IntentType.CLEAR_ORDER)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.CLEAR_ORDER, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CONFIRMING, IntentType.CONFIRM_ORDER)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.CONFIRM_ORDER, ConversationState.CLOSING,
            True, False, AudioPhraseType.ORDER_COMPLETE
        )
        transitions[(ConversationState.CONFIRMING, IntentType.REPEAT)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.REPEAT, ConversationState.CONFIRMING,
            True, False, AudioPhraseType.ORDER_READY
        )
        transitions[(ConversationState.CONFIRMING, IntentType.QUESTION)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.QUESTION, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.GREETING  # Will be overridden by question response
        )
        transitions[(ConversationState.CONFIRMING, IntentType.SMALL_TALK)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.SMALL_TALK, ConversationState.CONFIRMING,
            True, False, AudioPhraseType.ORDER_CORRECT
        )
        transitions[(ConversationState.CONFIRMING, IntentType.UNKNOWN)] = StateTransition(
            ConversationState.CONFIRMING, IntentType.UNKNOWN, ConversationState.CLARIFYING,
            True, False, AudioPhraseType.ORDER_NOT_UNDERSTOOD
        )
        
        # From CLOSING state
        transitions[(ConversationState.CLOSING, IntentType.ADD_ITEM)] = StateTransition(
            ConversationState.CLOSING, IntentType.ADD_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.CLOSING, IntentType.REMOVE_ITEM)] = StateTransition(
            ConversationState.CLOSING, IntentType.REMOVE_ITEM, ConversationState.CLOSING,
            False, False, AudioPhraseType.ORDER_BEING_PREPARED
        )
        transitions[(ConversationState.CLOSING, IntentType.MODIFY_ITEM)] = StateTransition(
            ConversationState.CLOSING, IntentType.MODIFY_ITEM, ConversationState.CLOSING,
            False, False, AudioPhraseType.ORDER_BEING_PREPARED
        )
        transitions[(ConversationState.CLOSING, IntentType.SET_QUANTITY)] = StateTransition(
            ConversationState.CLOSING, IntentType.SET_QUANTITY, ConversationState.CLOSING,
            False, False, AudioPhraseType.ORDER_BEING_PREPARED
        )
        transitions[(ConversationState.CLOSING, IntentType.CLEAR_ORDER)] = StateTransition(
            ConversationState.CLOSING, IntentType.CLEAR_ORDER, ConversationState.CLOSING,
            False, False, AudioPhraseType.ORDER_BEING_PREPARED
        )
        transitions[(ConversationState.CLOSING, IntentType.CONFIRM_ORDER)] = StateTransition(
            ConversationState.CLOSING, IntentType.CONFIRM_ORDER, ConversationState.CLOSING,
            False, False, AudioPhraseType.ORDER_ALREADY_CONFIRMED
        )
        transitions[(ConversationState.CLOSING, IntentType.REPEAT)] = StateTransition(
            ConversationState.CLOSING, IntentType.REPEAT, ConversationState.CLOSING,
            True, False, AudioPhraseType.ORDER_PREPARED_WINDOW
        )
        transitions[(ConversationState.CLOSING, IntentType.QUESTION)] = StateTransition(
            ConversationState.CLOSING, IntentType.QUESTION, ConversationState.CLOSING,
            True, False, AudioPhraseType.GREETING  # Will be overridden by question response
        )
        transitions[(ConversationState.CLOSING, IntentType.SMALL_TALK)] = StateTransition(
            ConversationState.CLOSING, IntentType.SMALL_TALK, ConversationState.CLOSING,
            True, False, AudioPhraseType.ORDER_COMPLETE
        )
        transitions[(ConversationState.CLOSING, IntentType.UNKNOWN)] = StateTransition(
            ConversationState.CLOSING, IntentType.UNKNOWN, ConversationState.CLOSING,
            True, False, AudioPhraseType.DRIVE_TO_WINDOW
        )
        
        # From IDLE state
        transitions[(ConversationState.IDLE, IntentType.ADD_ITEM)] = StateTransition(
            ConversationState.IDLE, IntentType.ADD_ITEM, ConversationState.ORDERING,
            True, True, AudioPhraseType.GREETING  # Will be overridden by command response
        )
        transitions[(ConversationState.IDLE, IntentType.REMOVE_ITEM)] = StateTransition(
            ConversationState.IDLE, IntentType.REMOVE_ITEM, ConversationState.IDLE,
            False, False, AudioPhraseType.GREETING
        )
        transitions[(ConversationState.IDLE, IntentType.MODIFY_ITEM)] = StateTransition(
            ConversationState.IDLE, IntentType.MODIFY_ITEM, ConversationState.IDLE,
            False, False, AudioPhraseType.GREETING
        )
        transitions[(ConversationState.IDLE, IntentType.SET_QUANTITY)] = StateTransition(
            ConversationState.IDLE, IntentType.SET_QUANTITY, ConversationState.IDLE,
            False, False, AudioPhraseType.GREETING
        )
        transitions[(ConversationState.IDLE, IntentType.CLEAR_ORDER)] = StateTransition(
            ConversationState.IDLE, IntentType.CLEAR_ORDER, ConversationState.IDLE,
            False, False, AudioPhraseType.GREETING
        )
        transitions[(ConversationState.IDLE, IntentType.CONFIRM_ORDER)] = StateTransition(
            ConversationState.IDLE, IntentType.CONFIRM_ORDER, ConversationState.IDLE,
            False, False, AudioPhraseType.GREETING
        )
        transitions[(ConversationState.IDLE, IntentType.REPEAT)] = StateTransition(
            ConversationState.IDLE, IntentType.REPEAT, ConversationState.IDLE,
            False, False, AudioPhraseType.GREETING
        )
        transitions[(ConversationState.IDLE, IntentType.QUESTION)] = StateTransition(
            ConversationState.IDLE, IntentType.QUESTION, ConversationState.THINKING,
            True, False, AudioPhraseType.GREETING  # Will be overridden by question response
        )
        transitions[(ConversationState.IDLE, IntentType.SMALL_TALK)] = StateTransition(
            ConversationState.IDLE, IntentType.SMALL_TALK, ConversationState.THINKING,
            True, False, AudioPhraseType.WELCOME_MENU
        )
        transitions[(ConversationState.IDLE, IntentType.UNKNOWN)] = StateTransition(
            ConversationState.IDLE, IntentType.UNKNOWN, ConversationState.THINKING,
            True, False, AudioPhraseType.GREETING
        )
        
        return transitions
    
    def get_transition(
        self, 
        current_state: ConversationState, 
        intent: IntentType
    ) -> StateTransition:
        """
        Get transition decision for current state + intent combination.
        
        Args:
            current_state: Current conversation state
            intent: User intent
            
        Returns:
            StateTransition with target state, validity, and action info
        """
        key = (current_state, intent)
        return self.transitions.get(key, StateTransition(
            current_state, intent, current_state, False, False,
            AudioPhraseType.CANT_HELP_RIGHT_NOW
        ))
    
    def is_valid_transition(
        self, 
        current_state: ConversationState, 
        intent: IntentType
    ) -> bool:
        """Check if transition is valid without returning full details"""
        transition = self.get_transition(current_state, intent)
        return transition.is_valid
    
