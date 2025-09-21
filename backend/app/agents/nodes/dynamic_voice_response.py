"""
Dynamic Voice Response Node

Converts dynamic text responses to audio using TTS service.
Handles responses that aren't canned phrases (e.g., from commands, LLM responses).
Implements caching for identical responses.
"""

from typing import Dict, Any
import hashlib
import logging
from app.agents.state import ConversationWorkflowState

logger = logging.getLogger(__name__)


async def dynamic_voice_response_node(state: ConversationWorkflowState) -> ConversationWorkflowState:
    """
    Generate dynamic voice response from text using VoiceService with caching.
    Handles responses that aren't canned phrases (e.g., from commands, LLM responses).
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Updated state with audio URL
    """
    # Import services at runtime to avoid circular imports
    from app.core.container import Container
    
    try:
        # Get voice service from container
        container = Container()
        voice_service = container.voice_service()
        
        # Only generate voice if we have response text
        if not state.response_text or not state.response_text.strip():
            logger.warning("No response text to generate voice from")
            state.audio_url = None
            return state
        
        # Generate voice with caching
        # Use restaurant_id for multitenancy, default voice/language
        audio_url = await voice_service.generate_voice(
            text=state.response_text,
            voice="nova",  # Default voice
            language="english",  # Default language
            restaurant_id=int(state.restaurant_id) if state.restaurant_id else None
        )
        
        if audio_url:
            state.audio_url = audio_url
            logger.info(f"Generated voice audio: {audio_url}")
        else:
            state.add_error("Voice generation failed - no audio URL returned")
            state.audio_url = None
            
    except Exception as e:
        logger.error(f"Voice generation failed: {str(e)}")
        state.add_error(f"Voice generation failed: {str(e)}")
        state.audio_url = None
    
    return state


def should_continue_after_dynamic_voice_response(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after dynamic voice response generation.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "END" (workflow complete)
    """
    # Dynamic voice response is typically the final step
    # All dynamic responses (from commands, LLM) go through this node
    return "END"  # LangGraph convention for workflow end
