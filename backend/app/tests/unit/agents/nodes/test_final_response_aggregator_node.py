"""
Unit tests for Final Response Aggregator Node

Tests the Final Response Aggregator's ability to handle different combinations
of command results and generate appropriate responses.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.nodes.final_response_aggregator_node import (
    _needs_clarification,
    _build_final_response,
    _wants_to_finish_order,
    should_continue_after_final_response_aggregator
)
from app.agents.state import ConversationWorkflowState
from app.dto.order_result import CommandBatchResult
from app.agents.agent_response import ClarificationResponse
from app.constants.audio_phrases import AudioPhraseType
from app.tests.unit.workflow.test_helpers import (
    ConversationWorkflowStateBuilder,
    create_successful_command_batch_result,
    create_failed_command_batch_result
)


class TestHelperFunctions:
    """Test the helper functions used by the aggregator"""

    def test_needs_clarification_true(self):
        """Test _needs_clarification returns True when clarification is needed"""
        # Mock batch result with clarification needed
        mock_batch_result = MagicMock()
        mock_batch_result.results = [
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "clarification_needed",
                    "clarification_type": "ambiguous_item"
                }
            )
        ]
        
        result = _needs_clarification(mock_batch_result)
        assert result is True

    def test_needs_clarification_false(self):
        """Test _needs_clarification returns False when no clarification needed"""
        # Mock batch result without clarification needed
        mock_batch_result = MagicMock()
        mock_batch_result.results = [
            MagicMock(
                is_success=True, 
                data={"response_type": "item_added"}
            )
        ]
        
        result = _needs_clarification(mock_batch_result)
        assert result is False

    def test_build_final_response_success_only(self):
        """Test _build_final_response with success only"""
        # Mock batch result with success
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 1
        mock_batch_result.results = [
            MagicMock(is_success=True, data={"response_type": "item_added"})
        ]
        
        result = _build_final_response(mock_batch_result, None)
        assert result == "Your order has been updated."

    def test_build_final_response_unavailable_only(self):
        """Test _build_final_response with unavailable items only"""
        # Mock batch result with unavailable items
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 0
        mock_batch_result.results = [
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "pheasant"
                }
            )
        ]
        
        result = _build_final_response(mock_batch_result, None)
        assert result == "Sorry, we don't have pheasant."

    def test_build_final_response_multiple_unavailable_items(self):
        """Test _build_final_response with multiple unavailable items"""
        # Mock batch result with multiple unavailable items
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 0
        mock_batch_result.results = [
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "pheasant"
                }
            ),
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "unicorn burger"
                }
            )
        ]
        
        result = _build_final_response(mock_batch_result, None)
        assert result == "Sorry, we don't have pheasant and unicorn burger."

    def test_build_final_response_with_clarification(self):
        """Test _build_final_response with clarification"""
        # Mock batch result
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 0
        mock_batch_result.results = []
        
        # Mock clarification response
        mock_clarification_response = ClarificationResponse(
            response_type="question",
            phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
            response_text="Which fries would you like?",
            confidence=0.9
        )
        
        result = _build_final_response(mock_batch_result, mock_clarification_response)
        assert result == "Which fries would you like?"

    def test_build_final_response_mixed_scenario(self):
        """Test _build_final_response with mixed scenario: success + unavailable + clarification"""
        # Mock batch result with mixed results
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 1
        mock_batch_result.results = [
            # Successful item
            MagicMock(is_success=True, data={"response_type": "item_added"}),
            # Unavailable item
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "pheasant"
                }
            )
        ]
        
        # Mock clarification response
        mock_clarification_response = ClarificationResponse(
            response_type="question",
            phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
            response_text="Which fries would you like?",
            confidence=0.9
        )
        
        result = _build_final_response(mock_batch_result, mock_clarification_response)
        expected = "Your order has been updated. Sorry, we don't have pheasant. Which fries would you like?"
        assert result == expected

    def test_wants_to_finish_order_true(self):
        """Test _wants_to_finish_order returns True when order should be finished"""
        # Mock batch result with successful commands and no clarifications
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 2
        mock_batch_result.failed_commands = 0
        mock_batch_result.results = [
            MagicMock(is_success=True, data={"response_type": "item_added"}),
            MagicMock(is_success=True, data={"response_type": "item_added"})
        ]
        
        # Mock _needs_clarification to return False
        with patch('app.agents.nodes.final_response_aggregator_node._needs_clarification', return_value=False):
            result = _wants_to_finish_order(mock_batch_result)
            assert result is True

    def test_wants_to_finish_order_false(self):
        """Test _wants_to_finish_order returns False when order shouldn't be finished"""
        # Mock batch result with failed commands
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 0
        mock_batch_result.failed_commands = 1
        mock_batch_result.results = [
            MagicMock(is_success=False, data={"response_type": "error"})
        ]
        
        result = _wants_to_finish_order(mock_batch_result)
        assert result is False

    def test_should_continue_after_final_response_aggregator(self):
        """Test should_continue_after_final_response_aggregator always returns voice_generation"""
        state = (ConversationWorkflowStateBuilder()
                .build())
        
        result = should_continue_after_final_response_aggregator(state)
        assert result == "voice_generation"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_build_final_response_empty_response(self):
        """Test _build_final_response handles empty response gracefully"""
        # Mock batch result with no meaningful data
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 0
        mock_batch_result.results = []
        
        result = _build_final_response(mock_batch_result, None)
        assert "I'm sorry, I didn't understand" in result

    def test_build_final_response_many_unavailable_items(self):
        """Test _build_final_response with many unavailable items"""
        # Mock batch result with many unavailable items
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 0
        mock_batch_result.results = [
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "pheasant"
                }
            ),
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "unicorn burger"
                }
            ),
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "item_unavailable",
                    "requested_item": "dragon wings"
                }
            )
        ]
        
        result = _build_final_response(mock_batch_result, None)
        assert "pheasant, unicorn burger and dragon wings" in result

    def test_needs_clarification_with_ambiguous_item(self):
        """Test _needs_clarification detects ambiguous items"""
        # Mock batch result with ambiguous item
        mock_batch_result = MagicMock()
        mock_batch_result.results = [
            MagicMock(
                is_success=True, 
                data={
                    "response_type": "clarification_needed",
                    "clarification_type": "ambiguous_item",
                    "ambiguous_item": "fries"
                }
            )
        ]
        
        result = _needs_clarification(mock_batch_result)
        assert result is True

    def test_build_final_response_success_only(self):
        """Test _build_final_response with success only (no completion question)"""
        # Mock batch result with successful commands
        mock_batch_result = MagicMock()
        mock_batch_result.successful_commands = 2
        mock_batch_result.failed_commands = 0
        mock_batch_result.results = [
            MagicMock(is_success=True, data={"response_type": "item_added"}),
            MagicMock(is_success=True, data={"response_type": "item_added"})
        ]
        
        result = _build_final_response(mock_batch_result, None)
        assert result == "Your order has been updated."