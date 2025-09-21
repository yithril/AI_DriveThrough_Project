"""
Unit tests for canned_response_node

Tests the canned response node which resolves AudioPhraseType to actual audio URLs
and handles fallback responses for low confidence intents.
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
from app.agents.nodes.canned_response import canned_response_node, should_continue_after_canned_response
from app.constants.audio_phrases import AudioPhraseType


class TestCannedResponseNode:
    """Test the canned_response_node functionality"""

    @pytest.fixture
    def mock_voice_service(self):
        """Mock voice service for canned phrase generation"""
        voice_service = AsyncMock()
        voice_service.get_canned_phrase.return_value = "https://s3.amazonaws.com/bucket/canned-phrase.mp3"
        return voice_service

    @pytest.fixture
    def sample_state_with_phrase_type(self):
        """Sample workflow state with response phrase type"""
        return ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="",
            audio_url=None,
            response_phrase_type=AudioPhraseType.GREETING,
            intent_confidence=0.95
        )

    @pytest.fixture
    def sample_state_low_confidence(self):
        """Sample workflow state with low confidence intent"""
        return ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="",
            audio_url=None,
            response_phrase_type=AudioPhraseType.CLARIFICATION_REQUEST,
            intent_confidence=0.4  # Low confidence
        )

    @pytest.mark.asyncio
    async def test_canned_response_successful_phrase_resolution(self, sample_state_with_phrase_type, mock_voice_service):
        """Test successful resolution of canned phrase to audio URL"""
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await canned_response_node(sample_state_with_phrase_type)
            
            # Verify audio URL was set
            assert result_state.audio_url == "https://s3.amazonaws.com/bucket/canned-phrase.mp3"
            
            # Verify response text was set from AudioPhraseConstants
            assert result_state.response_text is not None
            assert len(result_state.response_text) > 0
            
            # Verify voice service was called with correct parameters
            mock_voice_service.get_canned_phrase.assert_called_once_with(
                AudioPhraseType.GREETING,
                restaurant_id=1
            )

    @pytest.mark.asyncio
    async def test_canned_response_no_phrase_type(self, mock_voice_service):
        """Test handling when no phrase type is provided"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="",
            audio_url=None,
            response_phrase_type=None  # No phrase type
        )
        
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await canned_response_node(state)
            
            # Verify fallback response
            assert result_state.response_text == "I'm sorry, I had trouble processing your request. Please try again."
            assert result_state.audio_url is None
            
            # Verify voice service was not called
            mock_voice_service.get_canned_phrase.assert_not_called()

    @pytest.mark.asyncio
    async def test_canned_response_voice_service_failure(self, sample_state_with_phrase_type):
        """Test handling when voice service fails"""
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            
            # Mock voice service failure
            mock_voice_service = AsyncMock()
            mock_voice_service.get_canned_phrase.side_effect = Exception("Voice service failed")
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await canned_response_node(sample_state_with_phrase_type)
            
            # Verify fallback response
            assert result_state.response_text == "I'm sorry, I had trouble processing your request. Please try again."
            assert result_state.audio_url is None

    @pytest.mark.asyncio
    async def test_canned_response_low_confidence_clarification(self, sample_state_low_confidence, mock_voice_service):
        """Test handling of low confidence intents with clarification"""
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await canned_response_node(sample_state_low_confidence)
            
            # Verify clarification was added to response
            assert "Could you please repeat that?" in result_state.response_text or "I didn't quite catch that" in result_state.response_text
            
            # Verify audio URL was still set
            assert result_state.audio_url == "https://s3.amazonaws.com/bucket/canned-phrase.mp3"

    @pytest.mark.asyncio
    async def test_canned_response_container_failure(self, sample_state_with_phrase_type):
        """Test handling when container fails to provide voice service"""
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.side_effect = Exception("Container failed")
            
            # Execute the node
            result_state = await canned_response_node(sample_state_with_phrase_type)
            
            # Verify fallback response
            assert result_state.response_text == "I'm sorry, I had trouble processing your request. Please try again."
            assert result_state.audio_url is None

    @pytest.mark.asyncio
    async def test_canned_response_different_phrase_types(self, mock_voice_service):
        """Test different phrase types are handled correctly"""
        phrase_types_to_test = [
            AudioPhraseType.GREETING,
            AudioPhraseType.CONFIRMATION,
            AudioPhraseType.GOODBYE,
            AudioPhraseType.ERROR_MESSAGE
        ]
        
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            for phrase_type in phrase_types_to_test:
                state = ConversationWorkflowState(
                    session_id="test-session-123",
                    restaurant_id=1,
                    order_id=100,
                    response_text="",
                    audio_url=None,
                    response_phrase_type=phrase_type
                )
                
                # Execute the node
                result_state = await canned_response_node(state)
                
                # Verify audio URL was set
                assert result_state.audio_url == "https://s3.amazonaws.com/bucket/canned-phrase.mp3"
                
                # Verify response text was set
                assert result_state.response_text is not None
                assert len(result_state.response_text) > 0
                
                # Verify voice service was called with correct phrase type
                mock_voice_service.get_canned_phrase.assert_called_with(
                    phrase_type,
                    restaurant_id=1
                )


class TestCannedResponseRouting:
    """Test the routing logic after canned response"""

    def test_should_continue_after_canned_response_returns_end(self):
        """Test that canned response always routes to END"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="Hello!",
            audio_url="https://s3.amazonaws.com/bucket/hello.mp3"
        )
        
        result = should_continue_after_canned_response(state)
        assert result == "END"

    def test_should_continue_after_canned_response_with_errors(self):
        """Test routing with errors in state"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="Error occurred",
            audio_url=None,
            errors=["Some error"]
        )
        
        result = should_continue_after_canned_response(state)
        assert result == "END"  # Still goes to END even with errors


class TestCannedResponseIntegration:
    """Integration tests for canned response node"""

    @pytest.mark.asyncio
    async def test_canned_response_full_flow(self):
        """Test the complete canned response flow"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="",
            audio_url=None,
            response_phrase_type=AudioPhraseType.CONFIRMATION,
            intent_confidence=0.9
        )
        
        # Mock the voice service with realistic behavior
        with patch('app.agents.nodes.canned_response.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            
            mock_voice_service = AsyncMock()
            mock_voice_service.get_canned_phrase.return_value = "https://s3.amazonaws.com/bucket/confirmation.mp3"
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await canned_response_node(state)
            
            # Verify complete state
            assert result_state.audio_url == "https://s3.amazonaws.com/bucket/confirmation.mp3"
            assert result_state.response_text is not None
            assert len(result_state.response_text) > 0
            assert not result_state.has_errors()
            
            # Verify routing
            routing_result = should_continue_after_canned_response(result_state)
            assert routing_result == "END"
