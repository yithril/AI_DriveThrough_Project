"""
Response Router Node

Routes command batch results to appropriate response nodes based on intent and outcome.
Sets routing context for the next node to use.
"""

from typing import Dict, Any
from app.agents.state.conversation_state import ConversationWorkflowState
from app.constants.audio_phrases import AudioPhraseType


async def response_router_node(state: ConversationWorkflowState) -> ConversationWorkflowState:
    """
    Route command batch results to appropriate response nodes.
    
    Simplified 2-category system:
    - canned_response: Simple, predictable responses (pre-recorded audio)
    - llm_response: Dynamic content or clarification (LLM + TTS)
    
    Args:
        state: Current conversation workflow state with command batch result
        
    Returns:
        Updated state with routing decision
    """
    # Get the batch result from command executor
    batch_result = state.command_batch_result
    
    if not batch_result:
        # No batch result - go to voice generation with error message
        state.next_node = "voice_generation"
        state.response_phrase_type = AudioPhraseType.COME_AGAIN
        return state
    
    # Simple routing logic based on batch outcome
    if batch_result.batch_outcome == "ALL_SUCCESS":
        # Simple success - use voice generation with canned phrase
        state.next_node = "voice_generation"
        state.response_phrase_type = _get_success_phrase_type(batch_result.command_family)
    else:
        # Complex situation (partial success, failures, errors) - use clarification agent
        state.next_node = "clarification_agent"
    
    return state


def _get_success_phrase_type(command_family: str) -> AudioPhraseType:
    """
    Get the appropriate AudioPhraseType for successful commands.
    
    Args:
        command_family: The type of command that succeeded (ADD_ITEM, REMOVE_ITEM, etc.)
        
    Returns:
        Appropriate AudioPhraseType for the success case
    """
    success_phrases = {
        "ADD_ITEM": AudioPhraseType.ITEM_ADDED_SUCCESS,
        "REMOVE_ITEM": AudioPhraseType.ITEM_REMOVED_SUCCESS,
        "MODIFY_ITEM": AudioPhraseType.ITEM_UPDATED_SUCCESS,
        "CLEAR_ORDER": AudioPhraseType.ORDER_CLEARED_SUCCESS,
        "CONFIRM_ORDER": AudioPhraseType.ORDER_CONFIRM,
        "QUESTION": AudioPhraseType.HOW_CAN_I_HELP,
        "REPEAT": AudioPhraseType.ORDER_REPEAT,
        "SMALL_TALK": AudioPhraseType.THANK_YOU,
        "UNKNOWN": AudioPhraseType.COME_AGAIN
    }
    
    return success_phrases.get(command_family, AudioPhraseType.THANK_YOU)


def should_continue_after_response_router(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after response routing.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name based on routing decision
    """
    # The response router sets the next_node, so we just return it
    return state.next_node or "canned_response"
