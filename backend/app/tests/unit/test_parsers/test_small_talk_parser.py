"""
Unit tests for SmallTalkParser
"""

import pytest
from app.agents.parser.small_talk_parser import SmallTalkParser
from app.agents.parser.base_parser import ParserResult
from app.commands.intent_classification_schema import IntentType


class TestSmallTalkParser:
    """Test SmallTalkParser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create SmallTalkParser instance for testing"""
        return SmallTalkParser()
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser.intent_type == IntentType.SMALL_TALK
    
    def test_parse_small_talk_basic(self, parser):
        """Test parsing basic small talk input"""
        user_input = "hello"
        context = {}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "SMALL_TALK"
        assert result.command_data["slots"]["response_type"] == "greeting"
        assert result.command_data["slots"]["user_input"] == "hello"
    
    def test_response_type_detection_greeting(self, parser):
        """Test greeting response type detection"""
        greeting_inputs = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "greetings",
            "howdy"
        ]
        
        for user_input in greeting_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["response_type"] == "greeting"
    
    def test_response_type_detection_thanks(self, parser):
        """Test thanks response type detection"""
        thanks_inputs = [
            "thank you",
            "thanks",
            "appreciate it",
            "grateful",
            "much obliged"
        ]
        
        for user_input in thanks_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["response_type"] == "thanks"
    
    def test_response_type_detection_goodbye(self, parser):
        """Test goodbye response type detection"""
        goodbye_inputs = [
            "goodbye",
            "bye",
            "see you",
            "later",
            "farewell",
            "take care"
        ]
        
        for user_input in goodbye_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["response_type"] == "goodbye"
    
    def test_response_type_detection_compliment(self, parser):
        """Test compliment response type detection"""
        compliment_inputs = [
            "good",
            "great",
            "excellent",
            "wonderful",
            "amazing",
            "fantastic",
            "love it",
            "like it",
            "enjoy",
            "delicious",
            "tasty"
        ]
        
        for user_input in compliment_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["response_type"] == "compliment"
    
    def test_response_type_detection_general(self, parser):
        """Test general response type detection"""
        general_inputs = [
            "okay",
            "sure",
            "alright",
            "fine",
            "whatever"
        ]
        
        for user_input in general_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["response_type"] == "general"
    
    def test_parse_with_context(self, parser):
        """Test parsing with various context"""
        user_input = "hello there"
        context = {
            "conversation_history": [{"user": "hi", "ai": "hello"}],
            "current_state": "ORDERING"
        }
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "SMALL_TALK"
        assert result.command_data["slots"]["response_type"] == "greeting"
    
    def test_parse_command_data_structure(self, parser):
        """Test that command data has correct structure for CommandFactory"""
        user_input = "hello"
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
        assert command_data["intent"] == "SMALL_TALK"
        assert command_data["confidence"] == 1.0
        assert "response_type" in command_data["slots"]
        assert "user_input" in command_data["slots"]
        assert command_data["needs_clarification"] is False
        assert command_data["clarifying_question"] == ""
        assert "SmallTalkParser" in command_data["notes"]
    
    def test_parse_always_succeeds(self, parser):
        """Test that small talk parsing always succeeds"""
        # Even with weird input, small talk should succeed
        weird_inputs = [
            "asdfasdf small talk asdfasdf",
            "!!!SMALL_TALK!!!",
            "123456",
            ""
        ]
        
        for user_input in weird_inputs:
            result = parser.parse(user_input, {})
            assert result.success is True
            assert result.command_data["intent"] == "SMALL_TALK"
    
    def test_user_input_preservation(self, parser):
        """Test that original user input is preserved in slots"""
        test_inputs = [
            "hello there",
            "thank you very much",
            "goodbye for now",
            "that was great"
        ]
        
        for user_input in test_inputs:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["user_input"] == user_input
    
    def test_case_insensitive_detection(self, parser):
        """Test that response type detection is case insensitive"""
        test_cases = [
            ("HELLO", "greeting"),
            ("Thank You", "thanks"),
            ("GOODBYE", "goodbye"),
            ("GREAT", "compliment")
        ]
        
        for user_input, expected_type in test_cases:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["response_type"] == expected_type
