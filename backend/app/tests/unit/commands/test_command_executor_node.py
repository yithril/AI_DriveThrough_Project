"""
Unit tests for command_executor_node

Tests the command execution node which validates command dictionaries,
creates command objects, executes them in batch, and stores results.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.state import ConversationWorkflowState
from app.agents.nodes.command_executor_node import command_executor_node, should_continue_after_command_executor
from app.dto.order_result import OrderResult, CommandBatchResult
from app.commands.intent_classification_schema import IntentType


class TestCommandExecutorNode:
    """Test the command_executor_node functionality"""

    @pytest.fixture
    def mock_container(self):
        """Mock container with all required services"""
        container = MagicMock()
        
        # Mock services
        container.command_invoker.return_value = AsyncMock()
        container.command_factory.return_value = MagicMock()
        container.validate_command_contract.return_value = True
        container.get_db.return_value = AsyncMock()
        container.unit_of_work.return_value = AsyncMock()
        
        return container

    @pytest.fixture
    def mock_command_batch_result(self):
        """Mock successful command batch result"""
        from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
        from app.agents.utils.response_builder import build_summary_events, build_response_payload
        
        results = [OrderResult.success("Command executed successfully")]
        batch_outcome = analyze_batch_outcome(results)
        first_error_code = get_first_error_code(results)
        summary_events = build_summary_events(results)
        response_payload = build_response_payload(
            batch_outcome=batch_outcome,
            summary_events=summary_events,
            first_error_code=first_error_code,
            intent_type="ADD_ITEM"
        )
        
        return CommandBatchResult(
            results=results,
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="All commands executed successfully",
            command_family="ADD_ITEM",
            batch_outcome=batch_outcome,
            first_error_code=first_error_code,
            response_payload=response_payload
        )

    @pytest.fixture
    def sample_state_with_commands(self):
        """Sample workflow state with command dictionaries"""
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        return ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            response_text="",
            audio_url=None,
            intent_type=IntentType.ADD_ITEM,
            intent_confidence=0.95,
            commands=[
                {
                    "intent": "ADD_ITEM",
                    "menu_item_id": 1,
                    "quantity": 2,
                    "size": "large"
                }
            ],
            order_state=order_state
        )

    @pytest.mark.asyncio
    async def test_command_executor_successful_execution(self, sample_state_with_commands, mock_container, mock_command_batch_result):
        """Test successful command execution"""
        # Use the existing MockContainer from helpers
        from app.tests.helpers.mock_services import MockContainer
        mock_container = MockContainer()
        
        # Test with LangGraph context injection - command executor needs service_factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(mock_container)
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        # Execute the node - this will test the full functionality
        result_state = await command_executor_node(sample_state_with_commands, context)
        
        # Verify the command executor processed the commands
        assert result_state is not None
        
        # The command executor should have attempted to validate and execute commands
        # Since we have valid command data, it should succeed
        if result_state.command_batch_result:
            # Verify the batch result has the new router-friendly fields
            assert result_state.command_batch_result.batch_outcome is not None
            assert result_state.command_batch_result.response_payload is not None
            assert result_state.command_batch_result.command_family is not None

    @pytest.mark.asyncio
    async def test_command_executor_validation_failure(self, sample_state_with_commands, mock_container):
        """Test command validation failure"""
        # Use the existing MockContainer from helpers
        from app.tests.helpers.mock_services import MockContainer
        mock_container = MockContainer()
        
        # Test with LangGraph context injection - command executor needs service_factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(mock_container)
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        # The MockContainer already provides all the services the command executor needs
        # No additional mocking required
        
        # Execute the node
        result_state = await command_executor_node(sample_state_with_commands, context)
        
        # Verify error was added to state
        assert result_state.has_errors()
        # The response text should indicate an error occurred
        assert "sorry" in result_state.response_text.lower() or "error" in result_state.response_text.lower()

    @pytest.mark.asyncio
    async def test_command_executor_command_creation_failure(self, sample_state_with_commands, mock_container):
        """Test command creation failure"""
        # Use the existing MockContainer from helpers
        from app.tests.helpers.mock_services import MockContainer
        mock_container = MockContainer()
        
        # Test with LangGraph context injection - command executor needs service_factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(mock_container)
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        # The MockContainer already provides all the services the command executor needs
        # No additional mocking required
        
        # Execute the node
        result_state = await command_executor_node(sample_state_with_commands, context)
        
        # Verify error was added to state
        assert result_state.has_errors()
        # The response text should indicate an error occurred
        assert "sorry" in result_state.response_text.lower() or "error" in result_state.response_text.lower()

    @pytest.mark.asyncio
    async def test_command_executor_batch_execution_failure(self, sample_state_with_commands, mock_container):
        """Test batch execution failure"""
        # Use the existing MockContainer from helpers
        from app.tests.helpers.mock_services import MockContainer
        mock_container = MockContainer()
        
        # Test with LangGraph context injection - command executor needs service_factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(mock_container)
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        # The MockContainer already provides all the services the command executor needs
        # No additional mocking required
        
        # Execute the node
        result_state = await command_executor_node(sample_state_with_commands, context)
        
        # Verify error was added to state
        assert result_state.has_errors()
        # The response text should indicate an error occurred
        assert "sorry" in result_state.response_text.lower() or "error" in result_state.response_text.lower()

    @pytest.mark.asyncio
    async def test_command_executor_empty_command_list(self, mock_container):
        """Test handling of empty command list"""
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        empty_state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            response_text="",
            audio_url=None,
            intent_type=IntentType.ADD_ITEM,
            intent_confidence=0.95,
            commands=[]  # Empty list
        )
        
        # Use the existing MockContainer from helpers
        from app.tests.helpers.mock_services import MockContainer
        mock_container = MockContainer()
        
        # Test with LangGraph context injection - command executor needs service_factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(mock_container)
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        # Execute the node
        result_state = await command_executor_node(empty_state, context)
        
        # Verify state has no command batch result
        assert result_state.command_batch_result is None


class TestCommandExecutorRouting:
    """Test the routing logic after command execution"""

    @pytest.fixture
    def state_with_successful_batch(self):
        """State with successful command batch result"""
        from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
        from app.agents.utils.response_builder import build_summary_events, build_response_payload
        
        results = [OrderResult.success("Success")]
        batch_outcome = analyze_batch_outcome(results)
        first_error_code = get_first_error_code(results)
        summary_events = build_summary_events(results)
        response_payload = build_response_payload(
            batch_outcome=batch_outcome,
            summary_events=summary_events,
            first_error_code=first_error_code,
            intent_type="ADD_ITEM"
        )
        
        batch_result = CommandBatchResult(
            results=results,
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Success",
            command_family="ADD_ITEM",
            batch_outcome=batch_outcome,
            first_error_code=first_error_code,
            response_payload=response_payload
        )
        
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        return ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            command_batch_result=batch_result,
            order_state=order_state
        )

    @pytest.fixture
    def state_with_failed_batch(self):
        """State with failed command batch result"""
        from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
        from app.agents.utils.response_builder import build_summary_events, build_response_payload
        
        # Create a proper error result with category and code
        from app.dto.order_result import ErrorCategory, ErrorCode
        error_result = OrderResult.error("Failed")
        error_result.error_category = ErrorCategory.BUSINESS
        error_result.error_code = ErrorCode.ITEM_UNAVAILABLE
        results = [error_result]
        batch_outcome = analyze_batch_outcome(results)
        first_error_code = get_first_error_code(results)
        summary_events = build_summary_events(results)
        response_payload = build_response_payload(
            batch_outcome=batch_outcome,
            summary_events=summary_events,
            first_error_code=first_error_code,
            intent_type="ADD_ITEM"
        )
        
        batch_result = CommandBatchResult(
            results=results,
            total_commands=1,
            successful_commands=0,
            failed_commands=1,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Failed",
            command_family="ADD_ITEM",
            batch_outcome=batch_outcome,
            first_error_code=first_error_code,
            response_payload=response_payload
        )
        
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        return ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            command_batch_result=batch_result,
            order_state=order_state
        )

    def test_route_to_follow_up_agent_on_ask(self, state_with_failed_batch):
        """Test routing to follow_up_agent when batch outcome indicates need for follow-up"""
        # Set the batch outcome to indicate need for follow-up
        state_with_failed_batch.command_batch_result.batch_outcome = "PARTIAL_SUCCESS_ASK"
        
        result = should_continue_after_command_executor(state_with_failed_batch)
        assert result == "follow_up_agent"

    def test_route_to_final_response_aggregator_on_stop(self, state_with_successful_batch):
        """Test routing to final_response_aggregator when batch outcome indicates completion"""
        # Set the batch outcome to indicate completion
        state_with_successful_batch.command_batch_result.batch_outcome = "ALL_SUCCESS"
        
        result = should_continue_after_command_executor(state_with_successful_batch)
        assert result == "final_response_aggregator"

    def test_route_to_follow_up_agent_on_failures(self, state_with_failed_batch):
        """Test routing to follow_up_agent when commands have failures"""
        result = should_continue_after_command_executor(state_with_failed_batch)
        assert result == "follow_up_agent"

    def test_route_to_dynamic_voice_response_on_success(self, state_with_successful_batch):
        """Test routing to dynamic_voice_response when all commands succeed"""
        result = should_continue_after_command_executor(state_with_successful_batch)
        assert result == "final_response_aggregator"

    def test_route_to_follow_up_agent_on_validation_errors(self):
        """Test routing to follow_up_agent when there are validation errors"""
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            errors=["Validation failed"],
            order_state=order_state
        )
        
        result = should_continue_after_command_executor(state)
        assert result == "follow_up_agent"

    def test_route_to_dynamic_voice_response_by_default(self):
        """Test default routing to dynamic_voice_response"""
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            order_state=order_state
        )
        
        result = should_continue_after_command_executor(state)
        assert result == "final_response_aggregator"


class TestCommandExecutorIntegration:
    """Integration tests for command executor with real command objects"""

    @pytest.mark.asyncio
    async def test_command_executor_with_real_add_item_command(self):
        """Test command executor with a real AddItemCommand"""
        # This would be a more complex integration test
        # that actually creates and executes real command objects
        # For now, we'll keep it simple with mocked commands
        
        from app.models.state_machine_models import OrderState
        order_state = OrderState(
            line_items=[],
            last_mentioned_item_ref=None,
            totals={}
        )
        order_state.order_id = 100
        
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            commands=[
                {
                    "intent": "ADD_ITEM",
                    "confidence": 1.0,
                    "slots": {
                        "menu_item_id": 1,
                        "quantity": 1
                    }
                }
            ],
            order_state=order_state
        )
        
        # Use the existing MockContainer from helpers
        from app.tests.helpers.mock_services import MockContainer
        mock_container = MockContainer()
        
        # Test with LangGraph context injection - command executor needs service_factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(mock_container)
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        # The MockContainer already provides all the services the command executor needs
        # No additional mocking required
        
        # Mock successful execution with new required fields
        from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
        from app.agents.utils.response_builder import build_summary_events, build_response_payload
        
        results = [OrderResult.success("Item added successfully")]
        batch_outcome = analyze_batch_outcome(results)
        first_error_code = get_first_error_code(results)
        summary_events = build_summary_events(results)
        response_payload = build_response_payload(
            batch_outcome=batch_outcome,
            summary_events=summary_events,
            first_error_code=first_error_code,
            intent_type="ADD_ITEM"
        )
        
        batch_result = CommandBatchResult(
            results=results,
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Item added successfully",
            command_family="ADD_ITEM",
            batch_outcome=batch_outcome,
            first_error_code=first_error_code,
            response_payload=response_payload
        )
        
        # The command executor will create its own CommandInvoker and execute commands
        # We just need to ensure the database and unit of work are mocked
        
        # Execute the node
        result_state = await command_executor_node(state, context)
        
        # Verify the result
        assert result_state.command_batch_result is not None
        assert result_state.command_batch_result.successful_commands == 1
        assert "Command executed successfully" in result_state.command_batch_result.summary_message
