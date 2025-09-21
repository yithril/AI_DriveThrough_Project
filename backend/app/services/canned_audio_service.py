"""
Service for managing canned audio phrases stored in blob storage
"""
import logging
from typing import Optional, Dict, Any
from io import BytesIO

from ..constants.audio_phrases import AudioPhraseType, AudioPhraseConstants
from .file_storage_service import FileStorageService
from .text_to_speech_service import TextToSpeechService

logger = logging.getLogger(__name__)


class CannedAudioService:
    """Service for managing pre-generated audio phrases"""
    
    def __init__(self, file_storage: FileStorageService, tts_service: TextToSpeechService):
        self.file_storage = file_storage
        self.tts_service = tts_service
    
    async def get_canned_audio_url(self, phrase_type: AudioPhraseType, restaurant_slug: str) -> Optional[str]:
        """
        Get the URL for a canned audio phrase
        
        Args:
            phrase_type: Type of phrase to retrieve
            restaurant_slug: Restaurant identifier for customization
            
        Returns:
            URL to the audio file, or None if not found
        """
        try:
            blob_path = AudioPhraseConstants.get_blob_path(phrase_type, restaurant_slug)
            result = await self.file_storage.get_file(blob_path)
            
            if result.success and result.data:
                # Extract URL from the result data
                url = result.data.get('url') or result.data.get('s3_url')
                if url:
                    logger.info(f"Found canned audio for {phrase_type.value} at {url}")
                    return url
                else:
                    logger.warning(f"No URL found in file data for {phrase_type.value}")
                    return None
            else:
                logger.warning(f"No canned audio found for {phrase_type.value} - {restaurant_slug}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get canned audio URL for {phrase_type.value}: {str(e)}")
            return None
    
    async def generate_and_store_canned_audio(
        self, 
        phrase_type: AudioPhraseType, 
        restaurant_slug: str,
        restaurant_name: str = None
    ) -> Optional[str]:
        """
        Generate and store a canned audio phrase
        
        Args:
            phrase_type: Type of phrase to generate
            restaurant_slug: Restaurant identifier
            restaurant_name: Restaurant name for customization
            
        Returns:
            URL to the stored audio file, or None if failed
        """
        try:
            # Get the text for this phrase
            text = AudioPhraseConstants.get_phrase_text(phrase_type, restaurant_name)
            if not text:
                logger.error(f"No text found for phrase type {phrase_type.value}")
                return None
            
            # Generate audio using TTS service
            logger.info(f"Generating audio for {phrase_type.value}: '{text}'")
            audio_chunks = []
            async for chunk in self.tts_service.generate_audio_stream(
                text, 
                voice=AudioPhraseConstants.STANDARD_VOICE
            ):
                audio_chunks.append(chunk)
            
            # Combine chunks into complete audio
            audio_data = b''.join(audio_chunks)
            
            # Store in blob storage using the organized path from constants
            blob_path = AudioPhraseConstants.get_blob_path(phrase_type, restaurant_slug)
            
            # Use the blob path directly as the S3 key since that's what the constants are designed for
            result = await self.file_storage.store_file(
                file_data=audio_data,
                file_name=blob_path,
                content_type=f"audio/{AudioPhraseConstants.AUDIO_FORMAT}"
            )
            
            if result.success and result.data:
                # Extract URL from the result data
                url = result.data.get('url') or result.data.get('s3_url')
            else:
                url = None
            
            if url:
                logger.info(f"Successfully stored canned audio at {url}")
                return url
            else:
                logger.error(f"Failed to store canned audio for {phrase_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate and store canned audio for {phrase_type.value}: {str(e)}")
            return None
    
    async def generate_all_canned_audio(self, restaurant_slug: str, restaurant_name: str = None) -> Dict[str, str]:
        """
        Generate all canned audio phrases for a restaurant
        
        Args:
            restaurant_slug: Restaurant identifier
            restaurant_name: Restaurant name for customization
            
        Returns:
            Dictionary mapping phrase types to their audio URLs
        """
        results = {}
        
        for phrase_type in AudioPhraseConstants.get_all_phrase_types():
            try:
                url = await self.generate_and_store_canned_audio(
                    phrase_type, 
                    restaurant_slug, 
                    restaurant_name
                )
                if url:
                    results[phrase_type.value] = url
                    logger.info(f"Generated {phrase_type.value} audio: {url}")
                else:
                    logger.error(f"Failed to generate {phrase_type.value} audio")
                    
            except Exception as e:
                logger.error(f"Error generating {phrase_type.value} audio: {str(e)}")
        
        logger.info(f"Generated {len(results)} canned audio files for {restaurant_slug}")
        return results
    
    async def get_or_generate_canned_audio(
        self, 
        phrase_type: AudioPhraseType, 
        restaurant_slug: str,
        restaurant_name: str = None
    ) -> Optional[str]:
        """
        Get existing canned audio or generate if not found
        
        Args:
            phrase_type: Type of phrase to retrieve/generate
            restaurant_slug: Restaurant identifier
            restaurant_name: Restaurant name for customization
            
        Returns:
            URL to the audio file, or None if failed
        """
        # Try to get existing audio first
        url = await self.get_canned_audio_url(phrase_type, restaurant_slug)
        if url:
            return url
        
        # Generate if not found
        logger.info(f"Canned audio not found for {phrase_type.value}, generating...")
        return await self.generate_and_store_canned_audio(
            phrase_type, 
            restaurant_slug, 
            restaurant_name
        )
