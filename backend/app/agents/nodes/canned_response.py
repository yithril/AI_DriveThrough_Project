"""
Canned Response Node

Handles canned responses by resolving AudioPhraseType to actual audio URLs.
These are pre-generated phrases that don't need dynamic TTS.
"""

import logging
from app.agents.state import ConversationWorkflowState
from app.constants.audio_phrases import AudioPhraseConstants

logger = logging.getLogger(__name__)


async def canned_response_node(state: ConversationWorkflowState) -> ConversationWorkflowState:
    """
    Handle canned responses by resolving AudioPhraseType to actual audio URLs.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Updated state with audio URL and response text
    """
    # Import services at runtime to avoid circular imports
    from app.core.container import Container
    
    try:
        # Get voice service from container
        container = Container()
        voice_service = container.voice_service()
        
        # If we have a phrase type, resolve it to audio
        if state.response_phrase_type and voice_service:
            # Get or generate the canned audio
            state.audio_url = await voice_service.get_canned_phrase(
                state.response_phrase_type, 
                restaurant_id=state.restaurant_id
            )
            
            # Also get the text for logging/debugging
            state.response_text = AudioPhraseConstants.get_phrase_text(
                state.response_phrase_type, 
                restaurant_name=str(state.restaurant_id)  # Using as restaurant name for now
            )
            
            logger.info(f"Resolved canned phrase {state.response_phrase_type.value} to audio: {state.audio_url}")
            
        else:
            # Fallback if no phrase type or voice service
            state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
            state.audio_url = None
            logger.warning("No response phrase type available for canned response")
        
        # Handle low confidence intents with clarification requests
        if hasattr(state, 'intent_confidence') and state.intent_confidence < 0.7:
            # Add clarification request to response
            if state.response_text:
                state.response_text += " Could you please repeat that?"
            else:
                state.response_text = "I didn't quite catch that. Could you repeat your order?"
            
    except Exception as e:
        logger.error(f"Canned response generation failed: {str(e)}")
        # Fallback response
        state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
        state.audio_url = None
    
    return state


def should_continue_after_canned_response(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after canned response.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "END" (canned responses are complete)
    """
    # Canned responses are complete - they already have audio_url
    # No need to go through voice_generator (which would duplicate TTS)
    return "END"
