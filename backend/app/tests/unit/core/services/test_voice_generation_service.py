"""
Unit tests for VoiceGenerationService
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.core.services.conversation.voice_generation_service import VoiceGenerationService
from app.constants.audio_phrases import AudioPhraseType


class TestVoiceGenerationService:
    """Test cases for VoiceGenerationService"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        factory = Mock()
        factory.create_voice_service.return_value = AsyncMock()
        return factory
    
    @pytest.fixture
    def service(self, mock_service_factory):
        """Create service with mocked dependencies"""
        return VoiceGenerationService(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_success(self, service, mocker):
        """Test successful voice generation"""
        # Mock the voice service
        mock_voice_service = service.service_factory.create_voice_service.return_value
        mock_voice_service.generate_audio.return_value = "http://example.com/audio.mp3"
        
        # Mock the audio phrase constants
        mock_constants = mocker.patch('app.core.services.conversation.voice_generation_service.AudioPhraseConstants')
        mock_constants.get_phrase_text.return_value = "Your order has been updated."
        
        # Test the service
        result = await service.generate_voice_response(
            response_text="Your order has been updated.",
            response_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            restaurant_id="1",
            custom_response_text=None,
            intent_confidence=0.9
        )
        
        # Verify result
        assert result["success"] is True
        assert result["response_text"] == "Your order has been updated."
        assert result["audio_url"] == "http://example.com/audio.mp3"
        
        # Verify voice service was called
        mock_voice_service.generate_audio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_low_confidence(self, service, mocker):
        """Test voice generation with low confidence (adds clarification request)"""
        # Mock the voice service
        mock_voice_service = service.service_factory.create_voice_service.return_value
        mock_voice_service.generate_audio.return_value = "http://example.com/audio.mp3"
        
        # Mock the audio phrase constants
        mock_constants = mocker.patch('app.core.services.conversation.voice_generation_service.AudioPhraseConstants')
        mock_constants.get_phrase_text.return_value = "Your order has been updated."
        
        # Test the service with low confidence
        result = await service.generate_voice_response(
            response_text="Your order has been updated.",
            response_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            restaurant_id="1",
            custom_response_text=None,
            intent_confidence=0.5  # Low confidence
        )
        
        # Verify result includes clarification request
        assert result["success"] is True
        assert "Could you please repeat that?" in result["response_text"]
        assert result["audio_url"] == "http://example.com/audio.mp3"
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_no_phrase_type(self, service):
        """Test voice generation with no phrase type"""
        # Test the service
        result = await service.generate_voice_response(
            response_text="Some response",
            response_phrase_type=None,
            restaurant_id="1",
            custom_response_text=None,
            intent_confidence=0.9
        )
        
        # Verify result
        assert result["success"] is False
        assert "trouble processing" in result["response_text"]
        assert result["audio_url"] is None
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_no_voice_service(self, service):
        """Test voice generation with no voice service available"""
        # Mock service factory to return None
        service.service_factory.create_voice_service.return_value = None
        
        # Test the service
        result = await service.generate_voice_response(
            response_text="Your order has been updated.",
            response_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            restaurant_id="1",
            custom_response_text=None,
            intent_confidence=0.9
        )
        
        # Verify result
        assert result["success"] is False
        assert "trouble with the audio system" in result["response_text"]
        assert result["audio_url"] is None
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_exception(self, service, mocker):
        """Test voice generation with exception"""
        # Mock the voice service to raise exception
        mock_voice_service = service.service_factory.create_voice_service.return_value
        mock_voice_service.generate_audio.side_effect = Exception("Voice service failed")
        
        # Test the service
        result = await service.generate_voice_response(
            response_text="Your order has been updated.",
            response_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            restaurant_id="1",
            custom_response_text=None,
            intent_confidence=0.9
        )
        
        # Verify result
        assert result["success"] is False
        assert "trouble processing" in result["response_text"]
        assert result["audio_url"] is None
    
    def test_should_continue_after_generation(self, service):
        """Test routing decision after voice generation"""
        generation_result = {"success": True}
        
        next_step = service.should_continue_after_generation(generation_result)
        assert next_step == "END"
