"""
Test command executor enrichment functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.state import ConversationWorkflowState
from app.agents.nodes.command_executor import command_executor_node
from app.dto.order_result import OrderResult, CommandBatchResult, ResponsePayload
from app.commands.intent_classification_schema import IntentType


class TestCommandExecutorEnrichment:
    """Test that command executor enriches CommandBatchResult with router-friendly fields"""
    
    @pytest.fixture
    def sample_state(self):
        """Sample workflow state with commands"""
        return ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
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
            ]
        )
    
    @pytest.mark.asyncio
    async def test_command_executor_enriches_batch_result(self, sample_state):
        """Test that command executor enriches CommandBatchResult with router-friendly fields"""
        
        # Mock the command invoker to return a basic batch result
        mock_batch_result = CommandBatchResult(
            results=[
                OrderResult.success("Item added", data={"item_name": "burger", "qty": 1}),
                OrderResult.error("Item unavailable", error_category="BUSINESS", 
                                error_code="item_unavailable", data={"item_name": "foie gras"})
            ],
            total_commands=2,
            successful_commands=1,
            failed_commands=1,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Mixed results"
        )
        
        with patch('app.agents.nodes.command_executor.CommandInvoker') as mock_invoker_class:
            mock_invoker = AsyncMock()
            mock_invoker.execute_multiple_commands.return_value = mock_batch_result
            mock_invoker_class.return_value = mock_invoker
            
            # Mock the container and services
            with patch('app.agents.nodes.command_executor.Container') as mock_container_class:
                mock_container = MagicMock()
                mock_container.order_service.return_value = MagicMock()
                mock_container.order_session_service.return_value = MagicMock()
                mock_container.customization_validator.return_value = MagicMock()
                mock_container_class.return_value = mock_container
                
                # Mock database session
                with patch('app.agents.nodes.command_executor.get_db') as mock_get_db:
                    mock_session = MagicMock()
                    mock_get_db.return_value = [mock_session]
                    
                    # Mock UnitOfWork
                    with patch('app.agents.nodes.command_executor.UnitOfWork') as mock_uow_class:
                        mock_uow = MagicMock()
                        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
                        mock_uow.__aexit__ = AsyncMock(return_value=None)
                        mock_uow_class.return_value = mock_uow
                        
                        # Execute the command executor
                        result_state = await command_executor_node(sample_state)
                        
                        # Verify the batch result was enriched
                        assert result_state.command_batch_result is not None
                        batch_result = result_state.command_batch_result
                        
                        # Check that router-friendly fields were added
                        assert hasattr(batch_result, 'batch_outcome')
                        assert hasattr(batch_result, 'first_error_code')
                        assert hasattr(batch_result, 'response_payload')
                        
                        # Verify the enrichment worked
                        assert batch_result.batch_outcome == "PARTIAL_SUCCESS_ASK"
                        assert batch_result.first_error_code == "item_unavailable"
                        assert isinstance(batch_result.response_payload, ResponsePayload)
                        
                        # Check response payload content
                        payload = batch_result.response_payload
                        assert payload.enum_key == "ADD_ITEM_PARTIAL_SUCCESS_ASK"
                        assert "successful_items" in payload.args
                        assert "failed_items" in payload.args
                        assert payload.args["first_error_code"] == "item_unavailable"
