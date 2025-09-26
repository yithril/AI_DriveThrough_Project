# Command System Guide

This guide explains how to create new commands and integrate them into the AI DriveThru system.

## Overview

The command system follows the Command Pattern and consists of:

1. **Commands** - Individual command implementations
2. **CommandFactory** - Creates command objects from intent data
3. **CommandInvoker** - Executes commands with proper context
4. **CommandDataValidator** - Validates command data structure

## Creating a New Command

### Step 1: Create the Command Class

Create a new command file in `app/commands/` following the naming pattern `{command_name}_command.py`:

```python
"""
Example: app/commands/example_command.py
"""

from typing import Optional, Dict, Any
from ..commands.base_command import BaseCommand
from ..dto.order_result import OrderResult
from ..constants.audio_phrases import AudioPhraseType
import logging

class ExampleCommand(BaseCommand):
    """
    Example command for demonstration
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        example_param: str,
        optional_param: Optional[str] = None
    ):
        """
        Initialize example command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID
            example_param: Required parameter
            optional_param: Optional parameter
        """
        super().__init__(restaurant_id, order_id)
        self.example_param = example_param
        self.optional_param = optional_param
        self.confidence = 1.0  # Set confidence level
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the example command
        
        Args:
            context: Command execution context
            db: Database session
            
        Returns:
            OrderResult: Success or error result
        """
        try:
            # Your command logic here
            self.logger.info(f"Executing example command with param: {self.example_param}")
            
            # Example business logic
            result_data = {
                "example_result": f"Processed {self.example_param}",
                "response_type": "example_success"
            }
            
            # Return success result
            return OrderResult.success(
                message=f"Example command completed: {self.example_param}",
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Example command execution failed: {e}")
            return OrderResult.error(f"Example command failed: {str(e)}")
    
    def _get_parameters(self) -> Dict[str, Any]:
        """
        Get command parameters for logging/debugging
        
        Returns:
            Dictionary of command parameters
        """
        return {
            "example_param": self.example_param,
            "optional_param": self.optional_param
        }
```

### Step 2: Add Command to CommandType Enum

Update `app/commands/command_type_schema.py`:

```python
from enum import Enum

class CommandType(Enum):
    # ... existing commands ...
    EXAMPLE = "EXAMPLE"
```

### Step 3: Add Command to CommandFactory

Update `app/commands/command_factory.py`:

```python
# Add to INTENT_TO_COMMAND mapping
INTENT_TO_COMMAND = {
    # ... existing mappings ...
    "EXAMPLE": ExampleCommand,
}

# Add creation method
@classmethod
def _create_example_command(cls, command_class, slots: Dict[str, Any], restaurant_id: int, order_id: int):
    """Create ExampleCommand from slots"""
    return command_class(
        restaurant_id=restaurant_id,
        order_id=order_id,
        example_param=slots.get("example_param", ""),
        optional_param=slots.get("optional_param")
    )

# Add to create_command method
elif intent == "EXAMPLE":
    return cls._create_example_command(command_class, slots, restaurant_id, order_id)
```

### Step 4: Update CommandDataValidator

Update `app/commands/command_data_validator.py`:

```python
# Add to REQUIRED_FIELDS if needed
REQUIRED_FIELDS = [
    "intent",
    "confidence", 
    "slots",
    "needs_clarification"
]

# Add validation logic if needed
def _validate_example_command(self, data: Dict[str, Any]) -> List[ValidationError]:
    """Validate example command specific data"""
    errors = []
    
    slots = data.get("slots", {})
    if "example_param" not in slots:
        errors.append(ValidationError(
            field="example_param",
            message="Example command requires example_param in slots"
        ))
    
    return errors
```

## Command Execution Flow

### 1. Intent Classification
```
User Input → Intent Classifier → IntentType (e.g., "ADD_ITEM")
```

### 2. Intent Parsing
```
IntentType → Parser → Command Data Dictionary
```

### 3. Command Creation
```
Command Data → CommandFactory → Command Object
```

### 4. Command Execution
```
Command Object → CommandInvoker → OrderResult
```

## CommandInvoker Details

The `CommandInvoker` handles:

### Single Command Execution
```python
command = CommandFactory.create_command(intent_data, restaurant_id, order_id)
result = await command_invoker.execute_command(command, context)
```

### Batch Command Execution
```python
commands = [command1, command2, command3]
batch_result = await command_invoker.execute_multiple_commands(commands, context)
```

### Command Context
The `CommandContext` provides:
- Database session
- Order service
- Order session service
- Customization validator
- Restaurant ID
- Order ID

## Testing Commands

### Unit Tests
Create tests in `app/tests/unit/commands/test_{command_name}_command.py`:

```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.commands.example_command import ExampleCommand
from app.commands.command_context import CommandContext
from app.dto.order_result import OrderResult

class TestExampleCommand:
    
    @pytest.fixture
    def command_context(self):
        context = CommandContext(session_id="test", restaurant_id=1, order_id=123)
        context.set_db_session(AsyncMock())
        return context
    
    @pytest.fixture
    def example_command(self):
        return ExampleCommand(
            restaurant_id=1,
            order_id=123,
            example_param="test_value"
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self, example_command, command_context):
        result = await example_command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "test_value" in result.message
        assert result.data["response_type"] == "example_success"
    
    @pytest.mark.asyncio
    async def test_execute_failure(self, example_command, command_context):
        # Test error scenarios
        pass
```

### Integration Tests
Test through the full pipeline:

```python
@pytest.mark.asyncio
async def test_example_command_pipeline(self, command_invoker, command_context):
    """Test EXAMPLE command through factory -> invoker pipeline"""
    intent_data = {
        "intent": "EXAMPLE",
        "confidence": 0.9,
        "slots": {
            "example_param": "test_value",
            "optional_param": "optional_value"
        },
        "needs_clarification": False
    }
    
    # Create command through factory
    command = CommandFactory.create_command(intent_data, 1, 123)
    assert command is not None
    assert command.__class__.__name__ == "ExampleCommand"
    
    # Execute through invoker
    result = await command_invoker.execute_command(command, command_context)
    
    # Should succeed
    assert result.is_success
    assert "test_value" in result.message
```

## Command Data Structure

Commands expect this data structure:

```python
{
    "intent": "COMMAND_NAME",
    "confidence": 0.9,
    "slots": {
        "param1": "value1",
        "param2": "value2"
    },
    "needs_clarification": False
}
```

## Best Practices

### 1. Command Design
- **Single Responsibility** - Each command should do one thing
- **Idempotent** - Commands should be safe to retry
- **Error Handling** - Always return meaningful error messages
- **Logging** - Log important operations and errors

### 2. Result Handling
- **Success Results** - Use `OrderResult.success()` for successful operations
- **Error Results** - Use `OrderResult.error()` for failures
- **Business Errors** - Use `OrderResult.business_error()` for business logic failures

### 3. Testing
- **Unit Tests** - Test command logic in isolation
- **Integration Tests** - Test through factory and invoker
- **Error Scenarios** - Test failure cases
- **Edge Cases** - Test boundary conditions

### 4. Documentation
- **Docstrings** - Document all public methods
- **Type Hints** - Use proper type annotations
- **Examples** - Include usage examples in docstrings

## Common Patterns

### 1. Database Operations
```python
async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
    try:
        # Use context services
        order_service = context.get_order_service()
        result = await order_service.some_operation(db=db)
        
        if result.is_success:
            return OrderResult.success("Operation completed")
        else:
            return OrderResult.business_error(result.message)
            
    except Exception as e:
        self.logger.error(f"Database operation failed: {e}")
        return OrderResult.error(f"Operation failed: {str(e)}")
```

### 2. Validation
```python
async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
    # Validate input
    if not self.required_param:
        return OrderResult.business_error("Required parameter missing")
    
    # Validate business rules
    if not await self._validate_business_rules():
        return OrderResult.business_error("Business rule validation failed")
    
    # Execute operation
    # ...
```

### 3. Response Data
```python
# Include response type for downstream processing
result_data = {
    "response_type": "item_added",
    "menu_item_id": self.menu_item_id,
    "quantity": self.quantity,
    "phrase_type": AudioPhraseType.ITEM_ADDED_SUCCESS
}

return OrderResult.success(
    message="Item added successfully",
    data=result_data
)
```

## Troubleshooting

### Common Issues

1. **Command Not Found**
   - Check `CommandType` enum includes your command
   - Verify `INTENT_TO_COMMAND` mapping
   - Ensure command class is imported

2. **Validation Failures**
   - Check required fields in `CommandDataValidator`
   - Verify slot names match command constructor
   - Ensure data types are correct

3. **Execution Failures**
   - Check command constructor parameters
   - Verify database session is available
   - Check service dependencies in context

4. **Test Failures**
   - Mock all external dependencies
   - Use proper async/await patterns
   - Check assertion expectations

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.getLogger("app.commands").setLevel(logging.DEBUG)
   ```

2. **Check Command Creation**
   ```python
   command = CommandFactory.create_command(intent_data, restaurant_id, order_id)
   print(f"Command created: {command}")
   print(f"Command type: {type(command).__name__}")
   ```

3. **Validate Command Data**
   ```python
   is_valid, errors = CommandDataValidator.validate(intent_data)
   if not is_valid:
       print(f"Validation errors: {errors}")
   ```

## Examples

See existing commands for reference:
- `AddItemCommand` - Complex command with validation
- `RemoveItemCommand` - Simple command with database operations
- `ItemUnavailableCommand` - Response-only command
- `ClarificationNeededCommand` - Interactive command

## Conclusion

The command system is designed to be:
- **Extensible** - Easy to add new commands
- **Testable** - Clear separation of concerns
- **Reliable** - Proper error handling and validation
- **Maintainable** - Consistent patterns and documentation

Follow this guide and you'll be able to create robust, well-tested commands that integrate seamlessly with the AI DriveThru system!
