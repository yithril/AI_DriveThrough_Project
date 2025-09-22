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
from app.commands.repeat_command import RepeatCommand
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
        command_context.order_service.add_item_to_order.assert_called_once_with(
            order_id=123,
            menu_item_id=456,
            quantity=2,
            customizations=["no_pickles"],
            special_instructions="Well done",
            size="large"
        )
    
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
        command_context.order_service.add_item_to_order.assert_called_once_with(
            order_id=123,
            menu_item_id=456,
            quantity=1,
            customizations=[],
            special_instructions=None,
            size=None
        )


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
        command_context.order_service.remove_item_from_order.assert_called_once_with(
            order_id=123,
            order_item_id=456
        )
    
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
        
        # Verify service was called with db and order_id
        command_context.order_service.clear_order.assert_called_once()
        # Check that it was called with db (AsyncMock) and order_id
        call_args = command_context.order_service.clear_order.call_args
        assert call_args[0][1] == 123  # order_id is second argument


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
        
        # Verify services were called with db and order_id
        command_context.order_service.get_order.assert_called_once()
        command_context.order_service.confirm_order.assert_called_once()
        # Check that order_id was passed correctly
        get_order_call = command_context.order_service.get_order.call_args
        confirm_order_call = command_context.order_service.confirm_order.call_args
        assert get_order_call[0][1] == 123  # order_id is second argument
        assert confirm_order_call[0][1] == 123  # order_id is second argument
    
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


class TestRepeatCommand:
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
    
    @pytest.mark.asyncio
    async def test_execute_full_order(self, command_context):
        """Test repeating full order"""
        command = RepeatCommand(
            restaurant_id=1,
            order_id=123,
            scope="full_order"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_success
        assert "Here's your order:" in result.message
        assert "Burger ($9.99)" in result.message
        assert "Fries ($4.99)" in result.message
        assert "Total: $14.98" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_empty_order(self, command_context):
        """Test repeating empty order"""
        command_context.order_service.get_order.return_value = OrderResult.success("Order retrieved", data={
            "order": {
                "order_items": [],
                "total_amount": 0.0
            }
        })
        
        command = RepeatCommand(
            restaurant_id=1,
            order_id=123,
            scope="full_order"
        )
        
        result = await command.execute(command_context, AsyncMock())
        
        assert result.is_error
        assert "No items in order to repeat" in result.message


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
