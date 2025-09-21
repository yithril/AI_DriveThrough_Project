"""
Unit tests for QuestionParser
"""

import pytest
from app.agents.parser.question_parser import QuestionParser
from app.agents.parser.base_parser import ParserResult
from app.commands.intent_classification_schema import IntentType


class TestQuestionParser:
    """Test QuestionParser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create QuestionParser instance for testing"""
        return QuestionParser()
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser.intent_type == IntentType.QUESTION
    
    def test_parse_question_basic(self, parser):
        """Test parsing basic question input"""
        user_input = "what's on the menu?"
        context = {}
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "QUESTION"
        assert result.command_data["slots"]["question"] == "what's on the menu?"
        assert result.command_data["slots"]["category"] == "menu"
    
    def test_question_category_detection_pricing(self, parser):
        """Test pricing question category detection"""
        pricing_questions = [
            "how much does it cost?",
            "what's the price?",
            "how expensive is it?",
            "total cost",
            "dollar amount"
        ]
        
        for user_input in pricing_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["category"] == "pricing"
    
    def test_question_category_detection_menu(self, parser):
        """Test menu question category detection"""
        menu_questions = [
            "what's on the menu?",
            "do you have burgers?",
            "what food do you serve?",
            "available items",
            "menu options"
        ]
        
        for user_input in menu_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["category"] == "menu"
    
    def test_question_category_detection_hours(self, parser):
        """Test hours question category detection"""
        hours_questions = [
            "what are your hours?",
            "when are you open?",
            "are you open today?",
            "what time do you close?",
            "monday hours"
        ]
        
        for user_input in hours_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["category"] == "hours"
    
    def test_question_category_detection_location(self, parser):
        """Test location question category detection"""
        location_questions = [
            "where are you located?",
            "what's your address?",
            "how do I find you?",
            "directions to restaurant",
            "nearby location"
        ]
        
        for user_input in location_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["category"] == "location"
    
    def test_question_category_detection_ingredients(self, parser):
        """Test ingredients question category detection"""
        ingredients_questions = [
            "what ingredients are in the burger?",
            "does it contain gluten?",
            "is it vegetarian?",
            "allergen information",
            "what's it made with?"
        ]
        
        for user_input in ingredients_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["category"] == "ingredients"
    
    def test_question_category_detection_general(self, parser):
        """Test general question category detection"""
        general_questions = [
            "how are you?",
            "what's up?",
            "random question",
            "unclear input"
        ]
        
        for user_input in general_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["category"] == "general"
    
    def test_parse_with_context(self, parser):
        """Test parsing with various context"""
        user_input = "what's the price?"
        context = {
            "restaurant_id": 1,
            "current_state": "ORDERING"
        }
        
        result = parser.parse(user_input, context)
        
        assert result.success is True
        assert result.command_data["intent"] == "QUESTION"
        assert result.command_data["slots"]["category"] == "pricing"
    
    def test_parse_command_data_structure(self, parser):
        """Test that command data has correct structure for CommandFactory"""
        user_input = "what's on the menu?"
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
        assert command_data["intent"] == "QUESTION"
        assert command_data["confidence"] == 1.0
        assert "question" in command_data["slots"]
        assert "category" in command_data["slots"]
        assert command_data["needs_clarification"] is False
        assert command_data["clarifying_question"] == ""
        assert "QuestionParser" in command_data["notes"]
    
    def test_parse_always_succeeds(self, parser):
        """Test that question parsing always succeeds"""
        # Even with weird input, question should succeed
        weird_inputs = [
            "asdfasdf question asdfasdf",
            "!!!QUESTION!!!",
            "123456",
            ""
        ]
        
        for user_input in weird_inputs:
            result = parser.parse(user_input, {})
            assert result.success is True
            assert result.command_data["intent"] == "QUESTION"
    
    def test_question_preservation(self, parser):
        """Test that original question is preserved in slots"""
        test_questions = [
            "what's on the menu?",
            "how much does it cost?",
            "where are you located?",
            "what are your hours?"
        ]
        
        for user_input in test_questions:
            result = parser.parse(user_input, {})
            assert result.command_data["slots"]["question"] == user_input
