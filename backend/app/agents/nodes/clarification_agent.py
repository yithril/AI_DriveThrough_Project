"""
Clarification Agent Node

Handles complex conversation scenarios that require LLM processing.
Used when commands need clarification, error handling, or dynamic responses.
"""

import logging
from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


async def clarification_agent_node(state: ConversationWorkflowState, context: Dict[str, Any]) -> ConversationWorkflowState:
    """
    Generate LLM-based clarification or error handling response.
    
    Args:
        state: Current conversation workflow state with command batch result
        context: LangGraph context containing services
        
    Returns:
        Updated state with response text and audio URL
    """
    try:
        # Get services from context
        container = context.get("container")
        voice_service = container.voice_service()
        
        if not voice_service:
            logger.error("Voice service not available")
            state.response_text = "I'm sorry, I'm having trouble with the audio system. Please try again."
            state.audio_url = None
            return state
        
        # Get the command batch result for context
        batch_result = state.command_batch_result
        
        if not batch_result:
            # No batch result - fallback response
            state.response_text = "I'm sorry, I didn't understand. Could you please try again?"
            state.audio_url = await voice_service.generate_tts(
                text=state.response_text,
                restaurant_id=state.restaurant_id
            )
            return state
        
        # Generate LLM response based on command results
        response_text = await _generate_clarification_response(
            batch_result=batch_result,
            conversation_history=state.conversation_history,
            order_state=state.order_state,
            user_input=state.user_input
        )
        
        # Generate audio using unified API
        state.response_text = response_text
        state.custom_response_text = response_text  # Set custom text for voice generation
        state.audio_url = await voice_service.generate_audio(
            phrase_type=AudioPhraseType.LLM_GENERATED,
            restaurant_id=state.restaurant_id,
            custom_text=response_text
        )
        
        logger.info(f"Generated clarification response: {response_text[:100]}...")
        
    except Exception as e:
        logger.error(f"Clarification agent generation failed: {str(e)}")
        # Fallback response
        state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
        state.audio_url = None
    
    return state


async def _generate_clarification_response(
    batch_result,
    conversation_history: list,
    order_state,
    user_input: str
) -> str:
    """
    Generate LLM response for clarification or error handling.
    
    Args:
        batch_result: CommandBatchResult with execution details
        conversation_history: Previous conversation context
        order_state: Current order state
        user_input: What the user said
        
    Returns:
        Generated clarification response text
    """
    # TODO: Implement LLM clarification response generation
    # For now, return a simple response based on batch outcome
    
    if batch_result.batch_outcome == "PARTIAL_SUCCESS":
        return "I added some items to your order, but there were some issues. Let me help you with that."
    elif batch_result.batch_outcome == "ALL_FAILED":
        return "I couldn't add those items. Let me help you find what you're looking for."
    elif batch_result.batch_outcome == "FATAL_SYSTEM":
        return "I'm sorry, I'm having some technical difficulties. Please try again."
    else:
        return "I need a bit more information to help you. Could you please clarify?"


def should_continue_after_clarification_agent(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after clarification agent.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "END" (clarification responses are complete)
    """
    # Clarification responses are complete - they already have audio_url
    return "END"
