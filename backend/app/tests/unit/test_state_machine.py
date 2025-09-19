"""
Unit tests for the Drive-Thru State Machine
"""

import pytest
from datetime import datetime
from app.core.state_machine import (
    DriveThruStateMachine,
    ConversationState,
    GlobalEvent,
    OrderState,
    ConversationContext
)


class TestDriveThruStateMachine:
    """Test cases for the drive-thru state machine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.state_machine = DriveThruStateMachine()
    
    def test_initial_state(self):
        """Test that state machine starts in IDLE state"""
        assert self.state_machine.get_current_state() == ConversationState.IDLE
        assert not self.state_machine.get_order_state().has_order
    
    def test_order_state_has_order(self):
        """Test order state detection"""
        # Empty order
        empty_order = OrderState(line_items=[], last_mentioned_item_ref=None, totals={})
        assert not empty_order.has_order
        
        # Order with items
        order_with_items = OrderState(
            line_items=[{"id": "li_1", "name": "Big Mac"}],
            last_mentioned_item_ref="li_1",
            totals={"subtotal": 7.49}
        )
        assert order_with_items.has_order
    
    def test_determine_event_utterance_ok(self):
        """Test event determination for clear utterances"""
        user_input = "I want a Big Mac"
        agent_outputs = {"confidence": 0.9, "needs_clarification": False}
        
        event = self.state_machine._determine_event(user_input, agent_outputs)
        assert event == "UTTERANCE_OK"
    
    def test_determine_event_utterance_unclear(self):
        """Test event determination for unclear utterances"""
        user_input = "I want something"
        agent_outputs = {"confidence": 0.5, "needs_clarification": True}
        
        event = self.state_machine._determine_event(user_input, agent_outputs)
        assert event == "UTTERANCE_UNCLEAR"
    
    def test_determine_event_user_says_done(self):
        """Test event determination for completion phrases"""
        test_phrases = ["that's it", "that's all", "done", "finished"]
        
        for phrase in test_phrases:
            event = self.state_machine._determine_event(phrase, {})
            assert event == "USER_SAYS_DONE"
    
    def test_determine_event_user_needs_time(self):
        """Test event determination for thinking phrases"""
        test_phrases = ["give me a minute", "looking", "let me think"]
        
        for phrase in test_phrases:
            event = self.state_machine._determine_event(phrase, {})
            assert event == "USER_NEEDS_TIME"
    
    def test_determine_event_user_says_never_mind(self):
        """Test event determination for cancellation phrases"""
        test_phrases = ["never mind", "skip it", "forget it"]
        
        for phrase in test_phrases:
            event = self.state_machine._determine_event(phrase, {})
            assert event == "USER_SAYS_NEVER_MIND"
    
    def test_determine_event_user_confirms(self):
        """Test event determination for confirmation phrases"""
        test_phrases = ["yes", "correct", "that's right"]
        
        for phrase in test_phrases:
            event = self.state_machine._determine_event(phrase, {})
            assert event == "USER_CONFIRMS"
    
    def test_determine_event_user_wants_changes(self):
        """Test event determination for change phrases"""
        test_phrases = ["add", "change", "modify"]
        
        for phrase in test_phrases:
            event = self.state_machine._determine_event(phrase, {})
            assert event == "USER_WANTS_CHANGES"
    
    def test_determine_event_out_of_stock(self):
        """Test event determination for out-of-stock items"""
        user_input = "I want a Big Mac"
        agent_outputs = {"out_of_stock": True, "item": "Big Mac"}
        
        event = self.state_machine._determine_event(user_input, agent_outputs)
        assert event == "E.OOS"
    
    def test_guard_has_order(self):
        """Test has_order guard"""
        # Test with empty order
        self.state_machine.order_state = OrderState(line_items=[], last_mentioned_item_ref=None, totals={})
        assert not self.state_machine._check_guard("has_order", {})
        
        # Test with order items
        self.state_machine.order_state = OrderState(
            line_items=[{"id": "li_1", "name": "Big Mac"}],
            last_mentioned_item_ref="li_1",
            totals={"subtotal": 7.49}
        )
        assert self.state_machine._check_guard("has_order", {})
    
    def test_guard_no_order(self):
        """Test no_order guard"""
        # Test with empty order
        self.state_machine.order_state = OrderState(line_items=[], last_mentioned_item_ref=None, totals={})
        assert self.state_machine._check_guard("no_order", {})
        
        # Test with order items
        self.state_machine.order_state = OrderState(
            line_items=[{"id": "li_1", "name": "Big Mac"}],
            last_mentioned_item_ref="li_1",
            totals={"subtotal": 7.49}
        )
        assert not self.state_machine._check_guard("no_order", {})
    
    def test_guard_low_confidence(self):
        """Test low_confidence guard"""
        # High confidence
        agent_outputs = {"confidence": 0.9}
        assert not self.state_machine._check_guard("low_confidence", agent_outputs)
        
        # Low confidence
        agent_outputs = {"confidence": 0.5}
        assert self.state_machine._check_guard("low_confidence", agent_outputs)
    
    def test_guard_unsafe_change(self):
        """Test unsafe_change guard"""
        # Safe change
        agent_outputs = {"unsafe_change": False}
        assert not self.state_machine._check_guard("unsafe_change", agent_outputs)
        
        # Unsafe change
        agent_outputs = {"unsafe_change": True}
        assert self.state_machine._check_guard("unsafe_change", agent_outputs)
    
    def test_find_transition_ordering_to_ordering(self):
        """Test transition from Ordering to Ordering"""
        self.state_machine.current_state = ConversationState.ORDERING
        event = "UTTERANCE_OK"
        agent_outputs = {"confidence": 0.9}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.ORDERING
        assert transition.to_state == ConversationState.ORDERING
        assert transition.event == "UTTERANCE_OK"
    
    def test_find_transition_ordering_to_clarifying(self):
        """Test transition from Ordering to Clarifying"""
        self.state_machine.current_state = ConversationState.ORDERING
        event = "UTTERANCE_UNCLEAR"
        agent_outputs = {"confidence": 0.5}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.ORDERING
        assert transition.to_state == ConversationState.CLARIFYING
        assert transition.guard == "low_confidence"
    
    def test_find_transition_ordering_to_confirming_with_order(self):
        """Test transition from Ordering to Confirming when order exists"""
        self.state_machine.current_state = ConversationState.ORDERING
        self.state_machine.order_state = OrderState(
            line_items=[{"id": "li_1", "name": "Big Mac"}],
            last_mentioned_item_ref="li_1",
            totals={"subtotal": 7.49}
        )
        event = "USER_SAYS_DONE"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.ORDERING
        assert transition.to_state == ConversationState.CONFIRMING
        assert transition.guard == "has_order"
    
    def test_find_transition_ordering_to_clarifying_no_order(self):
        """Test transition from Ordering to Clarifying when no order exists"""
        self.state_machine.current_state = ConversationState.ORDERING
        self.state_machine.order_state = OrderState(line_items=[], last_mentioned_item_ref=None, totals={})
        event = "USER_SAYS_DONE"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.ORDERING
        assert transition.to_state == ConversationState.CLARIFYING
        assert transition.guard == "no_order"
    
    def test_find_transition_ordering_to_thinking(self):
        """Test transition from Ordering to Thinking"""
        self.state_machine.current_state = ConversationState.ORDERING
        event = "USER_NEEDS_TIME"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.ORDERING
        assert transition.to_state == ConversationState.THINKING
    
    def test_find_transition_thinking_to_ordering(self):
        """Test transition from Thinking to Ordering"""
        self.state_machine.current_state = ConversationState.THINKING
        event = "USER_STARTS_ORDER"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.THINKING
        assert transition.to_state == ConversationState.ORDERING
    
    def test_find_transition_thinking_to_thinking_menu_question(self):
        """Test transition from Thinking to Thinking for menu questions"""
        self.state_machine.current_state = ConversationState.THINKING
        event = "MENU_QUESTION"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.THINKING
        assert transition.to_state == ConversationState.THINKING
    
    def test_find_transition_clarifying_to_ordering(self):
        """Test transition from Clarifying to Ordering"""
        self.state_machine.current_state = ConversationState.CLARIFYING
        event = "USER_CLARIFIES_OK"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.CLARIFYING
        assert transition.to_state == ConversationState.ORDERING
    
    def test_find_transition_confirming_to_closing(self):
        """Test transition from Confirming to Closing"""
        self.state_machine.current_state = ConversationState.CONFIRMING
        event = "USER_CONFIRMS"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.CONFIRMING
        assert transition.to_state == ConversationState.CLOSING
    
    def test_find_transition_closing_to_idle(self):
        """Test transition from Closing to Idle"""
        self.state_machine.current_state = ConversationState.CLOSING
        event = "ORDER_COMPLETE"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.CLOSING
        assert transition.to_state == ConversationState.IDLE
    
    def test_find_transition_closing_to_ordering(self):
        """Test transition from Closing to Ordering for additional items"""
        self.state_machine.current_state = ConversationState.CLOSING
        event = "ADD_MORE"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is not None
        assert transition.from_state == ConversationState.CLOSING
        assert transition.to_state == ConversationState.ORDERING
    
    def test_no_transition_found(self):
        """Test when no transition is found"""
        self.state_machine.current_state = ConversationState.IDLE
        event = "INVALID_EVENT"
        agent_outputs = {}
        
        transition = self.state_machine._find_transition(event, agent_outputs)
        assert transition is None
    
    def test_conversation_context_initialization(self):
        """Test conversation context initialization"""
        context = self.state_machine.get_conversation_context()
        assert context.turn_counter == 0
        assert context.last_action_uuid is None
        assert context.thinking_since is None
        assert context.timeout_at is None
        assert context.expectation == ""
    
    def test_set_thinking_action(self):
        """Test set_thinking action"""
        self.state_machine._set_thinking()
        context = self.state_machine.get_conversation_context()
        assert context.thinking_since is not None
        assert context.expectation == "menu_questions_or_wait"
    
    def test_cleanup_action(self):
        """Test cleanup action"""
        # Set some state
        self.state_machine.current_state = ConversationState.CLOSING
        self.state_machine.order_state = OrderState(
            line_items=[{"id": "li_1", "name": "Big Mac"}],
            last_mentioned_item_ref="li_1",
            totals={"subtotal": 7.49}
        )
        
        # Cleanup
        self.state_machine._cleanup()
        
        # Verify cleanup
        assert self.state_machine.get_current_state() == ConversationState.IDLE
        assert not self.state_machine.get_order_state().has_order
        context = self.state_machine.get_conversation_context()
        assert context.turn_counter == 0
        assert context.last_action_uuid is None
        assert context.thinking_since is None
        assert context.timeout_at is None
        assert context.expectation == ""


@pytest.mark.asyncio
class TestDriveThruStateMachineAsync:
    """Async test cases for the drive-thru state machine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.state_machine = DriveThruStateMachine()
    
    async def test_process_turn_ordering_to_ordering(self):
        """Test processing a turn that stays in Ordering"""
        self.state_machine.current_state = ConversationState.ORDERING
        
        user_input = "I want a Big Mac"
        agent_outputs = {"confidence": 0.9, "needs_clarification": False}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.ORDERING
    
    async def test_process_turn_ordering_to_thinking(self):
        """Test processing a turn that goes from Ordering to Thinking"""
        self.state_machine.current_state = ConversationState.ORDERING
        
        user_input = "give me a minute to look at the menu"
        agent_outputs = {}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.THINKING
    
    async def test_process_turn_thinking_to_ordering(self):
        """Test processing a turn that goes from Thinking to Ordering"""
        self.state_machine.current_state = ConversationState.THINKING
        
        user_input = "I want a Big Mac"
        agent_outputs = {"confidence": 0.9, "needs_clarification": False}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.ORDERING
    
    async def test_process_turn_ordering_to_clarifying(self):
        """Test processing a turn that goes from Ordering to Clarifying"""
        self.state_machine.current_state = ConversationState.ORDERING
        
        user_input = "I want something"
        agent_outputs = {"confidence": 0.5, "needs_clarification": True}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.CLARIFYING
    
    async def test_process_turn_ordering_to_confirming_with_order(self):
        """Test processing a turn that goes from Ordering to Confirming when order exists"""
        self.state_machine.current_state = ConversationState.ORDERING
        self.state_machine.order_state = OrderState(
            line_items=[{"id": "li_1", "name": "Big Mac"}],
            last_mentioned_item_ref="li_1",
            totals={"subtotal": 7.49}
        )
        
        user_input = "that's it"
        agent_outputs = {}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.CONFIRMING
    
    async def test_process_turn_confirming_to_closing(self):
        """Test processing a turn that goes from Confirming to Closing"""
        self.state_machine.current_state = ConversationState.CONFIRMING
        
        user_input = "yes, that's correct"
        agent_outputs = {}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.CLOSING
    
    async def test_process_turn_closing_to_idle(self):
        """Test processing a turn that goes from Closing to Idle"""
        self.state_machine.current_state = ConversationState.CLOSING
        
        user_input = "order complete"
        agent_outputs = {"order_complete": True}
        
        next_state = await self.state_machine.process_turn("session_123", user_input, agent_outputs)
        assert next_state == ConversationState.IDLE
