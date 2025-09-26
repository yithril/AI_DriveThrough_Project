"""
Unit tests for CommandExecutorService
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.core.services.conversation.command_executor_service import CommandExecutorService
from app.dto.order_result import OrderResult, CommandBatchResult


class TestCommandExecutorService:
    """Test cases for CommandExecutorService"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        factory = Mock()
        factory.create_order_service.return_value = AsyncMock()
        factory.create_order_session_service.return_value = AsyncMock()
        factory.create_customization_validator.return_value = Mock()
        return factory
    
    @pytest.fixture
    def service(self, mock_service_factory):
        """Create service with mocked dependencies"""
        return CommandExecutorService(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_execute_commands_success(self, service, mocker):
        """Test successful command execution"""
        # Mock the command invoker
        mock_invoker = mocker.patch('app.core.services.conversation.command_executor_service.CommandInvoker')
        mock_invoker_instance = AsyncMock()
        mock_invoker.return_value = mock_invoker_instance
        
        # Mock the batch result
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.has_successes = True
        mock_batch_result.has_failures = False
        mock_batch_result.summary_message = "Items added successfully"
        mock_invoker_instance.execute_multiple_commands.return_value = mock_batch_result
        
        # Mock the unit of work
        mock_uow = mocker.patch('app.core.services.conversation.command_executor_service.UnitOfWork')
        mock_uow_instance = AsyncMock()
        mock_uow.return_value = mock_uow_instance
        mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow_instance)
        mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
        
        # Test the service
        commands = [{"intent": "ADD_ITEM", "confidence": 0.9, "slots": {"menu_item_id": 1, "quantity": 1}}]
        result = await service.execute_commands(
            commands=commands,
            session_id="test-session",
            restaurant_id="1",
            shared_db_session=Mock()
        )
        
        # Verify result
        assert result["success"] is True
        assert "Items added successfully" in result["response_text"]
        assert result["command_batch_result"] == mock_batch_result
    
    @pytest.mark.asyncio
    async def test_execute_commands_no_commands(self, service, mocker):
        """Test execution with no commands"""
        # Test the service
        result = await service.execute_commands(
            commands=[],
            session_id="test-session",
            restaurant_id="1",
            shared_db_session=Mock()
        )
        
        # Verify result
        assert result["success"] is False
        assert "didn't understand" in result["response_text"]
        assert len(result["validation_errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_commands_validation_failure(self, service, mocker):
        """Test command execution with validation failures"""
        # Mock the command data validator
        mock_validator = mocker.patch('app.core.services.conversation.command_executor_service.CommandDataValidator')
        mock_validator.validate.return_value = (False, ["Invalid command"])
        mock_validator.get_validation_summary.return_value = "Invalid command"
        
        # Test the service
        commands = [{"intent": "INVALID", "confidence": 0.9, "slots": {"invalid_field": "value"}}]
        result = await service.execute_commands(
            commands=commands,
            session_id="test-session",
            restaurant_id="1",
            shared_db_session=Mock()
        )
        
        # Verify result
        assert result["success"] is False
        assert "couldn't understand" in result["response_text"]
        assert len(result["validation_errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_commands_mixed_results(self, service, mocker):
        """Test command execution with mixed success/failure results"""
        # Mock the command invoker
        mock_invoker = mocker.patch('app.core.services.conversation.command_executor_service.CommandInvoker')
        mock_invoker_instance = AsyncMock()
        mock_invoker.return_value = mock_invoker_instance
        
        # Mock the batch result with mixed results
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.has_successes = True
        mock_batch_result.has_failures = True
        mock_batch_result.summary_message = "Some items added, some failed"
        mock_invoker_instance.execute_multiple_commands.return_value = mock_batch_result
        
        # Mock the unit of work
        mock_uow = mocker.patch('app.core.services.conversation.command_executor_service.UnitOfWork')
        mock_uow_instance = AsyncMock()
        mock_uow.return_value = mock_uow_instance
        mock_uow_instance.__aenter__ = AsyncMock(return_value=mock_uow_instance)
        mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
        
        # Test the service
        commands = [{"intent": "ADD_ITEM", "confidence": 0.9, "slots": {"menu_item_id": 1, "quantity": 1}}]
        result = await service.execute_commands(
            commands=commands,
            session_id="test-session",
            restaurant_id="1",
            shared_db_session=Mock()
        )
        
        # Verify result
        assert result["success"] is True
        assert "Some items added, some failed" in result["response_text"]
        assert "couldn't be added" in result["response_text"]
    
    @pytest.mark.asyncio
    async def test_execute_commands_exception(self, service, mocker):
        """Test command execution with exception"""
        # Mock the unit of work to raise exception
        mock_uow = mocker.patch('app.core.services.conversation.command_executor_service.UnitOfWork')
        mock_uow_instance = AsyncMock()
        mock_uow.return_value = mock_uow_instance
        mock_uow_instance.__aenter__ = AsyncMock(side_effect=Exception("UoW failed"))
        mock_uow_instance.__aexit__ = AsyncMock(return_value=None)
        
        # Test the service
        commands = [{"intent": "ADD_ITEM", "confidence": 0.9, "slots": {"menu_item_id": 1, "quantity": 1}}]
        result = await service.execute_commands(
            commands=commands,
            session_id="test-session",
            restaurant_id="1",
            shared_db_session=Mock()
        )
        
        # Verify result
        assert result["success"] is False
        assert "error processing" in result["response_text"]
        assert len(result["validation_errors"]) > 0
    
    def test_should_continue_after_execution(self, service):
        """Test routing decision after command execution"""
        execution_result = {"success": True}
        
        next_step = service.should_continue_after_execution(execution_result)
        assert next_step == "final_response_aggregator"
