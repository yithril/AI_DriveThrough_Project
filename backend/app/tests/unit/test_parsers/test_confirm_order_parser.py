"""
Unit tests for ConfirmOrderParser
"""

import pytest
from app.agents.parser.confirm_order_parser import ConfirmOrderParser
from app.agents.parser.base_parser import ParserResult
from app.commands.intent_classification_schema import IntentType


class TestConfirmOrderParser:
    """Test ConfirmOrderParser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create ConfirmOrderParser instance for testing"""
        return ConfirmOrderParser()
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser.intent_type == IntentType.CONFIRM_ORDER
    
    def test_parse_confirm_order_basic(self, parser):
        """Test parsing basic confirm order input"""
        user_input = "that's it"
        context = {"order_items": [{"item": "burger"}]}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data is not None
        assert result.command_data["intent"] == "CONFIRM_ORDER"
        assert result.command_data["slots"] == {}
        assert result.command_data["confidence"] == 1.0
        assert result.needs_clarification is False
    
    def test_parse_confirm_order_variations(self, parser):
        """Test parsing various confirm order phrasings"""
        test_cases = [
            "that's it",
            "done",
            "confirm",
            "that's all",
            "finish",
            "complete",
            "ready to order",
            "I'm done",
            "that's everything"
        ]
        
        for user_input in test_cases:
            result = parser.parse(user_input, {})
            
            assert result.success is True
            assert result.command_data["intent"] == "CONFIRM_ORDER"
            assert result.command_data["slots"] == {}
    
    def test_parse_with_empty_context(self, parser):
        """Test parsing with empty context"""
        user_input = "done"
        context = {}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "CONFIRM_ORDER"
    
    def test_parse_with_order_items(self, parser):
        """Test parsing when order has items"""
        user_input = "that's it"
        context = {
            "order_items": [
                {"item": "burger", "quantity": 1},
                {"item": "fries", "quantity": 2}
            ]
        }
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "CONFIRM_ORDER"
        assert result.command_data["slots"] == {}
    
    def test_parse_command_data_structure(self, parser):
        """Test that command data has correct structure for CommandFactory"""
        user_input = "done"
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
        assert command_data["intent"] == "CONFIRM_ORDER"
        assert command_data["confidence"] == 1.0
        assert command_data["slots"] == {}
        assert command_data["needs_clarification"] is False
        assert command_data["clarifying_question"] == ""
        assert "ConfirmOrderParser" in command_data["notes"]
    
    def test_parse_always_succeeds(self, parser):
        """Test that confirm order parsing always succeeds"""
        # Even with weird input, confirm order should succeed
        weird_inputs = [
            "asdfasdf done asdfasdf",
            "!!!CONFIRM!!!",
            "123456",
            ""
        ]
        
        for user_input in weird_inputs:
            result = parser.parse(user_input, {})
            assert result.success is True
            assert result.command_data["intent"] == "CONFIRM_ORDER"
