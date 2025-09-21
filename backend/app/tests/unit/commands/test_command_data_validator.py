"""
Unit tests for CommandDataValidator.

Tests validation of command data produced by rule-based parsers.
"""

import pytest
from app.commands.command_data_validator import CommandDataValidator, ValidationError
from app.commands.intent_classification_schema import IntentType


class TestCommandDataValidator:
    """Test CommandDataValidator functionality"""
    
    def test_validator_initialization(self):
        """Test validator can be instantiated"""
        validator = CommandDataValidator()
        assert validator is not None
    
    def test_validate_valid_data(self):
        """Test validation with valid command data"""
        valid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False,
            "clarifying_question": "",
            "notes": "Parsed by ClearOrderParser"
        }
        
        is_valid, errors = CommandDataValidator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0
            # Missing slots and needs_clarification
        }
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 2
        assert any(error.field == "slots" for error in errors)
        assert any(error.field == "needs_clarification" for error in errors)
    
    def test_validate_invalid_intent(self):
        """Test validation with invalid intent"""
        invalid_data = {
            "intent": "INVALID_INTENT",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False
        }
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "intent"
        assert "Invalid intent" in errors[0].message
    
    def test_validate_invalid_confidence(self):
        """Test validation with invalid confidence values"""
        test_cases = [
            ("string", "1.0"),
            ("negative", -0.1),
            ("too_high", 1.1),
            ("not_number", "high")
        ]
        
        for case_name, confidence in test_cases:
            invalid_data = {
                "intent": "CLEAR_ORDER",
                "confidence": confidence,
                "slots": {},
                "needs_clarification": False
            }
            
            is_valid, errors = CommandDataValidator.validate(invalid_data)
            assert is_valid is False, f"Should fail for {case_name}"
            assert len(errors) == 1
            assert errors[0].field == "confidence"
    
    def test_validate_invalid_slots(self):
        """Test validation with invalid slots field"""
        invalid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": "not_a_dict",
            "needs_clarification": False
        }
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "slots"
        assert "must be a dictionary" in errors[0].message
    
    def test_validate_invalid_needs_clarification(self):
        """Test validation with invalid needs_clarification field"""
        invalid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": "yes"
        }
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "needs_clarification"
        assert "must be a boolean" in errors[0].message
    
    def test_validate_unexpected_fields(self):
        """Test validation with unexpected fields"""
        invalid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False,
            "unexpected_field": "should_not_be_here"
        }
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "unexpected_field"
        assert "Unexpected field" in errors[0].message
    
    def test_validate_optional_fields(self):
        """Test validation with optional fields"""
        valid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False,
            "clarifying_question": "What would you like to order?",
            "notes": "Parsed by ClearOrderParser",
            "user_input": "Clear my order"
        }
        
        is_valid, errors = CommandDataValidator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_optional_fields_invalid_types(self):
        """Test validation with invalid optional field types"""
        invalid_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False,
            "clarifying_question": 123,  # Should be string
            "notes": True,  # Should be string
            "user_input": []  # Should be string
        }
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 3
        assert any(error.field == "clarifying_question" for error in errors)
        assert any(error.field == "notes" for error in errors)
        assert any(error.field == "user_input" for error in errors)
    
    def test_validate_for_intent_correct(self):
        """Test validate_for_intent with correct intent"""
        data = {
            "intent": "CLEAR_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False
        }
        
        is_valid, errors = CommandDataValidator.validate_for_intent(data, IntentType.CLEAR_ORDER)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_for_intent_incorrect(self):
        """Test validate_for_intent with incorrect intent"""
        data = {
            "intent": "CONFIRM_ORDER",
            "confidence": 1.0,
            "slots": {},
            "needs_clarification": False
        }
        
        is_valid, errors = CommandDataValidator.validate_for_intent(data, IntentType.CLEAR_ORDER)
        assert is_valid is False
        assert len(errors) == 1
        assert "Expected intent CLEAR_ORDER" in errors[0].message
    
    def test_validate_for_intent_invalid_data(self):
        """Test validate_for_intent with invalid data structure"""
        data = {
            "intent": "CLEAR_ORDER",
            "confidence": "invalid"
        }
        
        is_valid, errors = CommandDataValidator.validate_for_intent(data, IntentType.CLEAR_ORDER)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_get_validation_summary_no_errors(self):
        """Test validation summary with no errors"""
        errors = []
        summary = CommandDataValidator.get_validation_summary(errors)
        assert summary == "Validation passed"
    
    def test_get_validation_summary_with_errors(self):
        """Test validation summary with errors"""
        errors = [
            ValidationError("intent", "Invalid intent", "INVALID"),
            ValidationError("confidence", "Must be between 0.0 and 1.0", 1.5)
        ]
        
        summary = CommandDataValidator.get_validation_summary(errors)
        assert "Validation failed with 2 error(s)" in summary
        assert "intent: Invalid intent (got: INVALID)" in summary
        assert "confidence: Must be between 0.0 and 1.0 (got: 1.5)" in summary
    
    def test_validate_non_dict_input(self):
        """Test validation with non-dictionary input"""
        invalid_data = "not_a_dict"
        
        is_valid, errors = CommandDataValidator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "root"
        assert "must be a dictionary" in errors[0].message
    
    def test_validate_all_intent_types(self):
        """Test validation with all valid intent types"""
        for intent in IntentType:
            data = {
                "intent": intent.value,
                "confidence": 1.0,
                "slots": {},
                "needs_clarification": False
            }
            
            is_valid, errors = CommandDataValidator.validate(data)
            assert is_valid is True, f"Should be valid for intent {intent.value}"
            assert len(errors) == 0
    
    def test_validate_edge_case_confidence(self):
        """Test validation with edge case confidence values"""
        edge_cases = [0.0, 1.0, 0.5, 0.999, 0.001]
        
        for confidence in edge_cases:
            data = {
                "intent": "CLEAR_ORDER",
                "confidence": confidence,
                "slots": {},
                "needs_clarification": False
            }
            
            is_valid, errors = CommandDataValidator.validate(data)
            assert is_valid is True, f"Should be valid for confidence {confidence}"
            assert len(errors) == 0
    
    def test_validate_complex_slots(self):
        """Test validation with complex slots data"""
        complex_slots = {
            "item_name": "Big Mac",
            "quantity": 2,
            "modifications": ["no pickles", "extra cheese"],
            "size": "large"
        }
        
        data = {
            "intent": "ADD_ITEM",
            "confidence": 0.95,
            "slots": complex_slots,
            "needs_clarification": False
        }
        
        is_valid, errors = CommandDataValidator.validate(data)
        assert is_valid is True
        assert len(errors) == 0
