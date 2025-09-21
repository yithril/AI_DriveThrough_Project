"""
Transition Decision Node

Determines if commands are needed for the state transition.
Routes based on state machine rules and intent type.
"""

from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState
from app.core.state_machine import DriveThruStateMachine


async def transition_decision_node(state: ConversationWorkflowState) -> ConversationWorkflowState:
    """
    Decide what action to take based on intent and current state using the state machine.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Updated state with transition decision
    """
    # Initialize state machine
    state_machine = DriveThruStateMachine()
    
    # Get the transition decision from state machine
    transition = state_machine.get_transition(state.current_state, state.intent_type)
    
    # Update state with transition results
    state.target_state = transition.target_state
    state.response_phrase_type = transition.response_phrase_type
    
    # Store transition info for routing decisions
    state.transition_requires_command = transition.requires_command
    state.transition_is_valid = transition.is_valid
    
    return state


def should_continue_after_transition_decision(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next based on transition decision.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "command_agent" or "canned_response"
    """
    # Check if the transition requires command execution
    if hasattr(state, 'transition_requires_command') and state.transition_requires_command:
        return "command_agent"
    else:
        return "canned_response"
