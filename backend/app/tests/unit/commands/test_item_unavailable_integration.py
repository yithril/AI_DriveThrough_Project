"""
Integration test for ItemUnavailableCommand with CommandInvoker
"""

import pytest
from unittest.mock import AsyncMock
from app.commands.command_invoker import CommandInvoker
from app.commands.command_context import CommandContext
from app.commands.item_unavailable_command import ItemUnavailableCommand
from app.dto.order_result import OrderResult


class TestItemUnavailableIntegration:
    """Test ItemUnavailableCommand integration with CommandInvoker"""
    
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
        assert result.data.get("requested_item") == "Quantum Cheeseburger"
    
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
        
        # Check individual results
        results = batch_result.results
        assert len(results) == 2
        assert results[0].is_success
        assert results[1].is_success
        assert "Quantum Cheeseburger" in results[0].message
        assert "Flying Pizza" in results[1].message
    
    @pytest.mark.asyncio
    async def test_item_unavailable_with_default_message(self, command_invoker, command_context):
        """Test ItemUnavailableCommand with default message generation"""
        command = ItemUnavailableCommand(
            restaurant_id=1,
            order_id=123,
            requested_item="Mystery Burger"
            # No custom message provided
        )
        
        result = await command_invoker.execute_command(command, command_context)
        
        assert result.is_success
        assert "Mystery Burger" in result.message
        assert "Sorry, we don't have Mystery Burger on our menu" == result.message
    
    @pytest.mark.asyncio
    async def test_item_unavailable_command_attributes(self, command_invoker, command_context):
        """Test that ItemUnavailableCommand has all required attributes"""
        command = ItemUnavailableCommand(
            restaurant_id=1,
            order_id=123,
            requested_item="Test Item"
        )
        
        # Check that all required attributes exist
        assert hasattr(command, 'logger')
        assert hasattr(command, 'confidence')
        assert command.confidence == 1.0
        assert command.requested_item == "Test Item"
        assert command.message == "Sorry, we don't have Test Item on our menu"
        
        # Test to_dict method
        command_dict = command.to_dict()
        assert command_dict["intent"] == "ITEM_UNAVAILABLE"
        assert command_dict["confidence"] == 1.0
        assert command_dict["slots"]["requested_item"] == "Test Item"
        assert command_dict["slots"]["message"] == "Sorry, we don't have Test Item on our menu"
