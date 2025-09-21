"""
Unit tests for CommandInvoker functionality - New Architecture
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.commands.command_invoker import CommandInvoker
from app.commands.command_context import CommandContext
from app.commands.base_command import BaseCommand
from app.dto.order_result import OrderResult, CommandBatchResult, ErrorCategory, ErrorCode, FollowUpAction


class MockOrderService:
    """Mock OrderService for testing"""
    
    def __init__(self):
        self.orders = {}
    
    async def add_item_to_order(self, order_id: int, menu_item_id: int, quantity: int, customizations=None, special_instructions=None):
        """Mock add item to order - always succeeds for testing"""
        return OrderResult.success(f"Added {quantity}x item {menu_item_id} to order {order_id}")
    
    async def remove_item_from_order(self, order_id: int, order_item_id: int):
        """Mock remove item from order - always succeeds for testing"""
        return OrderResult.success(f"Removed item {order_item_id} from order {order_id}")
    
    async def clear_order(self, order_id: int):
        """Mock clear order - always succeeds for testing"""
        return OrderResult.success(f"Cleared order {order_id}")


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


class MockCommand(BaseCommand):
    """Mock command for testing"""
    
    def __init__(self, restaurant_id: int, order_id: int, should_succeed: bool = True, error_message: str = None):
        super().__init__(restaurant_id, order_id)
        self.should_succeed = should_succeed
        self.error_message = error_message or "Mock command error"
    
    async def execute(self, context: CommandContext, db):
        if self.should_succeed:
            return OrderResult.success(f"Mock command {self.command_name} succeeded")
        else:
            return OrderResult.business_error(self.error_message, error_code=ErrorCode.ITEM_UNAVAILABLE)
    
    def _get_parameters(self):
        return {"should_succeed": self.should_succeed}


class TestCommandContext:
    """Test CommandContext functionality"""
    
    def test_context_creation(self):
        """Test basic context creation"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            user_id="test_user",
            order_id=123
        )
        
        assert context.session_id == "test_session"
        assert context.restaurant_id == 1
        assert context.user_id == "test_user"
        assert context.order_id == 123
        assert context.db_session is None
        assert context.order_service is None
    
    def test_context_scoping_properties(self):
        """Test context scoping properties"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        
        assert context.is_order_scoped is True
        assert context.is_session_scoped is True
        
        # Test without order_id
        context_no_order = CommandContext(
            session_id="test_session",
            restaurant_id=1
        )
        
        assert context_no_order.is_order_scoped is False
        assert context_no_order.is_session_scoped is True
    
    def test_context_service_setters(self):
        """Test setting services on context"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1
        )
        
        mock_service = MockOrderService()
        mock_session_service = MockOrderSessionService()
        mock_validator = MockCustomizationValidator()
        mock_db = AsyncMock()
        
        context.set_order_service(mock_service)
        context.set_order_session_service(mock_session_service)
        context.set_customization_validator(mock_validator)
        context.set_db_session(mock_db)
        
        assert context.order_service == mock_service
        assert context.order_session_service == mock_session_service
        assert context.customization_validator == mock_validator
        assert context.db_session == mock_db
    
    def test_context_getters(self):
        """Test context getter methods"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        
        assert context.get_order_id() == 123
        assert context.get_session_id() == "test_session"
        
        # Test error cases
        context_no_order = CommandContext(
            session_id="test_session",
            restaurant_id=1
        )
        
        with pytest.raises(ValueError, match="Command context is not scoped to an order"):
            context_no_order.get_order_id()
        
        # Test with None session_id by manually setting it after creation
        context_no_session = CommandContext(
            session_id="test_session",  # Required parameter
            restaurant_id=1,
            order_id=123
        )
        context_no_session.session_id = None  # Manually set to None to test error case
        
        with pytest.raises(ValueError, match="Command context is not scoped to a session"):
            context_no_session.get_session_id()
    
    def test_context_cloning(self):
        """Test context cloning methods"""
        original_context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            user_id="test_user",
            order_id=123
        )
        
        original_context.set_order_service(MockOrderService())
        original_context.metadata["test_key"] = "test_value"
        
        # Test with_order_id
        new_context = original_context.with_order_id(456)
        assert new_context.order_id == 456
        assert new_context.session_id == "test_session"  # Should be preserved
        assert new_context.restaurant_id == 1  # Should be preserved
        assert new_context.user_id == "test_user"  # Should be preserved
        assert new_context.order_service is not None  # Should be preserved
        assert new_context.metadata["test_key"] == "test_value"  # Should be copied
        
        # Test with_session_id
        new_session_context = original_context.with_session_id("new_session")
        assert new_session_context.session_id == "new_session"
        assert new_session_context.order_id == 123  # Should be preserved
        assert new_session_context.restaurant_id == 1  # Should be preserved


class TestCommandInvoker:
    """Test CommandInvoker functionality"""
    
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
    async def test_execute_single_command_success(self, command_invoker, command_context):
        """Test executing a single successful command"""
        command = MockCommand(restaurant_id=1, order_id=123, should_succeed=True)
        
        result = await command_invoker.execute_command(command, command_context)
        
        assert result.is_success
        assert "Mock command mock succeeded" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_single_command_failure(self, command_invoker, command_context):
        """Test executing a single failing command"""
        command = MockCommand(restaurant_id=1, order_id=123, should_succeed=False)
        
        result = await command_invoker.execute_command(command, command_context)
        
        assert result.is_error
        assert result.error_category == ErrorCategory.BUSINESS
        assert result.error_code == ErrorCode.ITEM_UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_execute_multiple_commands_all_success(self, command_invoker, command_context):
        """Test executing multiple commands that all succeed"""
        commands = [
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True)
        ]
        
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        assert isinstance(batch_result, CommandBatchResult)
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 3
        assert batch_result.failed_commands == 0
        assert batch_result.follow_up_action == FollowUpAction.CONTINUE
        assert "3 commands succeeded" in batch_result.summary_message
    
    @pytest.mark.asyncio
    async def test_execute_multiple_commands_mixed_results(self, command_invoker, command_context):
        """Test executing multiple commands with mixed success and failure"""
        commands = [
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=False, error_message="Business error"),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True)
        ]
        
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        assert isinstance(batch_result, CommandBatchResult)
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 2
        assert batch_result.failed_commands == 1
        assert batch_result.follow_up_action == FollowUpAction.ASK  # Business error should trigger ASK
        assert "2 commands succeeded" in batch_result.summary_message
        assert "1 command failed" in batch_result.summary_message
    
    @pytest.mark.asyncio
    async def test_execute_multiple_commands_no_early_termination(self, command_invoker, command_context):
        """Test that command execution continues even when some commands fail"""
        commands = [
            MockCommand(restaurant_id=1, order_id=123, should_succeed=False, error_message="First command failed"),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=False, error_message="Third command failed")
        ]
        
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        # All commands should have been executed
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 1
        assert batch_result.failed_commands == 2
        
        # Check that all results are present
        results = batch_result.results
        assert len(results) == 3
        assert results[0].is_error  # First command failed
        assert results[1].is_success  # Second command succeeded
        assert results[2].is_error  # Third command failed
    
    @pytest.mark.asyncio
    async def test_execute_multiple_commands_exception_handling(self, command_invoker, command_context):
        """Test that exceptions during command execution are handled gracefully"""
        # Create a command that raises an exception
        class ExceptionCommand(BaseCommand):
            async def execute(self, context: CommandContext, db):
                raise Exception("Simulated system error")
            
            def _get_parameters(self):
                return {}
        
        commands = [
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True),
            ExceptionCommand(restaurant_id=1, order_id=123),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True)
        ]
        
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        # All commands should have been attempted
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 2
        assert batch_result.failed_commands == 1
        
        # The exception should be categorized as a system error
        failed_result = batch_result.get_failed_results()[0]
        assert failed_result.error_category == ErrorCategory.SYSTEM
        assert failed_result.error_code == ErrorCode.INTERNAL_ERROR
        assert "Command execution failed" in failed_result.message
        
        # System error should trigger STOP action
        assert batch_result.follow_up_action == FollowUpAction.STOP
    
    @pytest.mark.asyncio
    async def test_command_history_tracking(self, command_invoker, command_context):
        """Test that commands are tracked in history"""
        command = MockCommand(restaurant_id=1, order_id=123, should_succeed=True)
        
        await command_invoker.execute_command(command, command_context)
        
        history = command_invoker.get_command_history()
        assert len(history) == 1
        
        history_entry = history[0]
        assert "command" in history_entry
        assert "result" in history_entry
        assert "timestamp" in history_entry
        assert history_entry["command"]["command"] == "mock"
        assert history_entry["result"]["is_success"] is True
    
    @pytest.mark.asyncio
    async def test_command_history_limit(self, command_invoker, command_context):
        """Test that command history is limited to 50 entries"""
        # Execute more than 50 commands to trigger the limit
        for i in range(55):
            command = MockCommand(restaurant_id=1, order_id=123, should_succeed=True)
            await command_invoker.execute_command(command, command_context)
        
        history = command_invoker.get_command_history()
        assert len(history) == 50  # Should be limited to 50
    
    def test_get_command_history_with_limit(self, command_invoker):
        """Test getting command history with a limit"""
        # Add 10 commands to history
        for i in range(10):
            command_invoker.command_history.append({
                "command": {"command": f"test_{i}"},
                "result": {"is_success": True},
                "timestamp": f"2024-01-01T00:00:{i:02d}"
            })
        
        # Get last 5 commands
        recent_history = command_invoker.get_command_history(limit=5)
        assert len(recent_history) == 5
        assert recent_history[0]["command"]["command"] == "test_5"  # Should start from test_5
    
    def test_clear_history(self, command_invoker):
        """Test clearing command history"""
        # Add some commands to history
        command_invoker.command_history.append({
            "command": {"command": "test"},
            "result": {"is_success": True},
            "timestamp": "2024-01-01T00:00:00"
        })
        
        assert len(command_invoker.command_history) == 1
        
        command_invoker.clear_history()
        assert len(command_invoker.command_history) == 0
    
    @pytest.mark.asyncio
    async def test_command_names_tracking_in_batch(self, command_invoker, command_context):
        """Test that command names are properly tracked in batch execution"""
        commands = [
            MockCommand(restaurant_id=1, order_id=123, should_succeed=True),
            MockCommand(restaurant_id=1, order_id=123, should_succeed=False)
        ]
        
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        # Command names should be tracked (though not directly exposed in current implementation)
        # This test ensures the command names are passed to CommandBatchResult.from_results
        assert batch_result.total_commands == 2
        assert len(batch_result.results) == 2
    
    def test_command_invoker_initialization(self, command_invoker):
        """Test that CommandInvoker initializes correctly"""
        assert command_invoker.command_history == []
    
    @pytest.mark.asyncio
    async def test_command_execution_with_context_services(self, command_invoker, command_context):
        """Test that commands can access services from context"""
        # Create a command that uses context services
        class ServiceUsingCommand(BaseCommand):
            async def execute(self, context: CommandContext, db):
                # Test that services are available
                assert context.order_service is not None
                assert context.order_session_service is not None
                assert context.customization_validator is not None
                assert context.db_session is not None
                
                return OrderResult.success("Services accessed successfully")
            
            def _get_parameters(self):
                return {}
        
        command = ServiceUsingCommand(restaurant_id=1, order_id=123)
        result = await command_invoker.execute_command(command, command_context)
        
        assert result.is_success
        assert "Services accessed successfully" in result.message
