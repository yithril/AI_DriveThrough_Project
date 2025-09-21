"""
Transition Decision Node

Determines if commands are needed for the state transition.
Routes based on state machine rules and intent type.
"""

from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.core.state_machine import ConversationState


async def transition_decision_node(state: ConversationWorkflowState) -> ConversationWorkflowState:
    """
    Decide what action to take based on intent and current state.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Updated state with transition decision
    """
    # TODO: Implement transition decision logic
    # - Check if intent requires commands (ADD_ITEM, REMOVE_ITEM, etc.)
    # - Check if intent is just a response (CONFIRM_ORDER, QUESTION, etc.)
    # - Determine target state based on current state + intent
    # - Set action_type: "commands_needed", "canned_response", "clarification_needed"
    
    # Stub implementation
    if state.intent_type and state.intent_type in ["ADD_ITEM", "REMOVE_ITEM", "MODIFY_ITEM"]:
        state.target_state = ConversationState.ORDERING
        # We'll add action_type to state later
    else:
        state.target_state = state.current_state  # No state change needed
    
    return state


def should_continue_after_transition_decision(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next based on transition decision.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "command_agent" or "canned_response"
    """
    # TODO: Implement routing logic
    # - Commands needed → "command_agent"
    # - Just a response → "canned_response"
    
    # Stub implementation
    if state.intent_type and state.intent_type in ["ADD_ITEM", "REMOVE_ITEM", "MODIFY_ITEM"]:
        return "command_agent"
    else:
        return "canned_response"
