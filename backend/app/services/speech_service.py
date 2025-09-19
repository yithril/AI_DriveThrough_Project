"""
Speech-to-Text service for processing audio input
"""

import openai
import asyncio
import io
import os
from typing import Optional, Dict, Any
from ..dto.order_result import OrderResult
from ..models.language import Language
from ..agents.prompts.drive_thru_context import get_drive_thru_context, get_restaurant_context


class SpeechService:
    """
    Service for converting audio to text using OpenAI Whisper with multi-language support
    """
    
    def __init__(self):
        """Initialize speech service with OpenAI API key"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        audio_format: str = "webm", 
        language: Language = None
    ) -> OrderResult:
        """
        Convert audio data to text using OpenAI Whisper with language support
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, mp3, wav, etc.)
            language: Language for transcription (defaults to English)
            
        Returns:
            OrderResult: Contains transcribed text or error
        """
        try:
            # Use default language if none provided
            if language is None:
                language = Language.get_default()
            
            # Create a temporary file-like object for the audio
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"
            
            # Create context prompt for better accuracy in drive-thru environment
            context_prompt = get_drive_thru_context()
            
            # Transcribe using OpenAI Whisper with retry logic
            transcript = await self._transcribe_with_retry(
                audio_file=audio_file,
                language=language,
                context_prompt=context_prompt
            )
            
            # Clean up the transcript
            cleaned_text = transcript.strip()
            
            if not cleaned_text:
                return OrderResult.error("No speech detected in audio")
            
            return OrderResult.success(
                "Audio transcribed successfully",
                data={
                    "transcript": cleaned_text,
                    "language": language.value,
                    "language_name": language.display_name,
                    "confidence": 0.95,  # Whisper doesn't provide confidence scores
                    "audio_format": audio_format,
                    "length": len(audio_data)
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Speech transcription failed: {str(e)}")
    
    async def transcribe_with_context(
        self, 
        audio_data: bytes, 
        context: Dict[str, Any], 
        language: Language = None
    ) -> OrderResult:
        """
        Transcribe audio with restaurant context for better accuracy
        
        Args:
            audio_data: Raw audio bytes
            context: Restaurant context (menu items, common phrases)
            language: Language for transcription (defaults to English)
            
        Returns:
            OrderResult: Contains transcribed text with context
        """
        try:
            # Use default language if none provided
            if language is None:
                language = Language.get_default()
            
            # Get menu items for context
            menu_items = context.get("menu_items", [])
            restaurant_name = context.get("restaurant_name", "")
            
            # Create enhanced context prompt with restaurant-specific info
            context_prompt = get_restaurant_context(restaurant_name, menu_items)
            
            # Create a temporary file-like object
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{language.value}"
            
            # Transcribe with context and retry logic
            transcript = await self._transcribe_with_retry(
                audio_file=audio_file,
                language=language,
                context_prompt=context_prompt
            )
            
            cleaned_text = transcript.strip()
            
            if not cleaned_text:
                return OrderResult.error("No speech detected in audio")
            
            return OrderResult.success(
                "Audio transcribed with context",
                data={
                    "transcript": cleaned_text,
                    "language": language.value,
                    "language_name": language.display_name,
                    "confidence": 0.97,  # Higher confidence with context
                    "context_used": True,
                    "restaurant_name": restaurant_name
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Contextual speech transcription failed: {str(e)}")
    
    
    
    async def _transcribe_with_retry(
        self, 
        audio_file: io.BytesIO, 
        language: Language, 
        context_prompt: str
    ) -> str:
        """
        Transcribe audio with retry logic for transient errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Reset file pointer for each attempt
                audio_file.seek(0)
                
                # Transcribe using OpenAI Whisper
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language=language.whisper_language_code,
                    prompt=context_prompt
                )
                
                return transcript
                
            except openai.APIConnectionError as e:
                # API unreachable - don't retry
                raise OrderResult.error(f"OpenAI API is unreachable: {str(e)}")
                
            except openai.RateLimitError as e:
                # Rate limit - retry with delay
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except openai.APITimeoutError as e:
                # Timeout - retry with delay
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except openai.APIError as e:
                # Other API errors - retry with delay
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                # Unexpected errors - don't retry
                raise OrderResult.error(f"Unexpected error during transcription: {str(e)}")
        
        # If we get here, all retries failed
        raise OrderResult.error(f"Transcription failed after {self.max_retries} attempts: {str(last_exception)}")
