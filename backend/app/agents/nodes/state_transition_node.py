"""
State Transition Node

Determines if commands are needed for the state transition and updates Redis state immediately.
Routes based on state machine rules and intent type.
"""

from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState
from app.core.state_machine import DriveThruStateMachine


async def state_transition_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    Decide what action to take based on intent and current state using the state machine.
    Updates Redis state immediately for valid transitions.
    
    Args:
        state: Current conversation workflow state
        context: LangGraph context containing services
        
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
    
    # Update Redis state immediately for valid transitions
    if transition.is_valid and transition.target_state:
        try:
            # Get order session service from factory
            service_factory = config.get("configurable", {}).get("service_factory") if config else None
            order_session_service = service_factory.create_order_session_service() if service_factory else None
                
                # Update the session state in Redis immediately
            await order_session_service.update_session(
                    session_id=state.session_id,
                    updates={
                        "conversation_state": transition.target_state.value,
                        "updated_at": state.session_id  # This will be updated by the service
                    }
                )
                
                # Update the workflow state to reflect the new state
            state.current_state = transition.target_state
                
        except Exception as e:
            # Log error but don't fail the workflow
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update Redis state for session {state.session_id}: {str(e)}")
    
    return state


def should_continue_after_state_transition(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next based on transition decision.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "intent_parser_router" or "voice_generation"
    """
    # Check if the transition requires command execution
    if hasattr(state, 'transition_requires_command') and state.transition_requires_command:
        return "intent_parser_router"
    else:
        return "voice_generation"
