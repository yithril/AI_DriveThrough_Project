"""
Unit tests for CommandFactory functionality
"""

import pytest
from app.commands.command_factory import CommandFactory
from app.commands.intent_classification_schema import IntentType
from app.tests.helpers.test_data_factory import TestDataFactory


class TestCommandFactory:
    """Test CommandFactory functionality"""
    
    def test_factory_initialization(self):
        """Test that CommandFactory can be instantiated"""
        factory = CommandFactory()
        assert factory is not None
    
    def test_get_supported_intents(self):
        """Test getting list of supported intents"""
        intents = CommandFactory.get_supported_intents()
        
        expected_intents = [
            "ADD_ITEM", "REMOVE_ITEM", "CLEAR_ORDER", "CONFIRM_ORDER",
            "QUESTION", "UNKNOWN"
        ]
        
        for intent in expected_intents:
            assert intent in intents
    
    def test_validate_intent_data_basic(self):
        """Test basic intent data validation"""
        valid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 0.95,
            "slots": {},
            "needs_clarification": False
        }
        
        validated = CommandFactory.validate_intent_data(valid_data)
        
        assert validated["intent"] == "CLEAR_ORDER"
        assert validated["confidence"] == 0.95
        assert validated["slots"] == {}
        assert validated["needs_clarification"] is False
    
    def test_validate_intent_data_normalization(self):
        """Test intent data normalization"""
        raw_data = {
            "intent": "clear_order",  # lowercase
            "confidence": "0.8",  # string
            "slots": None,  # None instead of dict
            "needs_clarification": "true"  # string instead of bool
        }
        
        validated = CommandFactory.validate_intent_data(raw_data)
        
        assert validated["intent"] == "CLEAR_ORDER"  # Should be uppercase
        assert validated["confidence"] == 0.8  # Should be float
        assert validated["slots"] is None  # None is preserved, not converted to {}
        assert validated["needs_clarification"] is True  # Should be bool
    
    def test_validate_intent_data_confidence_bounds(self):
        """Test confidence value bounds"""
        # Test confidence > 1.0
        data_high = {"intent": "CLEAR_ORDER", "confidence": 1.5}
        validated = CommandFactory.validate_intent_data(data_high)
        assert validated["confidence"] == 1.0
        
        # Test confidence < 0.0
        data_low = {"intent": "CLEAR_ORDER", "confidence": -0.5}
        validated = CommandFactory.validate_intent_data(data_low)
        assert validated["confidence"] == 0.0
    
    def test_validate_intent_data_unknown_intent(self):
        """Test handling of unknown intent"""
        data = {"intent": "UNKNOWN_INTENT", "confidence": 0.8}
        validated = CommandFactory.validate_intent_data(data)
        assert validated["intent"] == "UNKNOWN"
    
    def test_create_command_add_item(self):
        """Test creating AddItemCommand"""
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 1.0,
            "slots": {
                "item_id": 123,
                "quantity": 2,
                "size": "large",
                "modifiers": ["no_pickles", "extra_cheese"],
                "special_instructions": "Well done"
            },
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "AddItemCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
        assert command.menu_item_id == 123
        assert command.quantity == 2
        assert command.size == "large"
        assert command.modifiers == ["no_pickles", "extra_cheese"]
        assert command.special_instructions == "Well done"
    
    def test_create_command_remove_item(self):
        """Test creating RemoveItemCommand"""
        intent_data = {
            "intent": "REMOVE_ITEM",
            "confidence": 1.0,
            "slots": {
                "order_item_id": 456,
                "target_ref": "last_item"
            },
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "RemoveItemCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
        assert command.order_item_id == 456
        assert command.target_ref == "last_item"
    
    def test_create_command_clear_order(self):
        """Test creating ClearOrderCommand"""
        intent_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "ClearOrderCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
    
    def test_create_command_confirm_order(self):
        """Test creating ConfirmOrderCommand"""
        intent_data = {
            "intent": "CONFIRM_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "ConfirmOrderCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
    
    
    def test_create_command_question(self):
        """Test creating QuestionCommand"""
        intent_data = {
            "intent": "QUESTION",
            "confidence": 1.0,
            "slots": {
                "question": "What do you have?",
                "category": "menu"
            },
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "QuestionCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
        assert command.question == "What do you have?"
        assert command.category == "menu"
    
    
    def test_create_command_unknown(self):
        """Test creating UnknownCommand"""
        intent_data = {
            "intent": "UNKNOWN",
            "confidence": 1.0,
            "slots": {
                "user_input": "I don't understand",
                "clarifying_question": "Could you please repeat that?"
            },
            "needs_clarification": True
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "UnknownCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
        assert command.user_input == "I don't understand"
        assert command.clarifying_question == "Could you please repeat that?"
    
    def test_create_command_unsupported_intent(self):
        """Test creating command for unsupported intent"""
        intent_data = {
            "intent": "MODIFY_ITEM",  # Not in INTENT_TO_COMMAND
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        assert command is None
    
    def test_create_command_missing_required_fields(self):
        """Test creating command with missing required fields"""
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 1.0,
            "slots": {},  # Missing required item_id
            "needs_clarification": False
        }
        
        # Should still create command but with None values
        command = CommandFactory.create_command(intent_data, 1, 100)
        assert command is not None
        assert command.menu_item_id is None
    
    def test_create_command_with_defaults(self):
        """Test creating commands with default values"""
        intent_data = {
            "intent": "QUESTION",
            "confidence": 1.0,
            "slots": {},  # No question provided
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.question == "How can I help you?"  # Default value
    
    def test_create_command_exception_handling(self):
        """Test that exceptions during command creation are handled"""
        # Create invalid data that would cause an exception
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 1.0,
            "slots": {
                "item_id": "invalid_id",  # Should be int, not string
                "quantity": "invalid_quantity"  # Should be int, not string
            },
            "needs_clarification": False
        }
        
        # Command factory doesn't validate types, it just passes them through
        # So this should create a command with string values
        command = CommandFactory.create_command(intent_data, 1, 100)
        assert command is not None
        assert command.menu_item_id == "invalid_id"  # String value is preserved
        assert command.quantity == "invalid_quantity"  # String value is preserved
    
    def test_create_command_with_parser_output(self):
        """Test creating commands from parser output format"""
        # This simulates the output from our rule-based parsers
        parser_output = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False,
            "clarifying_question": "",
            "notes": "Parsed by ClearOrderParser"
        }
        
        command = CommandFactory.create_command(parser_output, 1, 100)
        
        assert command is not None
        assert command.__class__.__name__ == "ClearOrderCommand"
        assert command.restaurant_id == 1
        assert command.order_id == 100
    
    def test_create_command_with_complex_slots(self):
        """Test creating commands with complex slot data"""
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 0.95,
            "slots": {
                "item_id": 999,
                "quantity": 3,
                "size": "medium",
                "modifiers": ["no_onions", "extra_pickles", "hold_mayo"],
                "special_instructions": "Cook medium rare, no salt",
                "combo": True,
                "drink_id": 456,
                "sides": [789, 101]
            },
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        
        assert command is not None
        assert command.menu_item_id == 999
        assert command.quantity == 3
        assert command.size == "medium"
        assert len(command.modifiers) == 3
        assert "no_onions" in command.modifiers
        assert command.special_instructions == "Cook medium rare, no salt"
    
    def test_create_command_edge_cases(self):
        """Test creating commands with edge case values"""
        # Test with zero quantity
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 1.0,
            "slots": {"item_id": 123, "quantity": 0},
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        assert command is not None
        assert command.quantity == 0
        
        # Test with empty modifiers list
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 1.0,
            "slots": {"item_id": 123, "modifiers": []},
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        assert command is not None
        assert command.modifiers == []
        
        # Test with None values
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 1.0,
            "slots": {
                "item_id": 123,
                "size": None,
                "modifiers": None,
                "special_instructions": None
            },
            "needs_clarification": False
        }
        
        command = CommandFactory.create_command(intent_data, 1, 100)
        assert command is not None
        assert command.size is None
        assert command.modifiers == []
        assert command.special_instructions is None
    
    def test_create_command_all_intent_types(self):
        """Test creating commands for all supported intent types"""
        intent_types = [
            "ADD_ITEM", "REMOVE_ITEM", "CLEAR_ORDER", "CONFIRM_ORDER",
            "QUESTION", "UNKNOWN"
        ]
        
        for intent_type in intent_types:
            # Provide appropriate slots for each intent type
            slots = {}
            if intent_type == "ADD_ITEM":
                slots = {"item_id": 123}
            elif intent_type == "REMOVE_ITEM":
                slots = {"target_ref": "last_item"}
            elif intent_type in ["QUESTION", "UNKNOWN"]:
                slots = {}  # These can work with empty slots
            
            intent_data = {
                "intent": intent_type,
                "confidence": 1.0,
                "slots": slots,
                "needs_clarification": False
            }
            
            command = CommandFactory.create_command(intent_data, 1, 100)
            assert command is not None, f"Failed to create command for {intent_type}"
            assert command.restaurant_id == 1
            assert command.order_id == 100
