"""
Unit tests for UnknownParser
"""

import pytest
from app.agents.parser.unknown_parser import UnknownParser
from app.agents.parser.base_parser import ParserResult
from app.commands.intent_classification_schema import IntentType


class TestUnknownParser:
    """Test UnknownParser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create UnknownParser instance for testing"""
        return UnknownParser()
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser.intent_type == IntentType.UNKNOWN
    
    def test_parse_unknown_basic(self, parser):
        """Test parsing basic unknown input"""
        user_input = "asdfasdf"
        context = {}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "UNKNOWN"
        assert result.command_data["slots"]["user_input"] == "asdfasdf"
        assert "clarifying_question" in result.command_data["slots"]
    
    def test_clarifying_question_no_order(self, parser):
        """Test clarifying question when user has no order"""
        user_input = "unclear input"
        context = {
            "order_items": [],
            "current_state": "IDLE"
        }
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert "What would you like to order today?" in result.command_data["slots"]["clarifying_question"]
    
    def test_clarifying_question_has_order(self, parser):
        """Test clarifying question when user has order"""
        user_input = "unclear input"
        context = {
            "order_items": [{"item": "burger"}],
            "current_state": "ORDERING"
        }
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert "add something to your order" in result.command_data["slots"]["clarifying_question"]
    
    def test_clarifying_question_default(self, parser):
        """Test default clarifying question"""
        user_input = "unclear input"
        context = {}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert "I'm sorry, I didn't understand" in result.command_data["slots"]["clarifying_question"]
    
    def test_parse_with_various_contexts(self, parser):
        """Test parsing with various context scenarios"""
        test_cases = [
            # No order, IDLE state
            {
                "context": {"order_items": [], "current_state": "IDLE"},
                "expected_question": "What would you like to order today?"
            },
            # Has order, ORDERING state
            {
                "context": {"order_items": [{"item": "burger"}], "current_state": "ORDERING"},
                "expected_question": "add something to your order"
            },
            # Empty context
            {
                "context": {},
                "expected_question": "I'm sorry, I didn't understand"
            }
        ]
        
        for test_case in test_cases:
            result = parser.parse("unclear input", test_case["context"])
            assert result.success is True
            assert test_case["expected_question"] in result.command_data["slots"]["clarifying_question"]
    
    def test_parse_command_data_structure(self, parser):
        """Test that command data has correct structure for CommandFactory"""
        user_input = "unclear input"
        context = {}
        
        result = parser.parse(user_input, context)
        command_data = result.command_data
        
        # Check required fields for CommandFactory
        assert "intent" in command_data
        assert "confidence" in command_data
        assert "slots" in command_data
        assert "needs_clarification" in command_data
        assert "clarifying_question" in command_data
        assert "notes" in command_data
        
        # Check values
        assert command_data["intent"] == "UNKNOWN"
        assert command_data["confidence"] == 1.0
        assert "user_input" in command_data["slots"]
        assert "clarifying_question" in command_data["slots"]
        assert command_data["needs_clarification"] is False
        assert command_data["clarifying_question"] == ""
        assert "UnknownParser" in command_data["notes"]
    
    def test_parse_always_succeeds(self, parser):
        """Test that unknown parsing always succeeds"""
        # Even with weird input, unknown should succeed
        weird_inputs = [
            "asdfasdf",
            "!!!UNKNOWN!!!",
            "123456",
            "",
            "random gibberish"
        ]
        
        for user_input in weird_inputs:
            result = parser.parse(user_input, {})
            assert result.success is True
            assert result.command_data["intent"] == "UNKNOWN"
    
    def test_user_input_preservation(self, parser):
        """Test that original user input is preserved in slots"""
        test_inputs = [
            "asdfasdf",
            "unclear input",
            "random text",
            "gibberish"
        ]
        
        for user_input in test_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["user_input"] == user_input
    
    def test_clarifying_question_generation(self, parser):
        """Test clarifying question generation logic"""
        # Test the _generate_clarifying_question method directly
        test_cases = [
            # No order, IDLE state
            {
                "context": {"order_items": [], "current_state": "IDLE"},
                "expected": "What would you like to order today?"
            },
            # Has order, ORDERING state  
            {
                "context": {"order_items": [{"item": "burger"}], "current_state": "ORDERING"},
                "expected": "add something to your order"
            },
            # Empty context
            {
                "context": {},
                "expected": "I'm sorry, I didn't understand"
            }
        ]
        
        for test_case in test_cases:
            question = parser._generate_clarifying_question(test_case["context"])
            assert test_case["expected"] in question
