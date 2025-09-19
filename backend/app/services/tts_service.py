"""
Text-to-Speech service
"""

from typing import AsyncGenerator
from .tts_provider import TTSProvider
import logging

logger = logging.getLogger(__name__)


class TTSService:
    """
    TTS service that handles text-to-speech generation
    """
    
    def __init__(self, provider: TTSProvider):
        self.provider = provider
    
    async def generate_audio_stream(self, text: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate audio stream from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        logger.info(f"Generating audio for text: '{text[:50]}...' with voice: {voice}")
        
        try:
            async for chunk in self.provider.generate_audio_stream(text, voice):
                yield chunk
                
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    async def generate_greeting_audio(self, car_number: int, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate greeting audio for a car number
        
        Args:
            car_number: Car number for greeting
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        greeting_text = f"Welcome to our drive-thru! Car number {car_number}, please take a look at our menu and let us know what you'd like to order today."
        
        async for chunk in self.generate_audio_stream(greeting_text, voice):
            yield chunk
    
    async def generate_menu_audio(self, menu_item: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate menu announcement audio
        
        Args:
            menu_item: Menu item to announce
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        menu_text = f"Our special today is the {menu_item}! It's out of this world!"
        
        async for chunk in self.generate_audio_stream(menu_text, voice):
            yield chunk
    
    async def generate_order_audio(self, order_summary: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate order confirmation audio
        
        Args:
            order_summary: Order summary text
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        order_text = f"Thank you! I have your order: {order_summary}. Is that correct?"
        
        async for chunk in self.generate_audio_stream(order_text, voice):
            yield chunk
    
    async def generate_error_audio(self, error_type: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate error message audio
        
        Args:
            error_type: Type of error (not_understood, system_error, no_order)
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        error_messages = {
            "not_understood": "I'm sorry, I didn't catch that. Could you please repeat your order?",
            "system_error": "I'm experiencing some technical difficulties. Please give me a moment.",
            "no_order": "I don't see any items in your order yet. What would you like to order today?"
        }
        
        error_text = error_messages.get(error_type, "I'm sorry, I didn't understand that.")
        
        async for chunk in self.generate_audio_stream(error_text, voice):
            yield chunk
