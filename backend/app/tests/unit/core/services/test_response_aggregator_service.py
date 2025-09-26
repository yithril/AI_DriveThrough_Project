"""
Unit tests for ResponseAggregatorService
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.core.services.conversation.response_aggregator_service import ResponseAggregatorService
from app.dto.order_result import CommandBatchResult, OrderResult
from app.constants.audio_phrases import AudioPhraseType


class TestResponseAggregatorService:
    """Test cases for ResponseAggregatorService"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_service_factory):
        """Create service with mocked dependencies"""
        return ResponseAggregatorService(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_aggregate_response_success(self, service, mocker):
        """Test successful response aggregation"""
        # Mock command batch result
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.successful_commands = 1
        mock_batch_result.failed_commands = 0
        mock_batch_result.results = [
            Mock(is_success=True, data={"response_type": "item_added"})
        ]
        
        # Test the service
        result = await service.aggregate_response(
            command_batch_result=mock_batch_result,
            session_id="test-session",
            restaurant_id="1",
            conversation_history=[],
            order_state={}
        )
        
        # Verify result
        assert result["success"] is True
        assert "order has been updated" in result["response_text"]
    
    @pytest.mark.asyncio
    async def test_aggregate_response_no_batch_result(self, service):
        """Test response aggregation with no batch result"""
        # Test the service
        result = await service.aggregate_response(
            command_batch_result=None,
            session_id="test-session",
            restaurant_id="1",
            conversation_history=[],
            order_state={}
        )
        
        # Verify result
        assert result["success"] is False
        assert "didn't understand" in result["response_text"]
    
    @pytest.mark.asyncio
    async def test_aggregate_response_with_unavailable_items(self, service):
        """Test response aggregation with unavailable items"""
        # Mock command batch result with unavailable items
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.successful_commands = 1
        mock_batch_result.failed_commands = 0
        mock_batch_result.results = [
            Mock(is_success=True, data={
                "response_type": "item_added"
            }),
            Mock(is_success=True, data={
                "response_type": "item_unavailable",
                "requested_item": "unicorn burger"
            })
        ]
        
        # Test the service
        result = await service.aggregate_response(
            command_batch_result=mock_batch_result,
            session_id="test-session",
            restaurant_id="1",
            conversation_history=[],
            order_state={}
        )
        
        # Verify result
        assert result["success"] is True
        assert "order has been updated" in result["response_text"]
        assert "don't have unicorn burger" in result["response_text"]
    
    @pytest.mark.asyncio
    async def test_aggregate_response_with_clarification(self, service, mocker):
        """Test response aggregation with clarification needed"""
        # Mock command batch result with clarification
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.successful_commands = 1
        mock_batch_result.failed_commands = 0
        mock_batch_result.results = [
            Mock(is_success=True, data={
                "response_type": "clarification_needed"
            })
        ]
        
        # Mock clarification agent service
        mock_clarification = mocker.patch('app.core.services.conversation.response_aggregator_service.clarification_agent_service')
        mock_clarification.return_value = Mock(
            response_text="Which size would you like?"
        )
        
        # Test the service
        result = await service.aggregate_response(
            command_batch_result=mock_batch_result,
            session_id="test-session",
            restaurant_id="1",
            conversation_history=[],
            order_state={}
        )
        
        # Verify result
        assert result["success"] is True
        assert "order has been updated" in result["response_text"]
        assert "Which size would you like?" in result["response_text"]
    
    @pytest.mark.asyncio
    async def test_aggregate_response_exception(self, service, mocker):
        """Test response aggregation with exception"""
        # Mock command batch result
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.successful_commands = 1
        mock_batch_result.failed_commands = 0
        mock_batch_result.results = []
        
        # Mock clarification agent to raise exception
        mock_clarification = mocker.patch('app.core.services.conversation.response_aggregator_service.clarification_agent_service')
        mock_clarification.side_effect = Exception("Clarification failed")
        
        # Test the service
        result = await service.aggregate_response(
            command_batch_result=mock_batch_result,
            session_id="test-session",
            restaurant_id="1",
            conversation_history=[],
            order_state={}
        )
        
        # Verify result
        assert result["success"] is True  # The service handles exceptions gracefully
        assert "order has been updated" in result["response_text"]
    
    def test_needs_clarification_true(self, service):
        """Test clarification detection"""
        # Mock command batch result with clarification
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.results = [
            Mock(is_success=True, data={
                "response_type": "clarification_needed"
            })
        ]
        
        needs_clarification = service._needs_clarification(mock_batch_result)
        assert needs_clarification is True
    
    def test_needs_clarification_false(self, service):
        """Test no clarification needed"""
        # Mock command batch result without clarification
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.results = [
            Mock(is_success=True, data={
                "response_type": "item_added"
            })
        ]
        
        needs_clarification = service._needs_clarification(mock_batch_result)
        assert needs_clarification is False
    
    def test_wants_to_finish_order_true(self, service):
        """Test order completion detection"""
        # Mock command batch result with order confirmation
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.results = [
            Mock(is_success=True, data={
                "response_type": "order_confirmed"
            })
        ]
        
        wants_to_finish = service._wants_to_finish_order(mock_batch_result)
        assert wants_to_finish is True
    
    def test_determine_phrase_type_item_unavailable(self, service):
        """Test phrase type determination for unavailable items"""
        # Mock command batch result with unavailable item
        mock_batch_result = Mock(spec=CommandBatchResult)
        mock_batch_result.results = [
            Mock(is_success=True, data={
                "response_type": "item_unavailable"
            })
        ]
        
        phrase_type = service._determine_phrase_type(mock_batch_result)
        assert phrase_type == AudioPhraseType.ITEM_UNAVAILABLE
