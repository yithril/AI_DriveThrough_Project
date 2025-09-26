"""
Voice Generation Service

Handles all audio generation using the unified voice service API.
Supports both canned phrases and dynamic TTS generation.

Converted from voice_generation_node.py to be a reusable service.
"""

import logging
from typing import Dict, Any, Optional
from app.constants.audio_phrases import AudioPhraseConstants, AudioPhraseType

logger = logging.getLogger(__name__)


class VoiceGenerationService:
    """
    Service for handling all audio generation using the unified voice service API.
    
    Supports both canned phrases and dynamic TTS generation.
    """
    
    def __init__(self, voice_service):
        """
        Initialize the voice generation service.
        
        Args:
            voice_service: Voice service for audio operations
        """
        self.voice_service = voice_service
        self.logger = logging.getLogger(__name__)
    
    async def generate_voice_response(
        self,
        response_text: str,
        response_phrase_type: Optional[AudioPhraseType],
        restaurant_id: str,
        custom_response_text: Optional[str] = None,
        intent_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate audio using the unified voice service API.
        
        Args:
            response_text: The response text to generate audio for
            response_phrase_type: The type of audio phrase to generate
            restaurant_id: Restaurant identifier
            custom_response_text: Custom text for TTS generation
            intent_confidence: Confidence level of intent classification
            
        Returns:
            Dictionary with audio URL and response text
        """
        try:
            if not self.voice_service:
                self.logger.error("Voice service not available")
                return {
                    "success": False,
                    "response_text": "I'm sorry, I'm having trouble with the audio system. Please try again.",
                    "audio_url": None
                }
            
            # Check if we have phrase type and custom text
            if response_phrase_type:
                # Use unified audio generation API
                audio_url = await self.voice_service.generate_audio(
                    phrase_type=response_phrase_type,
                    restaurant_id=restaurant_id,
                    custom_text=response_text,  # Use response_text as custom_text
                    restaurant_name=str(restaurant_id)
                )
                
                # Use custom response text if provided, otherwise use canned phrase text
                if response_text and response_text.strip():
                    final_response_text = response_text
                else:
                    final_response_text = AudioPhraseConstants.get_phrase_text(
                        response_phrase_type, 
                        restaurant_name=str(restaurant_id)
                    )
                
                self.logger.info(f"Generated audio for {response_phrase_type.value}: {audio_url}")
                
                # Handle low confidence intents with clarification requests
                if intent_confidence is not None and intent_confidence < 0.7:
                    # Add clarification request to response
                    if final_response_text:
                        final_response_text += " Could you please repeat that?"
                    else:
                        final_response_text = "I didn't quite catch that. Could you repeat your order?"
                
                return {
                    "success": True,
                    "response_text": final_response_text,
                    "audio_url": audio_url
                }
            else:
                # Fallback if no phrase type
                self.logger.warning("No response phrase type available for voice generation")
                return {
                    "success": False,
                    "response_text": "I'm sorry, I had trouble processing your request. Please try again.",
                    "audio_url": None
                }
            
        except Exception as e:
            self.logger.error(f"Voice generation failed: {str(e)}")
            # Fallback response
            return {
                "success": False,
                "response_text": "I'm sorry, I had trouble processing your request. Please try again.",
                "audio_url": None
            }
    
    def should_continue_after_generation(self, generation_result: Dict[str, Any]) -> str:
        """
        Determine which step to go to next after voice generation.
        
        Args:
            generation_result: Voice generation result
            
        Returns:
            Next step name: "END" (voice generation is complete)
        """
        # Voice generation is complete - they already have audio_url
        return "END"
