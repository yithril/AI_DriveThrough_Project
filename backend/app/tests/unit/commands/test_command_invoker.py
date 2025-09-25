"""
Unit tests for CommandInvoker functionality
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.commands.command_invoker import CommandInvoker
from app.commands.command_context import CommandContext
from app.commands.base_command import BaseCommand
from app.commands.item_unavailable_command import ItemUnavailableCommand
from app.dto.order_result import OrderResult, CommandBatchResult, ErrorCategory, ErrorCode


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


class TestCommandInvoker:
    """Test CommandInvoker functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def command_context(self, mock_db):
        """Create CommandContext with mocked services"""
        context = CommandContext(
            session_id="test_session",
            restaurant_id=1,
            order_id=123
        )
        context.set_db_session(mock_db)
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
        assert batch_result.all_succeeded
    
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
        assert not batch_result.all_succeeded
        assert not batch_result.all_failed
    
    @pytest.mark.asyncio
    async def test_item_unavailable_command_success(self, command_invoker, command_context):
        """Test that ItemUnavailableCommand returns success (not error)"""
        command = ItemUnavailableCommand(
            restaurant_id=1,
            order_id=123,
            requested_item="Quantum Cheeseburger",
            message="Sorry, we don't have Quantum Cheeseburger on our menu"
        )
        
        result = await command_invoker.execute_command(command, command_context)
        
        # ItemUnavailableCommand should return SUCCESS (not error) because it's a successful response to user
        assert result.is_success
        assert "Quantum Cheeseburger" in result.message
        assert result.data is not None
        assert result.data.get("response_type") == "item_unavailable"
    
    @pytest.mark.asyncio
    async def test_item_unavailable_command_batch(self, command_invoker, command_context):
        """Test ItemUnavailableCommand in batch execution"""
        commands = [
            ItemUnavailableCommand(1, 123, "Quantum Cheeseburger", "Sorry, we don't have Quantum Cheeseburger"),
            ItemUnavailableCommand(1, 123, "Flying Pizza", "Sorry, we don't have Flying Pizza")
        ]
        
        batch_result = await command_invoker.execute_multiple_commands(commands, command_context)
        
        # Both ItemUnavailableCommand should be treated as successes
        assert batch_result.total_commands == 2
        assert batch_result.successful_commands == 2
        assert batch_result.failed_commands == 0
        assert batch_result.all_succeeded
    
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
    
    def test_command_invoker_initialization(self, command_invoker):
        """Test that CommandInvoker initializes correctly"""
        assert command_invoker.command_history == []
    
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
