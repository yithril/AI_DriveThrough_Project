"""
Final Response Aggregator Node

Processes command batch results into comprehensive, user-friendly responses.
Handles success acknowledgments, unavailable items, and clarification questions.
"""

import logging
from typing import Dict, Any, List
from app.agents.state import ConversationWorkflowState
from app.agents.command_agents.clarification_agent import clarification_agent_service
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


async def final_response_aggregator_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    Aggregate command batch results into a comprehensive final response.
    
    Args:
        state: Current conversation workflow state with command batch result
        config: LangGraph config containing services
        
    Returns:
        Updated state with final response text and routing to voice generation
    """
    try:
        print(f"\n🔍 DEBUG - FINAL RESPONSE AGGREGATOR NODE:")
        print(f"   State has command_batch_result: {state.command_batch_result is not None}")
        
        # Get the batch result from command executor
        batch_result = state.command_batch_result
        
        if not batch_result:
            print(f"   No batch result - using fallback response")
            # No batch result - fallback response
            state.response_text = "I'm sorry, I didn't understand. Could you please try again?"
            state.response_phrase_type = AudioPhraseType.DIDNT_UNDERSTAND
            state.next_node = "voice_generation"
            return state
        
        print(f"   Batch result: {batch_result}")
        print(f"   Successful commands: {batch_result.successful_commands}")
        print(f"   Failed commands: {batch_result.failed_commands}")
        print(f"   Results: {len(batch_result.results) if batch_result.results else 0}")
        
        # Check if clarification is needed
        needs_clarification = _needs_clarification(batch_result)
        clarification_response = None
        
        if needs_clarification:
            # Call clarification service
            clarification_response = await clarification_agent_service(
                batch_result=batch_result,
                state=state,
                config=config
            )
        
        # Build final aggregated response
        final_response = _build_final_response(batch_result, clarification_response)
        
        # Check if user wants to finish order
        if _wants_to_finish_order(batch_result):
            final_response += " Would you like anything else?"
        
        # Set response and route to voice generation
        state.response_text = final_response
        state.response_phrase_type = _determine_phrase_type(batch_result)
        state.next_node = "voice_generation"
        
        logger.info(f"Final response aggregated: {final_response}")
        
        return state
        
    except Exception as e:
        logger.error(f"Final response aggregator failed: {e}")
        # Fallback response
        state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
        state.response_phrase_type = AudioPhraseType.DIDNT_UNDERSTAND
        state.next_node = "voice_generation"
        return state


def _needs_clarification(batch_result) -> bool:
    """
    Check if the batch result contains commands that need clarification.
    
    Args:
        batch_result: Command execution results
        
    Returns:
        True if clarification is needed
    """
    # Check for clarification commands in successful results
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("response_type") == "clarification_needed"):
            return True
    
    # Check for ambiguous items that need user choice
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("clarification_type") == "ambiguous_item"):
            return True
    
    return False


def _build_final_response(batch_result, clarification_response) -> str:
    """
    Build the final aggregated response from batch results and clarification.
    
    Args:
        batch_result: Command execution results
        clarification_response: Response from clarification service (if any)
        
    Returns:
        Final aggregated response text
    """
    response_parts = []
    
    # 1. Success acknowledgment (if anything succeeded)
    if batch_result.successful_commands > 0:
        response_parts.append("Your order has been updated.")
    
    # 2. Unavailable items (straightforward, no LLM needed)
    unavailable_items = []
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("response_type") == "item_unavailable"):
            requested_item = result.data.get("requested_item", "that item")
            unavailable_items.append(requested_item)
    
    if unavailable_items:
        if len(unavailable_items) == 1:
            response_parts.append(f"Sorry, we don't have {unavailable_items[0]}.")
        else:
            items_list = ", ".join(unavailable_items[:-1]) + f" and {unavailable_items[-1]}"
            response_parts.append(f"Sorry, we don't have {items_list}.")
    
    # 3. Clarification questions (from clarification service, if any)
    if clarification_response:
        response_parts.append(clarification_response.response_text)
    
    # Combine all parts
    final_response = " ".join(response_parts)
    
    # Ensure we have a response
    if not final_response.strip():
        final_response = "I'm sorry, I didn't understand. Could you please try again?"
    
    return final_response


def _wants_to_finish_order(batch_result) -> bool:
    """
    Check if the user wants to finish their order based on batch results.
    
    Args:
        batch_result: Command execution results
        
    Returns:
        True if user seems to want to finish order
    """
    # Check for confirm order commands
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("response_type") == "order_confirmed"):
            return True
    
    # Check if all items were successfully added (no clarifications needed)
    if (batch_result.successful_commands > 0 and 
        batch_result.failed_commands == 0 and
        not _needs_clarification(batch_result)):
        return True
    
    return False


def _determine_phrase_type(batch_result) -> AudioPhraseType:
    """
    Determine the appropriate phrase type based on batch results.
    
    Args:
        batch_result: Command execution results
        
    Returns:
        Appropriate AudioPhraseType for the response
    """
    # Check for specific command types in results
    for result in batch_result.results:
        if result.is_success and result.data:
            response_type = result.data.get("response_type")
            if response_type == "item_unavailable":
                return AudioPhraseType.ITEM_UNAVAILABLE
            elif response_type == "clarification_needed":
                return AudioPhraseType.CLARIFICATION_QUESTION
            elif response_type == "order_confirmed":
                return AudioPhraseType.ORDER_CONFIRM
    
    # Check for success/failure patterns
    if batch_result.successful_commands > 0 and batch_result.failed_commands == 0:
        return AudioPhraseType.ITEM_ADDED_SUCCESS
    elif batch_result.successful_commands > 0 and batch_result.failed_commands > 0:
        return AudioPhraseType.CUSTOM_RESPONSE  # Mixed results need custom response
    elif batch_result.failed_commands > 0:
        return AudioPhraseType.DIDNT_UNDERSTAND
    else:
        return AudioPhraseType.CUSTOM_RESPONSE


def should_continue_after_final_response_aggregator(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after final response aggregator.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name
    """
    # Final response aggregator always goes to voice generation
    return "voice_generation"
