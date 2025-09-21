"""
Unit tests for dynamic_voice_response_node

Tests the dynamic voice response node which converts text responses to audio using TTS service.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.nodes.dynamic_voice_response import dynamic_voice_response_node, should_continue_after_dynamic_voice_response
from .test_helpers import ConversationWorkflowStateBuilder, create_test_state


class TestDynamicVoiceResponseNode:
    """Test the dynamic_voice_response_node functionality"""

    @pytest.fixture
    def mock_voice_service(self):
        """Mock voice service for TTS generation"""
        voice_service = AsyncMock()
        voice_service.generate_voice.return_value = "https://s3.amazonaws.com/bucket/dynamic-tts.mp3"
        return voice_service

    @pytest.fixture
    def sample_state_with_text(self):
        """Sample workflow state with response text"""
        return (ConversationWorkflowStateBuilder()
                .with_response("Your order has been confirmed. Total is $12.99")
                .build())

    @pytest.fixture
    def sample_state_empty_text(self):
        """Sample workflow state with empty response text"""
        return (ConversationWorkflowStateBuilder()
                .with_response("")  # Empty text
                .build())

    @pytest.fixture
    def sample_state_whitespace_text(self):
        """Sample workflow state with whitespace-only response text"""
        return (ConversationWorkflowStateBuilder()
                .with_response("   \n\t  ")  # Whitespace only
                .build())

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_successful_generation(self, sample_state_with_text, mock_voice_service):
        """Test successful voice generation from text"""
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(sample_state_with_text)
            
            # Verify audio URL was set
            assert result_state.audio_url == "https://s3.amazonaws.com/bucket/dynamic-tts.mp3"
            
            # Verify response text was unchanged
            assert result_state.response_text == "Your order has been confirmed. Total is $12.99"
            
            # Verify voice service was called with correct parameters
            mock_voice_service.generate_voice.assert_called_once_with(
                text="Your order has been confirmed. Total is $12.99",
                voice="nova",
                language="english",
                restaurant_id=1  # Converted from string to int
            )

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_empty_text(self, sample_state_empty_text, mock_voice_service):
        """Test handling of empty response text"""
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(sample_state_empty_text)
            
            # Verify audio URL was set to None
            assert result_state.audio_url is None
            
            # Verify voice service was not called
            mock_voice_service.generate_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_whitespace_text(self, sample_state_whitespace_text, mock_voice_service):
        """Test handling of whitespace-only response text"""
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(sample_state_whitespace_text)
            
            # Verify audio URL was set to None
            assert result_state.audio_url is None
            
            # Verify voice service was not called
            mock_voice_service.generate_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_voice_service_failure(self, sample_state_with_text):
        """Test handling when voice service fails"""
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            
            # Mock voice service failure
            mock_voice_service = AsyncMock()
            mock_voice_service.generate_voice.side_effect = Exception("TTS service failed")
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(sample_state_with_text)
            
            # Verify error was added to state
            assert result_state.has_errors()
            assert "Voice generation failed" in str(result_state.errors)
            
            # Verify audio URL was set to None
            assert result_state.audio_url is None

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_container_failure(self, sample_state_with_text):
        """Test handling when container fails to provide voice service"""
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.side_effect = Exception("Container failed")
            
            # Execute the node
            result_state = await dynamic_voice_response_node(sample_state_with_text)
            
            # Verify error was added to state
            assert result_state.has_errors()
            assert "Voice generation failed" in str(result_state.errors)
            
            # Verify audio URL was set to None
            assert result_state.audio_url is None

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_voice_service_returns_none(self, sample_state_with_text):
        """Test handling when voice service returns None"""
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            
            # Mock voice service returning None
            mock_voice_service = AsyncMock()
            mock_voice_service.generate_voice.return_value = None
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(sample_state_with_text)
            
            # Verify error was added to state
            assert result_state.has_errors()
            assert "Voice generation failed - no audio URL returned" in str(result_state.errors)
            
            # Verify audio URL was set to None
            assert result_state.audio_url is None

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_different_restaurant_ids(self, mock_voice_service):
        """Test voice generation with different restaurant IDs for multitenancy"""
        restaurant_ids = [1, 2, 3, 100]
        
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            for restaurant_id in restaurant_ids:
                state = ConversationWorkflowState(
                    session_id="test-session-123",
                    restaurant_id=restaurant_id,
                    order_id=100,
                    response_text="Test response",
                    audio_url=None
                )
                
                # Execute the node
                result_state = await dynamic_voice_response_node(state)
                
                # Verify audio URL was set
                assert result_state.audio_url == "https://s3.amazonaws.com/bucket/dynamic-tts.mp3"
                
                # Verify voice service was called with correct restaurant_id
                mock_voice_service.generate_voice.assert_called_with(
                    text="Test response",
                    voice="nova",
                    language="english",
                    restaurant_id=restaurant_id
                )

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_long_text(self, mock_voice_service):
        """Test voice generation with long text responses"""
        long_text = "This is a very long response that might be generated by the AI agent when providing detailed information about menu items, prices, and order confirmations. It should still work correctly with the TTS service."
        
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text=long_text,
            audio_url=None
        )
        
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(state)
            
            # Verify audio URL was set
            assert result_state.audio_url == "https://s3.amazonaws.com/bucket/dynamic-tts.mp3"
            
            # Verify voice service was called with the long text
            mock_voice_service.generate_voice.assert_called_once_with(
                text=long_text,
                voice="nova",
                language="english",
                restaurant_id=1
            )


class TestDynamicVoiceResponseRouting:
    """Test the routing logic after dynamic voice response"""

    def test_should_continue_after_dynamic_voice_response_returns_end(self):
        """Test that dynamic voice response always routes to END"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="Your order is ready",
            audio_url="https://s3.amazonaws.com/bucket/order-ready.mp3"
        )
        
        result = should_continue_after_dynamic_voice_response(state)
        assert result == "END"

    def test_should_continue_after_dynamic_voice_response_with_errors(self):
        """Test routing with errors in state"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="Error occurred",
            audio_url=None,
            errors=["Voice generation failed"]
        )
        
        result = should_continue_after_dynamic_voice_response(state)
        assert result == "END"  # Still goes to END even with errors


class TestDynamicVoiceResponseIntegration:
    """Integration tests for dynamic voice response node"""

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_full_flow(self):
        """Test the complete dynamic voice response flow"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="I've added a Big Mac to your order. Anything else?",
            audio_url=None,
            intent_confidence=0.9
        )
        
        # Mock the voice service with realistic behavior
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            
            mock_voice_service = AsyncMock()
            mock_voice_service.generate_voice.return_value = "https://s3.amazonaws.com/bucket/order-update.mp3"
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node
            result_state = await dynamic_voice_response_node(state)
            
            # Verify complete state
            assert result_state.audio_url == "https://s3.amazonaws.com/bucket/order-update.mp3"
            assert result_state.response_text == "I've added a Big Mac to your order. Anything else?"
            assert not result_state.has_errors()
            
            # Verify routing
            routing_result = should_continue_after_dynamic_voice_response(result_state)
            assert routing_result == "END"

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_caching_behavior(self):
        """Test that voice generation respects caching (via voice service)"""
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            order_id=100,
            response_text="Cached response",
            audio_url=None
        )
        
        with patch('app.core.container.Container') as mock_container_class:
            mock_container = mock_container_class.return_value
            
            mock_voice_service = AsyncMock()
            mock_voice_service.generate_voice.return_value = "https://s3.amazonaws.com/bucket/cached-response.mp3"
            mock_container.voice_service.return_value = mock_voice_service
            
            # Execute the node twice with same text
            result_state1 = await dynamic_voice_response_node(state)
            result_state2 = await dynamic_voice_response_node(state)
            
            # Verify both calls succeeded
            assert result_state1.audio_url == "https://s3.amazonaws.com/bucket/cached-response.mp3"
            assert result_state2.audio_url == "https://s3.amazonaws.com/bucket/cached-response.mp3"
            
            # Verify voice service was called twice (caching is handled by voice service)
            assert mock_voice_service.generate_voice.call_count == 2
