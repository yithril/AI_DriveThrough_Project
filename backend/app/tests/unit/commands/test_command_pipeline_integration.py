"""
Comprehensive integration test for ALL commands through CommandFactory -> CommandInvoker pipeline
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.commands.command_factory import CommandFactory
from app.commands.command_invoker import CommandInvoker
from app.commands.command_context import CommandContext
from app.dto.order_result import OrderResult, ErrorCategory, ErrorCode


class MockOrderService:
    """Mock OrderService for testing"""
    
    def __init__(self):
        self.orders = {}
    
    async def add_item_to_order(self, order_id: int, menu_item_id: int, quantity: int, customizations=None, special_instructions=None, size=None, db=None):
        """Mock add item to order - always succeeds for testing"""
        return OrderResult.success(f"Added {quantity}x item {menu_item_id} to order {order_id}")
    
    async def remove_item_from_order(self, order_id: int, order_item_id: int, db=None):
        """Mock remove item from order - always succeeds for testing"""
        return OrderResult.success(f"Removed item {order_item_id} from order {order_id}")
    
    async def clear_order(self, order_id: int, db=None):
        """Mock clear order - always succeeds for testing"""
        return OrderResult.success(f"Cleared order {order_id}")
    
    async def get_order(self, order_id: int, db=None):
        """Mock get order for confirm order command"""
        return OrderResult.success("Order retrieved", data={"order_id": order_id, "items": []})


class MockOrderSessionService:
    """Mock OrderSessionService for testing"""
    
    def __init__(self):
        self.sessions = {}
    
    async def get_session(self, session_id: str):
        """Mock get session"""
        return {"session_id": session_id, "restaurant_id": 1}


class MockCustomizationValidator:
    """Mock CustomizationValidator for testing"""
    
    def __init__(self):
        pass
    
    def validate_customizations(self, menu_item_id: int, customizations: dict):
        """Mock validation - always succeeds"""
        return True


class TestCommandPipelineIntegration:
    """Test ALL commands through CommandFactory -> CommandInvoker pipeline"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_order_service(self):
        """Mock order service"""
        return MockOrderService()
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Mock order session service"""
        return MockOrderSessionService()
    
    @pytest.fixture
    def mock_customization_validator(self):
        """Mock customization validator"""
        return MockCustomizationValidator()
    
    @pytest.fixture
    def command_context(self, mock_db, mock_order_service, mock_order_session_service, mock_customization_validator):
        """Create CommandContext with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_db_session(mock_db)
        context.set_order_service(mock_order_service)
        context.set_order_session_service(mock_order_session_service)
        context.set_customization_validator(mock_customization_validator)
        return context
    
    @pytest.fixture
    def command_invoker(self):
        """Create CommandInvoker instance for testing"""
        return CommandInvoker()
    
    @pytest.mark.asyncio
    async def test_add_item_command_pipeline(self, command_invoker, command_context):
        """Test ADD_ITEM command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "ADD_ITEM",
            "confidence": 0.9,
            "slots": {
                "menu_item_id": 1,
                "quantity": 2,
                "size": "large",
                "customizations": {"no_onions": True}
            },
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "AddItemCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed (even though we're mocking the service)
        assert result.is_success
        assert "Added" in result.message
    
    @pytest.mark.asyncio
    async def test_remove_item_command_pipeline(self, command_invoker, command_context):
        """Test REMOVE_ITEM command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "REMOVE_ITEM",
            "confidence": 0.9,
            "slots": {
                "order_item_id": 1
            },
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "RemoveItemCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed
        assert result.is_success
        assert "removed" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_clear_order_command_pipeline(self, command_invoker, command_context):
        """Test CLEAR_ORDER command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "CLEAR_ORDER",
            "confidence": 0.9,
            "slots": {},
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "ClearOrderCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed
        assert result.is_success
        assert "cleared" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_confirm_order_command_pipeline(self, command_invoker, command_context):
        """Test CONFIRM_ORDER command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "CONFIRM_ORDER",
            "confidence": 0.9,
            "slots": {},
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "ConfirmOrderCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should fail because order is empty (this is correct behavior)
        assert result.is_error
        assert "empty order" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_question_command_pipeline(self, command_invoker, command_context):
        """Test QUESTION command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "QUESTION",
            "confidence": 0.9,
            "slots": {
                "question": "What are your hours?"
            },
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "QuestionCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed
        assert result.is_success
        assert "help" in result.message.lower() or "menu" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_item_unavailable_command_pipeline(self, command_invoker, command_context):
        """Test ITEM_UNAVAILABLE command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "ITEM_UNAVAILABLE",
            "confidence": 1.0,
            "slots": {
                "requested_item": "Quantum Cheeseburger",
                "message": "Sorry, we don't have Quantum Cheeseburger on our menu"
            },
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "ItemUnavailableCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed (this is a successful response to user)
        assert result.is_success
        assert "Quantum Cheeseburger" in result.message
        assert result.data is not None
        assert result.data.get("response_type") == "item_unavailable"
    
    @pytest.mark.asyncio
    async def test_clarification_needed_command_pipeline(self, command_invoker, command_context):
        """Test CLARIFICATION_NEEDED command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "CLARIFICATION_NEEDED",
            "confidence": 0.8,
            "slots": {
                "ambiguous_item": "fries",
                "suggested_options": ["French Fries", "Sweet Potato Fries"],
                "clarification_question": "Did you mean French Fries or Sweet Potato Fries?"
            },
            "needs_clarification": True
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "ClarificationNeededCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed (this is a successful response to user)
        assert result.is_success
        assert "clarification" in result.message.lower()
        assert result.data is not None
        assert result.data.get("clarification_type") == "ambiguous_item"
    
    @pytest.mark.asyncio
    async def test_unknown_command_pipeline(self, command_invoker, command_context):
        """Test UNKNOWN command through factory -> invoker pipeline"""
        intent_data = {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "slots": {
                "user_input": "blah blah blah"
            },
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        assert command is not None
        assert command.__class__.__name__ == "UnknownCommand"
        
        # Execute through invoker
        result = await command_invoker.execute_command(command, command_context)
        
        # Should succeed (this is a successful response to user)
        assert result.is_success
        assert "didn't understand" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_mixed_commands_batch_pipeline(self, command_invoker, command_context):
        """Test multiple different commands in batch execution"""
        intent_data_list = [
            {
                "intent": "ADD_ITEM",
                "confidence": 0.9,
                "slots": {"menu_item_id": 1, "quantity": 1},
                "needs_clarification": False
            },
            {
                "intent": "ITEM_UNAVAILABLE",
                "confidence": 1.0,
                "slots": {"requested_item": "Quantum Burger", "message": "Sorry, we don't have Quantum Burger"},
                "needs_clarification": False
            },
            {
                "intent": "CLARIFICATION_NEEDED",
                "confidence": 0.8,
                "slots": {"ambiguous_item": "fries", "clarification_question": "Which fries?"},
                "needs_clarification": True
            }
        ]
        
        # Create commands through factory
        commands = []
        for intent_data in intent_data_list:
            command = CommandFactory.create_command(intent_data, 1, 123)
            assert command is not None
            commands.append(command)
        
        # Execute batch through invoker
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        # All should succeed (they're all valid responses to user)
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 3
        assert batch_result.failed_commands == 0
        assert batch_result.all_succeeded
        
        # Check individual results
        results = batch_result.results
        assert len(results) == 3
        assert all(result.is_success for result in results)
    
    @pytest.mark.asyncio
    async def test_unsupported_intent_handling(self, command_invoker, command_context):
        """Test that unsupported intents are handled gracefully"""
        intent_data = {
            "intent": "UNSUPPORTED_INTENT",
            "confidence": 0.9,
            "slots": {},
            "needs_clarification": False
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        
        # Should return None for unsupported intent
        assert command is None
    
    @pytest.mark.asyncio
    async def test_invalid_intent_data_handling(self, command_invoker, command_context):
        """Test that invalid intent data is handled gracefully"""
        # Missing required fields
        intent_data = {
            "intent": "ADD_ITEM",
            # Missing confidence and slots
        }
        
        # Create command through factory
        command = CommandFactory.create_command(intent_data, 1, 123)
        
        # Should still create command (CommandFactory doesn't validate, CommandDataValidator does)
        assert command is not None
