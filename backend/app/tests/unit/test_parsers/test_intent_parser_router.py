"""
Unit tests for IntentParserRouter
"""

import pytest
from app.agents.nodes.intent_parser_router_node import IntentParserRouter
from app.agents.parser.base_parser import ParserResult
from app.commands.intent_classification_schema import IntentType


class TestIntentParserRouter:
    """Test IntentParserRouter functionality"""
    
    @pytest.fixture
    def router(self):
        """Create IntentParserRouter instance for testing"""
        return IntentParserRouter()
    
    def test_router_initialization(self, router):
        """Test router initializes correctly with all parsers"""
        assert len(router.parsers) == 6  # All 6 rule-based parsers
        assert IntentType.CLEAR_ORDER in router.parsers
        assert IntentType.CONFIRM_ORDER in router.parsers
        assert IntentType.QUESTION in router.parsers
        assert IntentType.UNKNOWN in router.parsers
    
    def test_parse_intent_clear_order(self, router):
        """Test routing CLEAR_ORDER intent"""
        result = router.parse_intent(
            intent_type=IntentType.CLEAR_ORDER,
            user_input="clear my order",
            context={}
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "CLEAR_ORDER"
        assert result.command_data["slots"] == {}
    
    def test_parse_intent_confirm_order(self, router):
        """Test routing CONFIRM_ORDER intent"""
        result = router.parse_intent(
            intent_type=IntentType.CONFIRM_ORDER,
            user_input="that's it",
            context={}
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "CONFIRM_ORDER"
        assert result.command_data["slots"] == {}
    
    
    def test_parse_intent_question(self, router):
        """Test routing QUESTION intent"""
        result = router.parse_intent(
            intent_type=IntentType.QUESTION,
            user_input="what's on the menu?",
            context={}
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "QUESTION"
        assert "question" in result.command_data["slots"]
        assert "category" in result.command_data["slots"]
    
    
    def test_parse_intent_unknown(self, router):
        """Test routing UNKNOWN intent"""
        result = router.parse_intent(
            intent_type=IntentType.UNKNOWN,
            user_input="asdfasdf",
            context={}
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "UNKNOWN"
        assert "user_input" in result.command_data["slots"]
        assert "clarifying_question" in result.command_data["slots"]
    
    def test_parse_intent_with_context(self, router):
        """Test parsing with various context"""
        context = {
            "order_items": [{"item": "burger"}],
            "current_state": "ORDERING",
            "conversation_history": [{"user": "hi", "ai": "hello"}]
        }
        
        result = router.parse_intent(
            intent_type=IntentType.QUESTION,
            user_input="what's on the menu?",
            context=context
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "QUESTION"
    
    def test_parse_intent_unsupported_intent(self, router):
        """Test parsing unsupported intent falls back to UNKNOWN"""
        # This should not happen in practice, but test the fallback
        result = router.parse_intent(
            intent_type="UNSUPPORTED_INTENT",  # This will be treated as unknown
            user_input="some input",
            context={}
        )
        
        # Should fall back to unknown parser
        assert result.success is True
        assert result.command_data["intent"] == "UNKNOWN"
    
    def test_parse_intent_parser_exception(self, router):
        """Test that parser exceptions are handled gracefully"""
        # Mock a parser that raises an exception
        class FailingParser:
            def parse(self, user_input, context):
                raise Exception("Parser failed")
        
        # Replace a parser with a failing one
        original_parser = router.parsers[IntentType.CLEAR_ORDER]
        router.parsers[IntentType.CLEAR_ORDER] = FailingParser()
        
        try:
            result = router.parse_intent(
                intent_type=IntentType.CLEAR_ORDER,
                user_input="clear order",
                context={}
            )
            
            # Should fall back to unknown parser
            assert result.success is True
            assert result.command_data["intent"] == "UNKNOWN"
        finally:
            # Restore original parser
            router.parsers[IntentType.CLEAR_ORDER] = original_parser
    
    def test_get_supported_intents(self, router):
        """Test getting supported intent types"""
        supported_intents = router.get_supported_intents()
        
        assert len(supported_intents) == 6
        assert IntentType.CLEAR_ORDER in supported_intents
        assert IntentType.CONFIRM_ORDER in supported_intents
        assert IntentType.QUESTION in supported_intents
        assert IntentType.UNKNOWN in supported_intents
    
    def test_router_consistency(self, router):
        """Test that router consistently routes same intent to same parser"""
        # Test multiple calls with same intent
        for _ in range(3):
            result1 = router.parse_intent(
                intent_type=IntentType.QUESTION,
                user_input="what's the price?",
                context={}
            )
            
            result2 = router.parse_intent(
                intent_type=IntentType.QUESTION,
                user_input="how much does it cost?",
                context={}
            )
            
            assert result1.success is True
            assert result2.success is True
            assert result1.command_data["intent"] == "QUESTION"
            assert result2.command_data["intent"] == "QUESTION"
    
    def test_router_with_empty_context(self, router):
        """Test router with empty context"""
        result = router.parse_intent(
            intent_type=IntentType.CLEAR_ORDER,
            user_input="clear order",
            context={}
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "CLEAR_ORDER"
    
    def test_router_with_complex_context(self, router):
        """Test router with complex context"""
        complex_context = {
            "order_items": [
                {"item": "burger", "quantity": 1},
                {"item": "fries", "quantity": 2}
            ],
            "current_state": "ORDERING",
            "conversation_history": [
                {"user": "hi", "ai": "hello"},
                {"user": "I want a burger", "ai": "okay"}
            ],
            "last_mentioned_item": "burger",
            "restaurant_id": 1,
            "session_id": "test-session"
        }
        
        result = router.parse_intent(
            intent_type=IntentType.CLEAR_ORDER,
            user_input="clear my order",
            context=complex_context
        )
        
        assert result.success is True
        assert result.command_data["intent"] == "CLEAR_ORDER"
