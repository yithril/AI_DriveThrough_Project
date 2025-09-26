"""
State Transition Service

Determines if commands are needed for the state transition and updates Redis state immediately.
Routes based on state machine rules and intent type.

Converted from state_transition_node.py to be a reusable service.
"""

import logging
from typing import Dict, Any, List
from app.models.state_machine_models import ConversationState
from app.core.state_machine import DriveThruStateMachine
from app.commands.intent_classification_schema import IntentType

logger = logging.getLogger(__name__)


class StateTransitionService:
    """
    Service for handling state transitions using the state machine.
    
    Determines if commands are needed for the state transition and updates Redis state immediately.
    Routes based on state machine rules and intent type.
    """
    
    def __init__(self, order_session_service):
        """
        Initialize the state transition service.
        
        Args:
            order_session_service: Order session service for session management
        """
        self.order_session_service = order_session_service
        self.state_machine = DriveThruStateMachine()
        self.logger = logging.getLogger(__name__)
    
    async def validate_transition(
        self,
        current_state: ConversationState,
        intent_type: IntentType,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Validate state transition and update Redis state if valid.
        
        Args:
            current_state: Current conversation state
            intent_type: Classified intent type
            session_id: Session identifier
            
        Returns:
            Dictionary with transition results and routing decision
        """
        try:
            # Get the transition decision from state machine
            transition = self.state_machine.get_transition(current_state, intent_type)
            
            # Update Redis state immediately for valid transitions
            if transition.is_valid and transition.target_state:
                try:
                    # Update the session state in Redis immediately
                    await self.order_session_service.update_session(
                        session_id=session_id,
                        updates={
                            "conversation_state": transition.target_state.value,
                            "updated_at": session_id  # This will be updated by the service
                        }
                    )
                    
                    self.logger.info(f"Updated Redis state for session {session_id} to {transition.target_state.value}")
                    
                except Exception as e:
                    # Log error but don't fail the workflow
                    self.logger.error(f"Failed to update Redis state for session {session_id}: {str(e)}")
            
            # Return transition results
            return {
                "is_valid": transition.is_valid,
                "target_state": transition.target_state,
                "requires_command": transition.requires_command,
                "response_phrase_type": transition.response_phrase_type,
                "current_state": current_state
            }
            
        except Exception as e:
            self.logger.error(f"State transition validation failed: {e}")
            # Return invalid transition on error
            return {
                "is_valid": False,
                "target_state": current_state,
                "requires_command": False,
                "response_phrase_type": None,
                "current_state": current_state,
                "error": str(e)
            }
    
    def should_continue_after_transition(self, transition_result: Dict[str, Any]) -> str:
        """
        Determine which step to go to next based on transition decision.
        
        Args:
            transition_result: State transition result
            
        Returns:
            Next step name: "intent_parser_router" or "voice_generation"
        """
        # Check if the transition requires command execution
        if transition_result.get("requires_command", False):
            return "intent_parser_router"
        else:
            return "voice_generation"
