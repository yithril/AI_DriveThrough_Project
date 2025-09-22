"""
Unit tests for VoiceService unified audio generation API
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.voice_service import VoiceService
from app.constants.audio_phrases import AudioPhraseType, AudioPhraseConstants


class TestVoiceServiceUnifiedAPI:
    """Test the unified generate_audio method"""
    
    @pytest.fixture
    def voice_service(self):
        """Create a VoiceService instance for testing"""
        # Mock the required services
        mock_tts = AsyncMock()
        mock_stt = AsyncMock()
        mock_storage = AsyncMock()
        mock_redis = AsyncMock()
        
        return VoiceService(
            text_to_speech_service=mock_tts,
            speech_to_text_service=mock_stt,
            file_storage_service=mock_storage,
            redis_service=mock_redis
        )
    
    @pytest.fixture
    def mock_s3_service(self):
        """Mock S3 service"""
        mock_s3 = AsyncMock()
        mock_s3.upload_file.return_value = "https://s3.amazonaws.com/bucket/audio.mp3"
        return mock_s3
    
    @pytest.fixture
    def mock_tts_service(self):
        """Mock TTS service"""
        mock_tts = AsyncMock()
        mock_tts.generate_voice.return_value = "https://s3.amazonaws.com/bucket/tts.mp3"
        return mock_tts
    
    @pytest.mark.asyncio
    async def test_generate_audio_canned_phrase_success(self, voice_service, mock_s3_service, mock_tts_service):
        """Test generate_audio with canned phrase (no custom text)"""
        # Mock the dependencies
        with patch.object(voice_service, 'file_storage_service', mock_s3_service), \
             patch.object(voice_service, 'text_to_speech_service', mock_tts_service), \
             patch.object(voice_service, 'get_canned_phrase', return_value="https://s3.amazonaws.com/bucket/canned.mp3") as mock_get_canned:
            
            # Test canned phrase
            result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                restaurant_id=1
            )
            
            # Should use canned phrase
            mock_get_canned.assert_called_once_with(AudioPhraseType.ITEM_ADDED_SUCCESS, 1, None)
            assert result == "https://s3.amazonaws.com/bucket/canned.mp3"
    
    @pytest.mark.asyncio
    async def test_generate_audio_dynamic_phrase_with_custom_text(self, voice_service, mock_s3_service, mock_tts_service):
        """Test generate_audio with dynamic phrase and custom text"""
        # Mock the dependencies
        with patch.object(voice_service, 'file_storage_service', mock_s3_service), \
             patch.object(voice_service, 'text_to_speech_service', mock_tts_service), \
             patch.object(voice_service, '_generate_tts', return_value="https://s3.amazonaws.com/bucket/tts.mp3") as mock_generate_tts:
            
            # Test dynamic phrase with custom text
            result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.LLM_GENERATED,
                restaurant_id=1,
                custom_text="What size would you like?"
            )
            
            # Should use TTS with custom text
            mock_generate_tts.assert_called_once_with("What size would you like?", 1)
            assert result == "https://s3.amazonaws.com/bucket/tts.mp3"
    
    @pytest.mark.asyncio
    async def test_generate_audio_dynamic_phrase_without_custom_text(self, voice_service, mock_s3_service, mock_tts_service):
        """Test generate_audio with dynamic phrase but no custom text (uses fallback)"""
        # Mock the dependencies
        with patch.object(voice_service, 'file_storage_service', mock_s3_service), \
             patch.object(voice_service, 'text_to_speech_service', mock_tts_service), \
             patch.object(voice_service, '_generate_tts', return_value="https://s3.amazonaws.com/bucket/tts.mp3") as mock_generate_tts:
            
            # Test dynamic phrase without custom text
            result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
                restaurant_id=1
            )
            
            # Should use TTS with fallback text
            expected_text = AudioPhraseConstants.get_phrase_text(AudioPhraseType.CLARIFICATION_QUESTION, None)
            mock_generate_tts.assert_called_once_with(expected_text, 1)
            assert result == "https://s3.amazonaws.com/bucket/tts.mp3"
    
    @pytest.mark.asyncio
    async def test_generate_audio_canned_phrase_with_custom_text(self, voice_service, mock_s3_service, mock_tts_service):
        """Test generate_audio with canned phrase but custom text provided (should use TTS)"""
        # Mock the dependencies
        with patch.object(voice_service, 'file_storage_service', mock_s3_service), \
             patch.object(voice_service, 'text_to_speech_service', mock_tts_service), \
             patch.object(voice_service, '_generate_tts', return_value="https://s3.amazonaws.com/bucket/tts.mp3") as mock_generate_tts:
            
            # Test canned phrase with custom text (should use TTS)
            result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                restaurant_id=1,
                custom_text="Custom message"
            )
            
            # Should use TTS with custom text, not canned
            mock_generate_tts.assert_called_once_with("Custom message", 1)
            assert result == "https://s3.amazonaws.com/bucket/tts.mp3"
    
    @pytest.mark.asyncio
    async def test_generate_audio_error_handling(self, voice_service):
        """Test generate_audio error handling"""
        # Mock an exception
        with patch.object(voice_service, '_is_canned_phrase', side_effect=Exception("Test error")):
            result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                restaurant_id=1
            )
            
            # Should return None on error
            assert result is None


class TestVoiceServiceCannedPhraseDetection:
    """Test the _is_canned_phrase method"""
    
    @pytest.fixture
    def voice_service(self):
        """Create a VoiceService instance for testing"""
        # Mock the required services
        mock_tts = AsyncMock()
        mock_stt = AsyncMock()
        mock_storage = AsyncMock()
        mock_redis = AsyncMock()
        
        return VoiceService(
            text_to_speech_service=mock_tts,
            speech_to_text_service=mock_stt,
            file_storage_service=mock_storage,
            redis_service=mock_redis
        )
    
    def test_is_canned_phrase_canned_phrases(self, voice_service):
        """Test that canned phrases return True"""
        # Test various canned phrases
        assert voice_service._is_canned_phrase(AudioPhraseType.GREETING) == True
        assert voice_service._is_canned_phrase(AudioPhraseType.THANK_YOU) == True
        assert voice_service._is_canned_phrase(AudioPhraseType.ITEM_ADDED_SUCCESS) == True
        assert voice_service._is_canned_phrase(AudioPhraseType.ORDER_CONFIRM) == True
        assert voice_service._is_canned_phrase(AudioPhraseType.COME_AGAIN) == True
    
    def test_is_canned_phrase_dynamic_phrases(self, voice_service):
        """Test that dynamic phrases return False"""
        # Test various dynamic phrases
        assert voice_service._is_canned_phrase(AudioPhraseType.CUSTOM_RESPONSE) == False
        assert voice_service._is_canned_phrase(AudioPhraseType.CLARIFICATION_QUESTION) == False
        assert voice_service._is_canned_phrase(AudioPhraseType.ERROR_MESSAGE) == False
        assert voice_service._is_canned_phrase(AudioPhraseType.LLM_GENERATED) == False


class TestVoiceServiceTTSGeneration:
    """Test the _generate_tts method"""
    
    @pytest.fixture
    def voice_service(self):
        """Create a VoiceService instance for testing"""
        # Mock the required services
        mock_tts = AsyncMock()
        mock_stt = AsyncMock()
        mock_storage = AsyncMock()
        mock_redis = AsyncMock()
        
        return VoiceService(
            text_to_speech_service=mock_tts,
            speech_to_text_service=mock_stt,
            file_storage_service=mock_storage,
            redis_service=mock_redis
        )
    
    @pytest.fixture
    def mock_tts_service(self):
        """Mock TTS service"""
        mock_tts = AsyncMock()
        mock_tts.generate_voice.return_value = "https://s3.amazonaws.com/bucket/tts.mp3"
        return mock_tts
    
    @pytest.mark.asyncio
    async def test_generate_tts_success(self, voice_service, mock_tts_service):
        """Test successful TTS generation"""
        # Patch the generate_voice method directly
        with patch.object(voice_service, 'generate_voice', return_value="https://s3.amazonaws.com/bucket/tts.mp3") as mock_generate_voice:
            result = await voice_service._generate_tts("Test text", 1)
            
            # Should call generate_voice with correct parameters
            mock_generate_voice.assert_called_once_with(
                text="Test text",
                voice=AudioPhraseConstants.STANDARD_VOICE,
                language="english",
                restaurant_id=1
            )
            assert result == "https://s3.amazonaws.com/bucket/tts.mp3"
    
    @pytest.mark.asyncio
    async def test_generate_tts_error_handling(self, voice_service):
        """Test TTS generation error handling"""
        # Mock generate_voice to raise exception
        with patch.object(voice_service, 'generate_voice', side_effect=Exception("TTS error")):
            result = await voice_service._generate_tts("Test text", 1)
            
            # Should return None on error
            assert result is None


class TestVoiceServiceIntegration:
    """Integration tests for the unified API"""
    
    @pytest.fixture
    def voice_service(self):
        """Create a VoiceService instance for testing"""
        # Mock the required services
        mock_tts = AsyncMock()
        mock_stt = AsyncMock()
        mock_storage = AsyncMock()
        mock_redis = AsyncMock()
        
        return VoiceService(
            text_to_speech_service=mock_tts,
            speech_to_text_service=mock_stt,
            file_storage_service=mock_storage,
            redis_service=mock_redis
        )
    
    @pytest.mark.asyncio
    async def test_canned_vs_dynamic_routing(self, voice_service):
        """Test that the service correctly routes canned vs dynamic phrases"""
        # Mock all dependencies
        mock_s3 = AsyncMock()
        mock_tts = AsyncMock()
        mock_tts.generate_voice.return_value = "https://s3.amazonaws.com/bucket/tts.mp3"
        
        with patch.object(voice_service, 'file_storage_service', mock_s3), \
             patch.object(voice_service, 'text_to_speech_service', mock_tts), \
             patch.object(voice_service, 'get_canned_phrase', return_value="https://s3.amazonaws.com/bucket/canned.mp3") as mock_get_canned, \
             patch.object(voice_service, '_generate_tts', return_value="https://s3.amazonaws.com/bucket/tts.mp3") as mock_generate_tts:
            
            # Test canned phrase
            canned_result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                restaurant_id=1
            )
            assert canned_result == "https://s3.amazonaws.com/bucket/canned.mp3"
            mock_get_canned.assert_called_once()
            mock_generate_tts.assert_not_called()
            
            # Reset mocks
            mock_get_canned.reset_mock()
            mock_generate_tts.reset_mock()
            
            # Test dynamic phrase
            dynamic_result = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.LLM_GENERATED,
                restaurant_id=1,
                custom_text="Dynamic response"
            )
            assert dynamic_result == "https://s3.amazonaws.com/bucket/tts.mp3"
            mock_generate_tts.assert_called_once()
            mock_get_canned.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_restaurant_name_parameter(self, voice_service):
        """Test that restaurant_name parameter is passed correctly"""
        mock_s3 = AsyncMock()
        mock_tts = AsyncMock()
        
        with patch.object(voice_service, 'file_storage_service', mock_s3), \
             patch.object(voice_service, 'text_to_speech_service', mock_tts), \
             patch.object(voice_service, 'get_canned_phrase', return_value="https://s3.amazonaws.com/bucket/canned.mp3") as mock_get_canned:
            
            # Test with restaurant_name
            await voice_service.generate_audio(
                phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                restaurant_id=1,
                restaurant_name="Test Restaurant"
            )
            
            # Should pass restaurant_name to get_canned_phrase
            mock_get_canned.assert_called_once_with(
                AudioPhraseType.ITEM_ADDED_SUCCESS, 
                1, 
                "Test Restaurant"
            )
