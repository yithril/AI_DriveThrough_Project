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
    
    # Check if order changed and update state
    state.order_state_changed = _did_order_change(batch_result)
    
    if not batch_result:
        # No batch result - go to voice generation with error message
        state.next_node = "voice_generation"
        state.response_phrase_type = AudioPhraseType.COME_AGAIN
        return state
    
    # Intelligent routing logic based on batch outcome and command types
    if batch_result.batch_outcome == "ALL_SUCCESS":
        # Check if any successful commands were clarification commands
        has_clarification = _has_clarification_commands(batch_result)
        
        if has_clarification:
            # Clarification needed - route to clarification agent with prepared context
            state.next_node = "clarification_agent"
            _prepare_clarification_context(state, batch_result)
        else:
            # Simple success - use voice generation with canned phrase
            state.next_node = "voice_generation"
            state.response_phrase_type = _get_success_phrase_type(batch_result.command_family)
    else:
        # Complex situation (partial success, failures, errors) - use clarification agent
        state.next_node = "clarification_agent"
        _prepare_clarification_context(state, batch_result)
    
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
        "ADDITEM": AudioPhraseType.ITEM_ADDED_SUCCESS,
        "ADD_ITEM": AudioPhraseType.ITEM_ADDED_SUCCESS,
        "REMOVEITEM": AudioPhraseType.ITEM_REMOVED_SUCCESS,
        "REMOVE_ITEM": AudioPhraseType.ITEM_REMOVED_SUCCESS,
        "MODIFYITEM": AudioPhraseType.ITEM_UPDATED_SUCCESS,
        "MODIFY_ITEM": AudioPhraseType.ITEM_UPDATED_SUCCESS,
        "CLEARORDER": AudioPhraseType.ORDER_CLEARED_SUCCESS,
        "CLEAR_ORDER": AudioPhraseType.ORDER_CLEARED_SUCCESS,
        "CONFIRMORDER": AudioPhraseType.ORDER_CONFIRM,
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
    return state.next_node or "voice_generation"


def _did_order_change(batch_result) -> bool:
    """
    Check if the order state changed based on command results.
    
    Args:
        batch_result: CommandBatchResult from command execution
        
    Returns:
        bool: True if order was modified, False otherwise
    """
    if not batch_result:
        return False
    
    # Order-changing command families
    ORDER_CHANGING_FAMILIES = {
        "ADD_ITEM", "REMOVE_ITEM", "MODIFY_ITEM", "CLEAR_ORDER", "CONFIRM_ORDER"
    }
    
    # Check if it was an order-modifying command and it succeeded
    return (batch_result.command_family in ORDER_CHANGING_FAMILIES and 
            batch_result.successful_commands > 0)


def _has_clarification_commands(batch_result) -> bool:
    """
    Check if any commands in the batch were clarification commands.
    
    Args:
        batch_result: CommandBatchResult from command execution
        
    Returns:
        bool: True if any commands were clarification commands
    """
    if not batch_result or not batch_result.results:
        return False
    
    # Check for clarification commands in results
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("clarification_type") == "ambiguous_item"):
            return True
    
    # Check command family
    if batch_result.command_family == "CLARIFICATION_NEEDED":
        return True
    
    return False


def _prepare_clarification_context(state: ConversationWorkflowState, batch_result) -> None:
    """
    Prepare clarification context data for the clarification agent.
    
    This function enriches the state with clarification-specific data that the
    clarification agent can use to generate better responses.
    
    Args:
        state: Current conversation workflow state
        batch_result: CommandBatchResult from command execution
    """
    # Extract clarification data from successful clarification commands
    clarification_data = []
    
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("clarification_type") == "ambiguous_item"):
            
            clarification_data.append({
                "ambiguous_item": result.data.get("ambiguous_item"),
                "suggested_options": result.data.get("suggested_options", []),
                "user_input": result.data.get("user_input"),
                "clarification_question": result.data.get("clarification_question"),
                "needs_user_response": result.data.get("needs_user_response", True)
            })
    
    # Store clarification data in state for the clarification agent to use
    state.clarification_context = {
        "clarification_commands": clarification_data,
        "batch_outcome": batch_result.batch_outcome,
        "command_family": batch_result.command_family,
        "total_commands": batch_result.total_commands,
        "successful_commands": batch_result.successful_commands,
        "failed_commands": batch_result.failed_commands
    }
    
    # Set expectation for user response if clarification is needed
    if clarification_data:
        state.conversation_context.expectation = "clarification_response"
