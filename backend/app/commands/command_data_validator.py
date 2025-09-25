"""
Command data validator for rule-based parser output.

Validates the structured command data produced by rule-based parsers
before it's passed to the CommandFactory.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from app.commands.command_type_schema import CommandType


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    value: Any = None


class CommandDataValidator:
    """
    Validates command data produced by rule-based parsers.
    
    Ensures the data structure is correct before passing to CommandFactory.
    """
    
    REQUIRED_FIELDS = ["intent", "confidence", "slots"]
    OPTIONAL_FIELDS = ["notes", "user_input"]
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> tuple[bool, List[ValidationError]]:
        """
        Validate command data structure.
        
        Args:
            data: Command data dictionary from parser
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if data is a dictionary
        if not isinstance(data, dict):
            errors.append(ValidationError(
                field="root",
                message="Command data must be a dictionary",
                value=type(data).__name__
            ))
            return False, errors
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in data:
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing"
                ))
        
        # Validate intent field
        if "intent" in data:
            if not isinstance(data["intent"], str):
                errors.append(ValidationError(
                    field="intent",
                    message="Intent must be a string",
                    value=type(data["intent"]).__name__
                ))
            elif data["intent"] not in [command.value for command in CommandType]:
                errors.append(ValidationError(
                    field="intent",
                    message=f"Invalid intent: {data['intent']}",
                    value=data["intent"]
                ))
        
        # Validate confidence field
        if "confidence" in data:
            if not isinstance(data["confidence"], (int, float)):
                errors.append(ValidationError(
                    field="confidence",
                    message="Confidence must be a number",
                    value=type(data["confidence"]).__name__
                ))
            elif not (0.0 <= data["confidence"] <= 1.0):
                errors.append(ValidationError(
                    field="confidence",
                    message="Confidence must be between 0.0 and 1.0",
                    value=data["confidence"]
                ))
        
        # Validate slots field
        if "slots" in data:
            if not isinstance(data["slots"], dict):
                errors.append(ValidationError(
                    field="slots",
                    message="Slots must be a dictionary",
                    value=type(data["slots"]).__name__
                ))
        
        
        # Validate optional fields if present
        for field in cls.OPTIONAL_FIELDS:
            if field in data:
                if field in ["notes", "user_input"]:
                    if not isinstance(data[field], str):
                        errors.append(ValidationError(
                            field=field,
                            message=f"{field} must be a string",
                            value=type(data[field]).__name__
                        ))
        
        # Check for unexpected fields
        all_valid_fields = cls.REQUIRED_FIELDS + cls.OPTIONAL_FIELDS
        for field in data.keys():
            if field not in all_valid_fields:
                errors.append(ValidationError(
                    field=field,
                    message=f"Unexpected field: {field}",
                    value=data[field]
                ))
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_for_intent(cls, data: Dict[str, Any], expected_intent: CommandType) -> tuple[bool, List[ValidationError]]:
        """
        Validate command data for a specific intent.
        
        Args:
            data: Command data dictionary
            expected_intent: The intent this data should have
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        is_valid, errors = cls.validate(data)
        
        if not is_valid:
            return False, errors
        
        # Check intent matches expected
        if data.get("intent") != expected_intent.value:
            errors.append(ValidationError(
                field="intent",
                message=f"Expected intent {expected_intent.value}, got {data.get('intent')}",
                value=data.get("intent")
            ))
            return False, errors
        
        return True, errors
    
    @classmethod
    def get_validation_summary(cls, errors: List[ValidationError]) -> str:
        """
        Get a human-readable summary of validation errors.
        
        Args:
            errors: List of validation errors
            
        Returns:
            Formatted error summary
        """
        if not errors:
            return "Validation passed"
        
        summary = f"Validation failed with {len(errors)} error(s):\n"
        for error in errors:
            summary += f"  - {error.field}: {error.message}"
            if error.value is not None:
                summary += f" (got: {error.value})"
            summary += "\n"
        
        return summary.strip()
