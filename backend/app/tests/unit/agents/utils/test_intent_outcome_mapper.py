"""
Unit tests for IntentOutcomeMapper

Tests the pure function that maps intent + outcome to routing decisions.
"""

import pytest
from app.agents.utils.intent_outcome_mapper import IntentOutcomeMapper, RoutingDecision


class TestIntentOutcomeMapper:
    """Test the IntentOutcomeMapper pure function"""
    
    def test_map_add_item_all_success(self):
        """Test ADD_ITEM + ALL_SUCCESS mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("ADD_ITEM", "ALL_SUCCESS")
        
        assert result.next_node == "canned_response"
        assert result.template_purpose == "Added that to your order. Would you like anything else?"
        assert result.template_key == "ITEM_ADDED_SUCCESS"
        assert result.args == {}
    
    def test_map_add_item_partial_success(self):
        """Test ADD_ITEM + PARTIAL_SUCCESS mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("ADD_ITEM", "PARTIAL_SUCCESS")
        
        assert result.next_node == "follow_up_agent"
        assert result.template_purpose == "Ask for clarification or continue"
        assert result.template_key == "ADDITEM_PARTIAL_SUCCESS"
        assert result.args == {}
    
    def test_map_add_item_all_failed(self):
        """Test ADD_ITEM + ALL_FAILED mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("ADD_ITEM", "ALL_FAILED")
        
        assert result.next_node == "follow_up_agent"
        assert result.template_purpose == "I could not add that. Ask which item"
        assert result.template_key == "ADDITEM_ALL_FAILED"
        assert result.args == {}
    
    def test_map_add_item_fatal_system(self):
        """Test ADD_ITEM + FATAL_SYSTEM mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("ADD_ITEM", "FATAL_SYSTEM")
        
        assert result.next_node == "canned_response"
        assert result.template_purpose == "I'm sorry, I'm having some technical difficulties. Please try again."
        assert result.template_key == "SYSTEM_ERROR_RETRY"
        assert result.args == {}
    
    def test_map_question_all_success(self):
        """Test QUESTION + ALL_SUCCESS mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("QUESTION", "ALL_SUCCESS")
        
        assert result.next_node == "dynamic_voice_response"
        assert result.template_purpose == "Generate answer"
        assert result.template_key == "QUESTION_ALL_SUCCESS"
        assert result.args == {}
    
    def test_map_clear_order_all_success(self):
        """Test CLEAR_ORDER + ALL_SUCCESS mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("CLEAR_ORDER", "ALL_SUCCESS")
        
        assert result.next_node == "canned_response"
        assert result.template_purpose == "Your order has been cleared."
        assert result.template_key == "ORDER_CLEARED_SUCCESS"
        assert result.args == {}
    
    def test_map_repeat_all_success(self):
        """Test REPEAT + ALL_SUCCESS mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("REPEAT", "ALL_SUCCESS")
        
        assert result.next_node == "dynamic_voice_response"
        assert result.template_purpose == "Repeat order summary"
        assert result.template_key == "REPEAT_ALL_SUCCESS"
        assert result.args == {}
    
    def test_map_remove_item_all_success(self):
        """Test REMOVE_ITEM + ALL_SUCCESS mapping"""
        result = IntentOutcomeMapper.map_intent_outcome("REMOVE_ITEM", "ALL_SUCCESS")
        
        assert result.next_node == "canned_response"
        assert result.template_purpose == "Removed that from your order. Would you like anything else?"
        assert result.template_key == "ITEM_REMOVED_SUCCESS"
        assert result.args == {}
    
    def test_map_unknown_intent(self):
        """Test unknown intent raises ValueError"""
        with pytest.raises(ValueError, match="Unknown intent: INVALID_INTENT"):
            IntentOutcomeMapper.map_intent_outcome("INVALID_INTENT", "ALL_SUCCESS")
    
    def test_map_unknown_outcome(self):
        """Test unknown outcome raises ValueError"""
        with pytest.raises(ValueError, match="Unknown outcome 'INVALID_OUTCOME' for intent 'ADD_ITEM'"):
            IntentOutcomeMapper.map_intent_outcome("ADD_ITEM", "INVALID_OUTCOME")
    
    def test_case_insensitive(self):
        """Test that intent and outcome are case insensitive"""
        result1 = IntentOutcomeMapper.map_intent_outcome("add_item", "all_success")
        result2 = IntentOutcomeMapper.map_intent_outcome("ADD_ITEM", "ALL_SUCCESS")
        
        assert result1.next_node == result2.next_node
        assert result1.template_purpose == result2.template_purpose
        assert result1.template_key == result2.template_key
        assert result1.args == result2.args
    
    def test_get_available_intents(self):
        """Test getting list of available intents"""
        intents = IntentOutcomeMapper.get_available_intents()
        
        assert "ADD_ITEM" in intents
        assert "QUESTION" in intents
        assert "CLEAR_ORDER" in intents
        assert "REMOVE_ITEM" in intents
        assert "MODIFY_ITEM" in intents
        assert "CONFIRM_ORDER" in intents
        assert "REPEAT" in intents
        assert "SMALL_TALK" in intents
        assert "UNKNOWN" in intents
    
    def test_get_available_outcomes(self):
        """Test getting list of available outcomes for an intent"""
        outcomes = IntentOutcomeMapper.get_available_outcomes("ADD_ITEM")
        
        assert "ALL_SUCCESS" in outcomes
        assert "PARTIAL_SUCCESS" in outcomes
        assert "ALL_FAILED" in outcomes
        assert "FATAL_SYSTEM" in outcomes
    
    def test_get_available_outcomes_invalid_intent(self):
        """Test getting outcomes for invalid intent raises ValueError"""
        with pytest.raises(ValueError, match="Unknown intent: INVALID_INTENT"):
            IntentOutcomeMapper.get_available_outcomes("INVALID_INTENT")


class TestRoutingDecision:
    """Test the RoutingDecision dataclass"""
    
    def test_routing_decision_creation(self):
        """Test creating a RoutingDecision"""
        decision = RoutingDecision(
            next_node="canned_response",
            template_purpose="Test purpose",
            template_key="TEST_KEY",
            args={"key": "value"}
        )
        
        assert decision.next_node == "canned_response"
        assert decision.template_purpose == "Test purpose"
        assert decision.template_key == "TEST_KEY"
        assert decision.args == {"key": "value"}
    
    def test_routing_decision_empty_args(self):
        """Test RoutingDecision with empty args"""
        decision = RoutingDecision(
            next_node="follow_up_agent",
            template_purpose="Ask question",
            template_key="ASK_KEY",
            args={}
        )
        
        assert decision.args == {}
