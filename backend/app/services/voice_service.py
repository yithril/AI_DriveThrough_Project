"""
Voice Service - Unified service for all voice operations

Consolidates:
- Text-to-Speech generation with caching
- Canned audio phrase management  
- Speech-to-Text transcription
- Unified S3 bucket naming conventions
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from .text_to_speech_service import TextToSpeechService
from .speech_to_text_service import SpeechToTextService
from .file_storage_service import FileStorageService
from .redis_service import RedisService
from ..constants.audio_phrases import AudioPhraseType, AudioPhraseConstants

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Unified service for all voice operations.
    
    Consolidates:
    - Text-to-Speech generation with caching
    - Canned audio phrase management
    - Speech-to-Text transcription
    - Unified S3 bucket naming conventions
    """
    
    def __init__(
        self, 
        text_to_speech_service: TextToSpeechService,
        speech_to_text_service: SpeechToTextService,
        file_storage_service: FileStorageService,
        redis_service: RedisService = None
    ):
        self.text_to_speech_service = text_to_speech_service
        self.speech_to_text_service = speech_to_text_service
        self.file_storage_service = file_storage_service
        self.redis_service = redis_service
    
    def _generate_cache_key(
        self, 
        text: str, 
        voice: str = "nova", 
        language: str = "english",
        restaurant_id: int = None
    ) -> str:
        """
        Generate a cache key for the given parameters.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default: nova)
            language: Language to use (default: english)
            restaurant_id: Restaurant ID for multitenancy (optional)
            
        Returns:
            MD5 hex string safe for S3 object keys
        """
        # Include all parameters that affect the generated audio
        cache_content = f"{text}_{voice}_{language}_{restaurant_id or 'default'}"
        
        # Generate MD5 hash (hex string is S3-safe)
        cache_key = hashlib.md5(cache_content.encode('utf-8')).hexdigest()
        
        logger.debug(f"Generated cache key: {cache_key} for text: '{text[:50]}...'")
        return cache_key
    
    def _get_redis_cache_key(self, md5_hash: str, restaurant_id: int = None) -> str:
        """
        Generate Redis cache key for voice audio.
        
        Args:
            md5_hash: MD5 hash of the voice content
            restaurant_id: Restaurant ID for multitenancy
            
        Returns:
            Redis cache key
        """
        if restaurant_id:
            return f"voice:cache:restaurant:{restaurant_id}:{md5_hash}"
        else:
            return f"voice:cache:default:{md5_hash}"
    
    async def _get_cached_voice_url(self, md5_hash: str, restaurant_id: int = None) -> Optional[str]:
        """
        Get cached voice URL from Redis.
        
        Args:
            md5_hash: MD5 hash of the voice content
            restaurant_id: Restaurant ID for multitenancy
            
        Returns:
            Cached S3 URL or None if not found
        """
        if not self.redis_service:
            return None
            
        try:
            cache_key = self._get_redis_cache_key(md5_hash, restaurant_id)
            cached_url = await self.redis_service.get(cache_key)
            if cached_url:
                logger.info(f"Found cached voice URL in Redis: {cached_url}")
                return cached_url
        except Exception as e:
            logger.warning(f"Redis cache lookup failed: {str(e)}")
        
        return None
    
    async def _cache_voice_url(self, md5_hash: str, s3_url: str, restaurant_id: int = None, ttl: int = 86400) -> bool:
        """
        Cache voice URL in Redis.
        
        Args:
            md5_hash: MD5 hash of the voice content
            s3_url: S3 URL to cache
            restaurant_id: Restaurant ID for multitenancy
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis_service:
            return False
            
        try:
            cache_key = self._get_redis_cache_key(md5_hash, restaurant_id)
            await self.redis_service.set(cache_key, s3_url, ttl)
            logger.info(f"Cached voice URL in Redis: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"Redis cache storage failed: {str(e)}")
            return False
    
    def _get_cache_path(self, cache_key: str, restaurant_id: int = None) -> str:
        """
        Generate the S3 path for cached audio.
        
        Args:
            cache_key: Generated cache key
            restaurant_id: Restaurant ID for multitenancy
            
        Returns:
            S3 object key path
        """
        if restaurant_id:
            return f"tts-cache/restaurant-{restaurant_id}/{cache_key}.mp3"
        else:
            return f"tts-cache/default/{cache_key}.mp3"
    
    async def generate_voice(
        self, 
        text: str, 
        voice: str = "nova", 
        language: str = "english",
        restaurant_id: int = None
    ) -> Optional[str]:
        """
        Generate voice from text with caching support.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default: nova)
            language: Language to use (default: english) 
            restaurant_id: Restaurant ID for multitenancy (optional)
            
        Returns:
            URL to the audio file, or None if generation failed
        """
        if not text or not text.strip():
            logger.warning("Cannot generate voice for empty text")
            return None
        
        try:
            # Generate cache key and path
            cache_key = self._generate_cache_key(text, voice, language, restaurant_id)
            cache_path = self._get_cache_path(cache_key, restaurant_id)
            
            # Check Redis cache
            cached_url = await self._get_cached_voice_url(cache_key, restaurant_id)
            if cached_url:
                return cached_url
            
            # Generate new audio
            logger.info(f"Generating new voice audio for: '{text[:50]}...'")
            audio_chunks = []
            
            async for chunk in self.text_to_speech_service.generate_audio_stream(text, voice):
                audio_chunks.append(chunk)
            
            if not audio_chunks:
                logger.error("No audio chunks generated")
                return None
            
            # Combine chunks into complete audio
            audio_data = b''.join(audio_chunks)
            
            # Store in cache
            logger.info(f"Storing voice audio in cache: {cache_path}")
            store_result = await self.file_storage_service.store_file(
                file_data=audio_data,
                file_name=cache_path,
                content_type="audio/mpeg"
            )
            
            if store_result.success and store_result.data:
                audio_url = store_result.data.get('url') or store_result.data.get('s3_url')
                
                # Cache the URL in Redis for faster future access
                await self._cache_voice_url(cache_key, audio_url, restaurant_id)
                
                logger.info(f"Successfully generated and cached voice audio: {audio_url}")
                return audio_url
            else:
                logger.error(f"Failed to store voice audio: {store_result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Voice generation failed: {str(e)}")
            return None
    
    async def clear_cache(self, restaurant_id: int = None) -> bool:
        """
        Clear cached voice files for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID to clear cache for (None = clear all)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if restaurant_id:
                cache_prefix = f"tts-cache/restaurant-{restaurant_id}/"
                logger.info(f"Clearing voice cache for restaurant {restaurant_id}")
            else:
                cache_prefix = "tts-cache/"
                logger.info("Clearing all voice cache")
            
            # TODO: Implement cache clearing logic
            # This would depend on the file storage service's ability to delete by prefix
            logger.warning("Cache clearing not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"Failed to clear voice cache: {str(e)}")
            return False
    
    # ===== UNIFIED AUDIO GENERATION =====
    
    async def generate_audio(
        self, 
        phrase_type: AudioPhraseType, 
        restaurant_id: int,
        custom_text: Optional[str] = None,
        restaurant_name: str = None
    ) -> Optional[str]:
        """
        Unified method for generating all audio (canned or dynamic).
        
        Args:
            phrase_type: Type of audio phrase to generate
            restaurant_id: Restaurant ID for multitenancy (required)
            custom_text: Custom text for dynamic phrases (optional)
            restaurant_name: Restaurant name for customization
            
        Returns:
            URL to the audio file, or None if failed
        """
        try:
            # Determine if this is a canned phrase or dynamic
            if self._is_canned_phrase(phrase_type) and not custom_text:
                # Use pre-recorded audio
                return await self.get_canned_phrase(phrase_type, restaurant_id, restaurant_name)
            else:
                # Generate TTS with custom text or fallback text
                text = custom_text or AudioPhraseConstants.get_phrase_text(phrase_type, restaurant_name)
                return await self._generate_tts(text, restaurant_id)
                
        except Exception as e:
            logger.error(f"Audio generation failed: {str(e)}")
            return None
    
    def _is_canned_phrase(self, phrase_type: AudioPhraseType) -> bool:
        """
        Determine if a phrase type should use pre-recorded audio.
        
        Args:
            phrase_type: Type of audio phrase
            
        Returns:
            True if should use canned audio, False for TTS
        """
        # Dynamic phrases that always use TTS
        dynamic_phrases = {
            AudioPhraseType.CUSTOM_RESPONSE,
            AudioPhraseType.CLARIFICATION_QUESTION,
            AudioPhraseType.ERROR_MESSAGE,
            AudioPhraseType.LLM_GENERATED
        }
        
        return phrase_type not in dynamic_phrases
    
    async def _generate_tts(self, text: str, restaurant_id: int) -> Optional[str]:
        """
        Generate TTS audio for dynamic content.
        
        Args:
            text: Text to convert to speech
            restaurant_id: Restaurant ID for multitenancy
            
        Returns:
            URL to the audio file, or None if failed
        """
        try:
            # Use existing generate_voice method
            return await self.generate_voice(
                text=text,
                voice=AudioPhraseConstants.STANDARD_VOICE,
                language="english",
                restaurant_id=restaurant_id
            )
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            return None
    
    # ===== CANNED AUDIO FUNCTIONALITY =====
    
    async def get_canned_phrase(
        self, 
        phrase_type: AudioPhraseType, 
        restaurant_id: int,
        restaurant_name: str = None
    ) -> Optional[str]:
        """
        Get or generate a canned audio phrase.
        
        Args:
            phrase_type: Type of canned phrase
            restaurant_id: Restaurant ID for multitenancy (required)
            restaurant_name: Restaurant name for customization
            
        Returns:
            URL to the audio file, or None if failed
        """
        try:
            # Generate cache path for canned phrase
            cache_path = self._get_canned_phrase_path(phrase_type, restaurant_id)
            
            # Check if already cached
            logger.info(f"Checking cache for canned phrase: {cache_path}")
            cached_result = await self.file_storage_service.get_file(cache_path)
            
            if cached_result.success and cached_result.data:
                cached_url = cached_result.data.get('url') or cached_result.data.get('s3_url')
                if cached_url:
                    logger.info(f"Found cached canned phrase: {cached_url}")
                    return cached_url
            
            # Generate new canned phrase
            logger.info(f"Generating new canned phrase: {phrase_type.value}")
            text = AudioPhraseConstants.get_phrase_text(phrase_type, restaurant_name)
            if not text:
                logger.error(f"No text found for phrase type {phrase_type.value}")
                return None
            
            # Generate audio using TTS
            audio_chunks = []
            async for chunk in self.text_to_speech_service.generate_audio_stream(
                text, 
                voice=AudioPhraseConstants.STANDARD_VOICE
            ):
                audio_chunks.append(chunk)
            
            if not audio_chunks:
                logger.error("No audio chunks generated for canned phrase")
                return None
            
            # Store in cache
            audio_data = b''.join(audio_chunks)
            logger.info(f"Storing canned phrase in cache: {cache_path}")
            store_result = await self.file_storage_service.store_file(
                file_data=audio_data,
                file_name=cache_path,
                content_type="audio/mpeg"
            )
            
            if store_result.success and store_result.data:
                audio_url = store_result.data.get('url') or store_result.data.get('s3_url')
                logger.info(f"Successfully generated and cached canned phrase: {audio_url}")
                return audio_url
            else:
                logger.error(f"Failed to store canned phrase: {store_result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Canned phrase generation failed: {str(e)}")
            return None
    
    def _get_canned_phrase_path(self, phrase_type: AudioPhraseType, restaurant_id: int) -> str:
        """
        Generate S3 path for canned phrase.
        
        Args:
            phrase_type: Type of canned phrase
            restaurant_id: Restaurant ID for multitenancy (required)
            
        Returns:
            S3 object key path
        """
        return f"canned-phrases/restaurant-{restaurant_id}/{phrase_type.value}.mp3"
    
    async def generate_all_canned_phrases(
        self, 
        restaurant_id: int, 
        restaurant_name: str = None
    ) -> Dict[str, str]:
        """
        Generate all canned audio phrases for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID for multitenancy (required)
            restaurant_name: Restaurant name for customization
            
        Returns:
            Dictionary mapping phrase types to their audio URLs
        """
        results = {}
        
        for phrase_type in AudioPhraseConstants.get_all_phrase_types():
            try:
                url = await self.get_canned_phrase(phrase_type, restaurant_id, restaurant_name)
                if url:
                    results[phrase_type.value] = url
                    logger.info(f"Generated {phrase_type.value} audio: {url}")
                else:
                    logger.error(f"Failed to generate {phrase_type.value} audio")
                    
            except Exception as e:
                logger.error(f"Error generating {phrase_type.value} audio: {str(e)}")
        
        logger.info(f"Generated {len(results)} canned audio files for restaurant {restaurant_id or 'default'}")
        return results
    
    # ===== SPEECH-TO-TEXT FUNCTIONALITY =====
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        audio_format: str = "webm", 
        language: str = "english"
    ) -> Optional[str]:
        """
        Transcribe audio to text using Speech-to-Text service.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, mp3, wav, etc.)
            language: Language for transcription
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            from ..models.language import Language
            from ..dto.order_result import OrderResult
            
            # Convert language string to Language enum
            lang_enum = Language.from_string(language) if hasattr(Language, 'from_string') else None
            
            result = await self.speech_to_text_service.transcribe_audio(
                audio_data, 
                audio_format, 
                lang_enum
            )
            
            if result.is_success and result.data:
                return result.data.get('transcript', '')
            else:
                logger.error(f"Speech-to-text failed: {result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Speech-to-text transcription failed: {str(e)}")
            return None
    
    # ===== AUDIO FILE STORAGE FUNCTIONALITY =====
    
    async def store_uploaded_audio(
        self, 
        audio_data: bytes, 
        filename: str, 
        content_type: str, 
        restaurant_id: int,
        session_id: str = None
    ) -> Optional[str]:
        """
        Store uploaded audio file (e.g., from customer recording).
        
        Args:
            audio_data: Raw audio bytes
            filename: Original filename
            content_type: MIME type
            restaurant_id: Restaurant ID for multitenancy
            session_id: Session ID for tracking
            
        Returns:
            File ID for the stored audio, or None if failed
        """
        try:
            store_result = await self.file_storage_service.store_file(
                file_data=audio_data,
                file_name=filename,
                content_type=content_type,
                restaurant_id=restaurant_id
            )
            
            if store_result.success and store_result.data:
                file_id = store_result.data.get('file_id')
                logger.info(f"Stored uploaded audio: {filename} -> {file_id}")
                return file_id
            else:
                logger.error(f"Failed to store uploaded audio: {store_result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Audio storage failed: {str(e)}")
            return None
    
    async def store_transcript(
        self, 
        file_id: str, 
        transcript: str, 
        metadata: Dict[str, Any], 
        restaurant_id: int
    ) -> bool:
        """
        Store transcript with metadata for auditing.
        
        Args:
            file_id: Associated audio file ID
            transcript: Transcribed text
            metadata: Additional metadata (duration, confidence, etc.)
            restaurant_id: Restaurant ID for multitenancy
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            store_result = await self.file_storage_service.store_transcript(
                file_id=file_id,
                transcript=transcript,
                metadata=metadata,
                restaurant_id=restaurant_id
            )
            
            if store_result.success:
                logger.info(f"Stored transcript for file {file_id}")
                return True
            else:
                logger.warning(f"Failed to store transcript for file {file_id}: {store_result.message}")
                return False
                
        except Exception as e:
            logger.warning(f"Transcript storage failed for file {file_id}: {str(e)}")
            return False  # Not critical, just for auditing
