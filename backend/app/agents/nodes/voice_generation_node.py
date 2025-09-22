"""
Voice Generation Node

Handles all audio generation using the unified voice service API.
Supports both canned phrases and dynamic TTS generation.
"""

import logging
from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.constants.audio_phrases import AudioPhraseConstants

logger = logging.getLogger(__name__)


async def voice_generation_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    Generate audio using the unified voice service API.
    
    Args:
        state: Current conversation workflow state
        context: LangGraph context containing services
        
    Returns:
        Updated state with audio URL and response text
    """
    try:
        # Get voice service from factory
        service_factory = config.get("configurable", {}).get("service_factory") if config else None
        voice_service = service_factory.create_voice_service() if service_factory else None
        
        if not voice_service:
            logger.error("Voice service not available")
            state.response_text = "I'm sorry, I'm having trouble with the audio system. Please try again."
            state.audio_url = None
            return state
        
        # Check if we have phrase type and custom text
        if state.response_phrase_type:
            # Use unified audio generation API
            state.audio_url = await voice_service.generate_audio(
                phrase_type=state.response_phrase_type,
                restaurant_id=state.restaurant_id,
                custom_text=state.custom_response_text,
                restaurant_name=str(state.restaurant_id)
            )
            
            # Get the text for logging/debugging
            state.response_text = AudioPhraseConstants.get_phrase_text(
                state.response_phrase_type, 
                restaurant_name=str(state.restaurant_id)
            )
            
            logger.info(f"Generated audio for {state.response_phrase_type.value}: {state.audio_url}")
            
        else:
            # Fallback if no phrase type
            state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
            state.audio_url = None
            logger.warning("No response phrase type available for voice generation")
        
        # Handle low confidence intents with clarification requests
        if hasattr(state, 'intent_confidence') and state.intent_confidence < 0.7:
            # Add clarification request to response
            if state.response_text:
                state.response_text += " Could you please repeat that?"
            else:
                state.response_text = "I didn't quite catch that. Could you repeat your order?"
            
    except Exception as e:
        logger.error(f"Voice generation failed: {str(e)}")
        # Fallback response
        state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
        state.audio_url = None
    
    return state


def should_continue_after_voice_generation(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after voice generation.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "END" (voice generation is complete)
    """
    # Voice generation is complete - they already have audio_url
    return "END"
