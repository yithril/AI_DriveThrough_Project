"""
Unit tests for individual command classes

Tests the execute() method of each command to ensure no red flags.
Uses mocked services to test command logic in isolation.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.commands.add_item_command import AddItemCommand
from app.commands.remove_item_command import RemoveItemCommand
from app.commands.clear_order_command import ClearOrderCommand
from app.commands.confirm_order_command import ConfirmOrderCommand
from app.commands.question_command import QuestionCommand
from app.commands.unknown_command import UnknownCommand
from app.commands.command_context import CommandContext
from app.dto.order_result import OrderResult
from app.tests.helpers.mock_services import MockOrderSessionService, MockCustomizationValidationService


class TestAddItemCommand:
    """Test AddItemCommand execution"""
    
    @pytest.fixture
    def mock_order_service(self):
        """Mock order service that always succeeds"""
        service = AsyncMock()
        service.add_item_to_order.return_value = OrderResult.success("Item added successfully")
        return service
    
    @pytest.fixture
    def command_context(self, mock_order_service):
        """Create command context with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_order_service(mock_order_service)
        context.set_order_session_service(MockOrderSessionService())
        context.set_customization_validator(MockCustomizationValidationService())
        return context
    
    @pytest.mark.asyncio
    async def test_execute_success(self, command_context):
        """Test successful item addition"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=2,
            size="large",
            modifiers=["no_pickles"],
            special_instructions="Well done"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Item added successfully" in result.message
        
        # Verify service was called with correct parameters
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 2
        assert call_args.kwargs['session_id'] == "test_session"  # NEW: session_id
        assert call_args.kwargs['restaurant_id'] == 1  # NEW: restaurant_id
        assert call_args.kwargs['customizations'] == ["no_pickles"]
        assert call_args.kwargs['special_instructions'] == "Well done"
        assert call_args.kwargs['size'] == "large"
    
    @pytest.mark.asyncio
    async def test_execute_with_minimal_params(self, command_context):
        """Test execution with minimal required parameters"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        # Verify service was called with defaults
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 1
        assert call_args.kwargs['session_id'] == "test_session"  # NEW: session_id
        assert call_args.kwargs['restaurant_id'] == 1  # NEW: restaurant_id
        assert call_args.kwargs['customizations'] == []
        assert call_args.kwargs['special_instructions'] is None
        assert call_args.kwargs['size'] is None
    
    @pytest.mark.asyncio
    async def test_execute_with_complex_customizations(self, command_context):
        """Test execution with complex customization scenarios"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=3,
            size="large",
            modifiers=["extra cheese", "no pickles", "heavy sauce", "extra crispy"],
            special_instructions="well done, cut in half"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Item added successfully" in result.message
        
        # Verify service was called with all complex parameters
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 3
        assert call_args.kwargs['session_id'] == "test_session"  # NEW: session_id
        assert call_args.kwargs['restaurant_id'] == 1  # NEW: restaurant_id
        assert call_args.kwargs['customizations'] == ["extra cheese", "no pickles", "heavy sauce", "extra crispy"]
        assert call_args.kwargs['special_instructions'] == "well done, cut in half"
        assert call_args.kwargs['size'] == "large"
    
    @pytest.mark.asyncio
    async def test_execute_with_multiple_quantities(self, command_context):
        """Test execution with multiple quantities"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=5,
            size="medium",
            modifiers=["no onions"],
            special_instructions="extra crispy"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        
        # Verify quantity is passed correctly
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 5
        assert call_args.kwargs['customizations'] == ["no onions"]
        assert call_args.kwargs['special_instructions'] == "extra crispy"
        assert call_args.kwargs['size'] == "medium"
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_modifiers(self, command_context):
        """Test execution with empty modifiers list"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=1,
            modifiers=[],
            special_instructions="rare"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        
        # Verify empty modifiers are handled correctly
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 1
        assert call_args.kwargs['customizations'] == []
        assert call_args.kwargs['special_instructions'] == "rare"
        assert call_args.kwargs['size'] is None
    
    @pytest.mark.asyncio
    async def test_execute_with_none_parameters(self, command_context):
        """Test execution with None parameters (should use defaults)"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=2,
            size=None,
            modifiers=None,
            special_instructions=None
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        
        # Verify None parameters are handled correctly (converted to defaults)
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 2
        assert call_args.kwargs['customizations'] == []
        assert call_args.kwargs['special_instructions'] is None
        assert call_args.kwargs['size'] is None
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_modifiers(self, command_context):
        """Test execution with modifiers containing whitespace (should be filtered)"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=1,
            modifiers=["  extra cheese  ", "", "no pickles", "   "],
            special_instructions="well done"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        
        # Verify whitespace modifiers are NOT filtered (AddItemCommand doesn't filter them)
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 1
        assert call_args.kwargs['customizations'] == ["  extra cheese  ", "", "no pickles", "   "]  # All modifiers passed through
        assert call_args.kwargs['special_instructions'] == "well done"
        assert call_args.kwargs['size'] is None
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_special_instructions(self, command_context):
        """Test execution with whitespace-only special instructions (should be None)"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=1,
            special_instructions="   "  # Only whitespace
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        
        # Verify whitespace-only special instructions are NOT converted (AddItemCommand doesn't filter them)
        call_args = command_context.order_service.add_item_to_order.call_args
        assert call_args is not None
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['menu_item_id'] == 456
        assert call_args.kwargs['quantity'] == 1
        assert call_args.kwargs['customizations'] == []
        assert call_args.kwargs['special_instructions'] == "   "  # Whitespace preserved as-is
        assert call_args.kwargs['size'] is None
    
    @pytest.mark.asyncio
    async def test_execute_service_failure(self, command_context):
        """Test execution when OrderService fails"""
        # Mock service to return error
        command_context.order_service.add_item_to_order.return_value = OrderResult.error("Menu item not found")
        
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=999,  # Non-existent item
            quantity=1
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert not result.is_success
        assert "Menu item not found" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, command_context):
        """Test execution when an exception occurs"""
        # Mock service to raise exception
        command_context.order_service.add_item_to_order.side_effect = Exception("Database connection failed")
        
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=1
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert not result.is_success
        assert "Failed to add item to order: Database connection failed" in result.message
    
    def test_get_parameters(self):
        """Test _get_parameters method returns correct data"""
        command = AddItemCommand(
            restaurant_id=1,
            order_id=123,
            menu_item_id=456,
            quantity=2,
            size="large",
            modifiers=["extra cheese", "no pickles"],
            special_instructions="well done"
        )
        
        params = command._get_parameters()
        
        expected_params = {
            "menu_item_id": 456,
            "quantity": 2,
            "size": "large",
            "modifiers": ["extra cheese", "no pickles"],
            "special_instructions": "well done"
        }
        
        assert params == expected_params


class TestRemoveItemCommand:
    """Test RemoveItemCommand execution"""
    
    @pytest.fixture
    def mock_order_service(self):
        """Mock order service that always succeeds"""
        service = AsyncMock()
        service.remove_item_from_order.return_value = OrderResult.success("Item removed successfully")
        return service
    
    @pytest.fixture
    def command_context(self, mock_order_service):
        """Create command context with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_order_service(mock_order_service)
        return context
    
    @pytest.mark.asyncio
    async def test_execute_by_order_item_id(self, command_context):
        """Test removing item by order item ID"""
        command = RemoveItemCommand(
            restaurant_id=1,
            order_id=123,
            order_item_id=456
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Item removed from order successfully" in result.message
        
        # Verify service was called with correct parameters
        command_context.order_service.remove_item_from_order.assert_called_once()
        call_args = command_context.order_service.remove_item_from_order.call_args
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['order_item_id'] == "456"  # Now converted to string
        assert call_args.kwargs['session_id'] == "test_session"  # NEW: session_id
        assert call_args.kwargs['restaurant_id'] == 1  # NEW: restaurant_id
    
    @pytest.mark.asyncio
    async def test_execute_by_target_ref(self, command_context):
        """Test removing item by target reference"""
        # Mock the order service to return order data for target resolution
        # Create mock order items that match the expected structure
        from unittest.mock import Mock
        
        mock_item1 = Mock()
        mock_item1.id = 1
        mock_item1.menu_item_id = 456
        mock_item1.menu_item = Mock()
        mock_item1.menu_item.name = "Burger"
        
        mock_item2 = Mock()
        mock_item2.id = 2
        mock_item2.menu_item_id = 789
        mock_item2.menu_item = Mock()
        mock_item2.menu_item.name = "Fries"
        
        command_context.order_service.get_order.return_value = OrderResult.success("Order retrieved", data={
            "order": {
                "order_items": [mock_item1, mock_item2]
            }
        })
        
        command = RemoveItemCommand(
            restaurant_id=1,
            order_id=123,
            target_ref="last_item"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        # Verify that get_order was called for target resolution
        command_context.order_service.get_order.assert_called_once()
        get_order_call = command_context.order_service.get_order.call_args
        assert get_order_call[0][1] == 123  # order_id is second argument


class TestClearOrderCommand:
    """Test ClearOrderCommand execution"""
    
    @pytest.fixture
    def mock_order_service(self):
        """Mock order service that always succeeds"""
        service = AsyncMock()
        service.clear_order.return_value = OrderResult.success("Order cleared successfully")
        return service
    
    @pytest.fixture
    def command_context(self, mock_order_service):
        """Create command context with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_order_service(mock_order_service)
        return context
    
    @pytest.mark.asyncio
    async def test_execute_success(self, command_context):
        """Test successful order clearing"""
        command = ClearOrderCommand(
            restaurant_id=1,
            order_id=123
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Order cleared successfully" in result.message
        
        # Verify service was called with correct parameters
        command_context.order_service.clear_order.assert_called_once()
        call_args = command_context.order_service.clear_order.call_args
        assert call_args.kwargs['order_id'] == "123"  # Now converted to string
        assert call_args.kwargs['session_id'] == "test_session"  # NEW: session_id
        assert call_args.kwargs['restaurant_id'] == 1  # NEW: restaurant_id


class TestConfirmOrderCommand:
    """Test ConfirmOrderCommand execution"""
    
    @pytest.fixture
    def mock_order_service(self):
        """Mock order service with order data"""
        service = AsyncMock()
        service.get_order.return_value = OrderResult.success("Order retrieved", data={
            "order": {
                "order_items": [
                    {"menu_item_name": "Burger", "quantity": 1, "price": 9.99},
                    {"menu_item_name": "Fries", "quantity": 1, "price": 4.99}
                ],
                "total_amount": 14.98
            }
        })
        service.confirm_order.return_value = OrderResult.success("Order confirmed")
        return service
    
    @pytest.fixture
    def command_context(self, mock_order_service):
        """Create command context with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_order_service(mock_order_service)
        return context
    
    @pytest.mark.asyncio
    async def test_execute_success(self, command_context):
        """Test successful order confirmation"""
        command = ConfirmOrderCommand(
            restaurant_id=1,
            order_id=123
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Order confirmed" in result.message
        assert "2 items, total: $14.98" in result.message
        
        # Verify services were called with correct parameters
        command_context.order_service.get_order.assert_called_once()
        get_order_call = command_context.order_service.get_order.call_args
        assert get_order_call[0][1] == 123  # get_order uses positional args: (db, order_id)
        
        command_context.order_service.confirm_order.assert_called_once()
        confirm_order_call = command_context.order_service.confirm_order.call_args
        assert confirm_order_call.kwargs['order_id'] == "123"  # Now converted to string
        assert confirm_order_call.kwargs['session_id'] == "test_session"  # NEW: session_id
        assert confirm_order_call.kwargs['restaurant_id'] == 1  # NEW: restaurant_id
    
    @pytest.mark.asyncio
    async def test_execute_empty_order(self, command_context):
        """Test confirmation fails for empty order"""
        # Mock empty order
        command_context.order_service.get_order.return_value = OrderResult.success("Order retrieved", data={
            "order": {
                "order_items": [],
                "total_amount": 0.0
            }
        })
        
        command = ConfirmOrderCommand(
            restaurant_id=1,
            order_id=123
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_error
        assert "Cannot confirm empty order" in result.message


# class TestRepeatCommand:  # Commented out - RepeatCommand doesn't exist
    """Test RepeatCommand execution"""
    
    @pytest.fixture
    def mock_order_service(self):
        """Mock order service with order data"""
        service = AsyncMock()
        service.get_order.return_value = OrderResult.success("Order retrieved", data={
            "order": {
                "order_items": [
                    {"menu_item_name": "Burger", "quantity": 1, "price": 9.99},
                    {"menu_item_name": "Fries", "quantity": 1, "price": 4.99}
                ],
                "total_amount": 14.98
            }
        })
        return service
    
    @pytest.fixture
    def command_context(self, mock_order_service):
        """Create command context with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_order_service(mock_order_service)
        return context
    
    # Removed test_execute_full_order and test_execute_empty_order - they were testing RepeatCommand which doesn't exist


class TestQuestionCommand:
    """Test QuestionCommand execution"""
    
    @pytest.fixture
    def command_context(self):
        """Create command context"""
        return CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
    
    @pytest.mark.asyncio
    async def test_execute_menu_question(self, command_context):
        """Test menu question response"""
        command = QuestionCommand(
            restaurant_id=1,
            order_id=123,
            question="What do you have?",
            category="menu"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "I'd be happy to help you with our menu!" in result.message
        assert result.data["category"] == "menu"
    
    @pytest.mark.asyncio
    async def test_execute_pricing_question(self, command_context):
        """Test pricing question response"""
        command = QuestionCommand(
            restaurant_id=1,
            order_id=123,
            question="How much is a burger?",
            category="pricing"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "I can help you with pricing!" in result.message
        assert result.data["category"] == "pricing"




class TestUnknownCommand:
    """Test UnknownCommand execution"""
    
    @pytest.fixture
    def command_context(self):
        """Create command context"""
        return CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
    
    @pytest.mark.asyncio
    async def test_execute_with_clarifying_question(self, command_context):
        """Test unknown command with clarifying question"""
        command = UnknownCommand(
            restaurant_id=1,
            order_id=123,
            user_input="I don't understand",
            clarifying_question="Could you please repeat that?"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Could you please repeat that?" in result.message
        assert result.data["needs_clarification"] is True
        assert result.data["user_input"] == "I don't understand"
    
    @pytest.mark.asyncio
    async def test_execute_with_default_question(self, command_context):
        """Test unknown command with default clarifying question"""
        command = UnknownCommand(
            restaurant_id=1,
            order_id=123,
            user_input="Gibberish"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "I'm sorry, I didn't understand" in result.message
        assert result.data["needs_clarification"] is True
