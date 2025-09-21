"""
Unit tests for RepeatParser
"""

import pytest
from app.agents.parser.repeat_parser import RepeatParser
from app.agents.parser.base_parser import ParserResult
from app.commands.intent_classification_schema import IntentType


class TestRepeatParser:
    """Test RepeatParser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create RepeatParser instance for testing"""
        return RepeatParser()
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser.intent_type == IntentType.REPEAT
    
    def test_parse_repeat_full_order(self, parser):
        """Test parsing repeat full order input"""
        user_input = "repeat my order"
        context = {"order_items": [{"item": "burger"}]}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "REPEAT"
        assert result.command_data["slots"]["scope"] == "full_order"
        assert result.command_data["slots"]["target_ref"] == "last_item"
    
    def test_parse_repeat_last_item(self, parser):
        """Test parsing repeat last item input"""
        user_input = "repeat that"
        context = {"order_items": [{"item": "burger"}]}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "REPEAT"
        assert result.command_data["slots"]["scope"] == "last_item"
        assert result.command_data["slots"]["target_ref"] == "last_item"
    
    def test_scope_detection_full_order(self, parser):
        """Test scope detection for full order keywords"""
        full_order_cases = [
            "repeat my order",
            "repeat everything",
            "repeat all",
            "what did i order",
            "repeat my order please"
        ]
        
        for user_input in full_order_cases:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["scope"] == "full_order"
    
    def test_scope_detection_last_item(self, parser):
        """Test scope detection for last item keywords"""
        last_item_cases = [
            "repeat that",
            "repeat last",
            "repeat previous",
            "what was that",
            "what did i just say"
        ]
        
        for user_input in last_item_cases:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["scope"] == "last_item"
    
    def test_scope_detection_default(self, parser):
        """Test scope detection defaults to full_order when unclear"""
        unclear_cases = [
            "repeat",
            "what",
            "huh",
            "say again"
        ]
        
        for user_input in unclear_cases:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["scope"] == "full_order"
    
    def test_target_reference_detection(self, parser):
        """Test target reference detection"""
        # Test line number detection
        result = parser.parse("repeat line 2", {})
        assert result.command_data["slots"]["target_ref"] == "line_2"
        
        # Test last item detection
        result = parser.parse("repeat that", {})
        assert result.command_data["slots"]["target_ref"] == "last_item"
        
        # Test default
        result = parser.parse("repeat", {})
        assert result.command_data["slots"]["target_ref"] == "last_item"
    
    def test_parse_with_context(self, parser):
        """Test parsing with various context"""
        user_input = "repeat my order"
        context = {
            "order_items": [
                {"item": "burger", "quantity": 1},
                {"item": "fries", "quantity": 2}
            ],
            "current_state": "ORDERING"
        }
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "REPEAT"
        assert result.command_data["slots"]["scope"] == "full_order"
    
    def test_parse_command_data_structure(self, parser):
        """Test that command data has correct structure for CommandFactory"""
        user_input = "repeat my order"
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
        assert command_data["intent"] == "REPEAT"
        assert command_data["confidence"] == 1.0
        assert "scope" in command_data["slots"]
        assert "target_ref" in command_data["slots"]
        assert command_data["needs_clarification"] is False
        assert command_data["clarifying_question"] == ""
        assert "RepeatParser" in command_data["notes"]
    
    def test_parse_always_succeeds(self, parser):
        """Test that repeat parsing always succeeds"""
        # Even with weird input, repeat should succeed
        weird_inputs = [
            "asdfasdf repeat asdfasdf",
            "!!!REPEAT!!!",
            "123456",
            ""
        ]
        
        for user_input in weird_inputs:
            result = parser.parse(user_input, {})
            assert result.success is True
            assert result.command_data["intent"] == "REPEAT"
    
    def test_line_number_regex(self, parser):
        """Test line number regex matching"""
        test_cases = [
            ("repeat line 1", "line_1"),
            ("repeat line 2", "line_2"),
            ("repeat line 10", "line_10"),
            ("repeat line 1 please", "line_1"),
            ("what's on line 3", "line_3")
        ]
        
        for user_input, expected_ref in test_cases:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["target_ref"] == expected_ref
