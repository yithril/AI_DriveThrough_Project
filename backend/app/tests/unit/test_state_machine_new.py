"""
Unit tests for the new simplified state machine
"""

import pytest
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, backend_dir)

from app.core.state_machine import DriveThruStateMachine, StateTransition
from app.models.state_machine_models import ConversationState
from app.commands.command_contract import IntentType
from app.constants.audio_phrases import AudioPhraseType, AudioPhraseConstants


class TestDriveThruStateMachine:
    """Test cases for the new simplified state machine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.state_machine = DriveThruStateMachine()
    
    def test_command_requiring_transitions(self):
        """Test state+intent pairs that should require commands"""
        
        # ORDERING state - all order modification intents should require commands
        command_intents = [
            IntentType.ADD_ITEM,
            IntentType.REMOVE_ITEM, 
            IntentType.MODIFY_ITEM,
            IntentType.SET_QUANTITY,
            IntentType.CLEAR_ORDER
        ]
        
        for intent in command_intents:
            transition = self.state_machine.get_transition(ConversationState.ORDERING, intent)
            assert transition.requires_command, f"{intent} in ORDERING should require command"
            assert transition.is_valid, f"{intent} in ORDERING should be valid"
            assert transition.target_state == ConversationState.ORDERING, f"{intent} should stay in ORDERING"
    
    def test_command_requiring_from_other_states(self):
        """Test that ADD_ITEM from other states also requires commands"""
        
        # ADD_ITEM should require commands from most states
        add_item_states = [
            ConversationState.THINKING,
            ConversationState.CLARIFYING, 
            ConversationState.CONFIRMING,
            ConversationState.CLOSING,
            ConversationState.IDLE
        ]
        
        for state in add_item_states:
            transition = self.state_machine.get_transition(state, IntentType.ADD_ITEM)
            if transition.is_valid:  # Only test valid transitions
                assert transition.requires_command, f"ADD_ITEM from {state} should require command"
    
    def test_finisher_transitions(self):
        """Test 'finisher' transitions that complete the order flow"""
        
        # ORDERING -> CONFIRMING (user says done)
        transition = self.state_machine.get_transition(ConversationState.ORDERING, IntentType.CONFIRM_ORDER)
        assert transition.is_valid
        assert not transition.requires_command  # Just confirmation, no command needed
        assert transition.target_state == ConversationState.CONFIRMING
        assert transition.response_phrase_type == AudioPhraseType.ORDER_SUMMARY
        
        # CONFIRMING -> CLOSING (user confirms order)
        transition = self.state_machine.get_transition(ConversationState.CONFIRMING, IntentType.CONFIRM_ORDER)
        assert transition.is_valid
        assert not transition.requires_command  # Just final confirmation
        assert transition.target_state == ConversationState.CLOSING
        assert transition.response_phrase_type == AudioPhraseType.ORDER_COMPLETE
    
    def test_invalid_finisher_attempts(self):
        """Test attempts to finish when no order exists"""
        
        # THINKING -> CONFIRM_ORDER should be invalid (no order to confirm)
        transition = self.state_machine.get_transition(ConversationState.THINKING, IntentType.CONFIRM_ORDER)
        assert not transition.is_valid
        assert transition.response_phrase_type == AudioPhraseType.NO_ORDER_YET
        
        # CLARIFYING -> CONFIRM_ORDER should be invalid (no order to confirm)  
        transition = self.state_machine.get_transition(ConversationState.CLARIFYING, IntentType.CONFIRM_ORDER)
        assert not transition.is_valid
        assert transition.response_phrase_type == AudioPhraseType.ADD_ITEMS_FIRST
        
        # IDLE -> CONFIRM_ORDER should be invalid (no order to confirm)
        transition = self.state_machine.get_transition(ConversationState.IDLE, IntentType.CONFIRM_ORDER)
        assert not transition.is_valid
        assert transition.response_phrase_type == AudioPhraseType.GREETING
    
    def test_response_only_transitions(self):
        """Test transitions that just need responses, not commands"""
        
        # REPEAT intent - should just repeat order, no command needed
        transition = self.state_machine.get_transition(ConversationState.ORDERING, IntentType.REPEAT)
        assert transition.is_valid
        assert not transition.requires_command
        assert transition.response_phrase_type == AudioPhraseType.ORDER_REPEAT
        
        # SMALL_TALK - should just respond, no command needed
        transition = self.state_machine.get_transition(ConversationState.ORDERING, IntentType.SMALL_TALK)
        assert transition.is_valid
        assert not transition.requires_command
        assert transition.response_phrase_type == AudioPhraseType.CONTINUE_ORDERING
        
        # QUESTION - should just answer, no command needed
        transition = self.state_machine.get_transition(ConversationState.ORDERING, IntentType.QUESTION)
        assert transition.is_valid
        assert not transition.requires_command
        assert transition.target_state == ConversationState.CLARIFYING
    
    def test_closing_state_restrictions(self):
        """Test that CLOSING state restricts most order modifications"""
        
        # Most order modifications should be invalid in CLOSING state
        invalid_in_closing = [
            IntentType.REMOVE_ITEM,
            IntentType.MODIFY_ITEM,
            IntentType.SET_QUANTITY,
            IntentType.CLEAR_ORDER,
            IntentType.CONFIRM_ORDER
        ]
        
        for intent in invalid_in_closing:
            transition = self.state_machine.get_transition(ConversationState.CLOSING, intent)
            assert not transition.is_valid, f"{intent} should be invalid in CLOSING state"
            assert transition.response_phrase_type in [
                AudioPhraseType.ORDER_BEING_PREPARED,
                AudioPhraseType.ORDER_ALREADY_CONFIRMED
            ]
        
        # ADD_ITEM should still be valid (customer wants to add more)
        transition = self.state_machine.get_transition(ConversationState.CLOSING, IntentType.ADD_ITEM)
        assert transition.is_valid
        assert transition.requires_command
        assert transition.target_state == ConversationState.ORDERING
    
    def test_thinking_state_restrictions(self):
        """Test that THINKING state restricts order operations without items"""
        
        # Order operations without items should be invalid in THINKING
        invalid_without_order = [
            IntentType.REMOVE_ITEM,
            IntentType.MODIFY_ITEM,
            IntentType.SET_QUANTITY,
            IntentType.CLEAR_ORDER,
            IntentType.CONFIRM_ORDER,
            IntentType.REPEAT
        ]
        
        for intent in invalid_without_order:
            transition = self.state_machine.get_transition(ConversationState.THINKING, intent)
            assert not transition.is_valid, f"{intent} should be invalid in THINKING without order"
            assert transition.response_phrase_type == AudioPhraseType.NO_ORDER_YET
    
    def test_phrase_type_resolution(self):
        """Test that phrase types are returned correctly from state machine"""
        
        # Test that state machine returns the correct AudioPhraseType
        restaurant_name = "Test Burger"
        
        # GREETING should be returned for UNKNOWN intent in IDLE state
        transition = self.state_machine.get_transition(ConversationState.IDLE, IntentType.UNKNOWN)
        assert transition.response_phrase_type == AudioPhraseType.GREETING
        
        # Test that AudioPhraseConstants can resolve the phrase type to text
        text = AudioPhraseConstants.get_phrase_text(transition.response_phrase_type, restaurant_name)
        assert restaurant_name in text
        
        # NO_ORDER_YET should be returned for CONFIRM_ORDER in THINKING state
        transition = self.state_machine.get_transition(ConversationState.THINKING, IntentType.CONFIRM_ORDER)
        assert transition.response_phrase_type == AudioPhraseType.NO_ORDER_YET
        
        text = AudioPhraseConstants.get_phrase_text(transition.response_phrase_type, restaurant_name)
        assert "You don't have an order yet" in text
        
        # WELCOME_MENU should be returned for SMALL_TALK in IDLE state
        transition = self.state_machine.get_transition(ConversationState.IDLE, IntentType.SMALL_TALK)
        assert transition.response_phrase_type == AudioPhraseType.WELCOME_MENU
        
        text = AudioPhraseConstants.get_phrase_text(transition.response_phrase_type, restaurant_name)
        assert restaurant_name in text
        assert "Take your time looking at our menu" in text
    
    def test_upselling_phrases_available(self):
        """Test that upselling phrases are available in constants (not yet integrated)"""
        
        # Verify upselling phrases exist in AudioPhraseType
        assert hasattr(AudioPhraseType, 'UPSELL_1')
        assert hasattr(AudioPhraseType, 'UPSELL_2') 
        assert hasattr(AudioPhraseType, 'UPSELL_3')
        
        # Verify they have text
        upsell_1_text = AudioPhraseConstants.get_phrase_text(AudioPhraseType.UPSELL_1)
        assert "special today" in upsell_1_text
        
        upsell_2_text = AudioPhraseConstants.get_phrase_text(AudioPhraseType.UPSELL_2)
        assert "combo meal" in upsell_2_text
        
        upsell_3_text = AudioPhraseConstants.get_phrase_text(AudioPhraseType.UPSELL_3)
        assert "add a drink" in upsell_3_text
    
    def test_state_transition_coverage(self):
        """Test that we have transitions defined for all state+intent combinations"""
        
        states = list(ConversationState)
        intents = list(IntentType)
        
        # Should have 6 states × 10 intents = 60 combinations
        total_combinations = len(states) * len(intents)
        assert len(self.state_machine.transitions) == total_combinations
        
        # Verify every combination is covered
        for state in states:
            for intent in intents:
                key = (state, intent)
                assert key in self.state_machine.transitions, f"Missing transition for {state} + {intent}"
