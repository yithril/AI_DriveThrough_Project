"""
Conversation Orchestrator

Main entry point for processing conversation turns. Replaces LangGraph workflow
with a simple, direct approach that calls the new conversation services.

Follows the exact same flow as the original LangGraph workflow:
1. Intent Classification
2. State Transition  
3. Intent Parser Router
4. Command Executor
5. Response Aggregator
6. Voice Generation
"""

import logging
from typing import Dict, Any, List, Optional
from app.core.services.conversation import (
    IntentClassificationService,
    StateTransitionService,
    IntentParserRouterService,
    CommandExecutorService,
    ResponseAggregatorService,
    VoiceGenerationService
)
from app.commands.intent_classification_schema import IntentType, IntentClassificationResult
from app.models.state_machine_models import ConversationState

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """
    Main orchestrator for conversation processing.
    
    Replaces LangGraph workflow with direct service calls.
    Follows the exact same flow as the original LangGraph workflow.
    """
    
    def __init__(
        self,
        intent_classification_service: IntentClassificationService,
        state_transition_service: StateTransitionService,
        intent_parser_router_service: IntentParserRouterService,
        command_executor_service: CommandExecutorService,
        response_aggregator_service: ResponseAggregatorService,
        voice_generation_service: VoiceGenerationService
    ):
        """
        Initialize the conversation orchestrator.
        
        Args:
            intent_classification_service: Service for classifying user intents
            state_transition_service: Service for managing conversation state transitions
            intent_parser_router_service: Service for routing intents to parsers
            command_executor_service: Service for executing commands
            response_aggregator_service: Service for aggregating responses
            voice_generation_service: Service for generating voice responses
        """
        self.intent_classification_service = intent_classification_service
        self.state_transition_service = state_transition_service
        self.intent_parser_router_service = intent_parser_router_service
        self.command_executor_service = command_executor_service
        self.response_aggregator_service = response_aggregator_service
        self.voice_generation_service = voice_generation_service
        self.logger = logging.getLogger(__name__)
    
    async def process_conversation_turn(
        self, 
        user_input: str, 
        session_id: str, 
        restaurant_id: int,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        order_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a single conversation turn using the new service architecture.
        
        Follows the exact same flow as the original LangGraph workflow:
        1. Intent Classification
        2. State Transition  
        3. Intent Parser Router
        4. Command Executor
        5. Response Aggregator
        6. Voice Generation
        
        Args:
            user_input: User's input text
            session_id: Session identifier
            restaurant_id: Restaurant identifier
            conversation_history: Previous conversation turns (optional)
            order_state: Current order state (optional)
            
        Returns:
            Dictionary containing response text, audio URL, and metadata
        """
        try:
            self.logger.info(f"Processing conversation turn: '{user_input}'")
            print(f"\n🚀 CONVERSATION ORCHESTRATOR:")
            print(f"   User input: '{user_input}'")
            print(f"   Session ID: {session_id}")
            print(f"   Restaurant ID: {restaurant_id}")
            
            # Step 1: Intent Classification
            print(f"\n🔍 STEP 1: Intent Classification")
            intent_result = await self.intent_classification_service.classify_intent(
                user_input=user_input,
                conversation_history=conversation_history or [],
                order_state=order_state or {},
                current_state="ORDERING"  # Default state
            )
            
            print(f"   Intent: {intent_result.intent}")
            print(f"   Confidence: {intent_result.confidence}")
            print(f"   Cleansed input: {intent_result.cleansed_input}")
            
            # Check if we should continue after classification (same logic as original workflow)
            if self.intent_classification_service.should_continue_after_classification(intent_result) == "voice_generation":
                # Low confidence - go directly to voice generation (same as original workflow)
                response = await self.voice_generation_service.generate_voice_response(
                    response_text="I'm sorry, I didn't understand. Could you please try again?",
                    response_phrase_type=None,
                    restaurant_id=str(restaurant_id),
                    intent_confidence=intent_result.confidence
                )
                response["intent_type"] = intent_result.intent
                return response
            
            # Step 2: State Transition (state machine validation)
            print(f"\n🔍 STEP 2: State Transition")
            state_transition_result = await self.state_transition_service.validate_transition(
                current_state=ConversationState.ORDERING,  # Default state
                intent_type=intent_result.intent,
                session_id=session_id
            )
            
            # Check if we should continue after state transition (same logic as original workflow)
            if self.state_transition_service.should_continue_after_transition(state_transition_result) == "voice_generation":
                # No commands needed - use state machine response
                response_phrase_type = state_transition_result.get("response_phrase_type")
                
                # Get the proper text for the phrase type from audio constants
                from app.constants.audio_phrases import AudioPhraseConstants
                response_text = AudioPhraseConstants.get_phrase_text(response_phrase_type)
                
                response = await self.voice_generation_service.generate_voice_response(
                    response_text=response_text,
                    response_phrase_type=response_phrase_type,
                    restaurant_id=str(restaurant_id)
                )
                response["intent_type"] = intent_result.intent
                return response
            
            # Step 3: Intent Parser Router (route to correct parser)
            print(f"\n🔍 STEP 3: Intent Parser Router")
            # Get shared database session for command execution
            from app.core.database import AsyncSessionLocal
            shared_db_session = AsyncSessionLocal()
            print(f"   🔍 DEBUG - Orchestrator creating shared_db_session: {shared_db_session}")
            parser_result = await self.intent_parser_router_service.route_to_parser(
                intent_type=intent_result.intent,
                user_input=intent_result.cleansed_input,
                restaurant_id=str(restaurant_id),
                session_id=session_id,
                conversation_history=conversation_history or [],
                order_state=order_state or {},
                current_state="ORDERING",
                shared_db_session=shared_db_session
            )
            
            if not parser_result["success"]:
                return {
                    "response_text": parser_result["response_text"],
                    "audio_url": None,
                    "success": False,
                    "intent_type": intent_result.intent
                }
            
            # Step 4: Command Executor
            print(f"\n🔍 STEP 4: Command Executor")
            # Get shared database session from database module
            from app.core.database import AsyncSessionLocal
            shared_db_session = AsyncSessionLocal()
            command_result = await self.command_executor_service.execute_commands(
                commands=parser_result["commands"],
                session_id=session_id,
                restaurant_id=str(restaurant_id),
                shared_db_session=shared_db_session
            )
            
            # Check if we should continue after command execution (same logic as original workflow)
            if self.command_executor_service.should_continue_after_execution(command_result) == "final_response_aggregator":
                # Always go to response aggregator (same as original workflow)
                
                # Step 5: Response Aggregator
                print(f"\n🔍 STEP 5: Response Aggregator")
                aggregated_response = await self.response_aggregator_service.aggregate_response(
                    command_batch_result=command_result.get("command_batch_result"),
                    session_id=session_id,
                    restaurant_id=str(restaurant_id),
                    conversation_history=conversation_history or [],
                    order_state=order_state or {}
                )
                
                # Step 6: Voice Generation
                print(f"\n🔍 STEP 6: Voice Generation")
                final_response = await self.voice_generation_service.generate_voice_response(
                    response_text=aggregated_response["response_text"],
                    response_phrase_type=aggregated_response.get("response_phrase_type"),
                    restaurant_id=str(restaurant_id),
                    intent_confidence=intent_result.confidence
                )
                
                # Check if order was modified and set order_state_changed flag
                command_batch_result = command_result.get("command_batch_result")
                order_state_changed = False
                print(f"   🔍 DEBUG - Checking order state change:")
                print(f"     command_batch_result: {command_batch_result}")
                if command_batch_result:
                    print(f"     successful_commands: {command_batch_result.successful_commands}")
                    print(f"     command_family: {command_batch_result.command_family}")
                    # Check if any commands were successful and modified the order
                    order_modifying_commands = ["ADDITEM", "REMOVEITEM", "MODIFYITEM", "SETQUANTITY", "CLEARORDER"]
                    if (command_batch_result.successful_commands > 0 and 
                        command_batch_result.command_family in order_modifying_commands):
                        order_state_changed = True
                        print(f"   🔍 DEBUG - Order state changed: {command_batch_result.command_family} with {command_batch_result.successful_commands} successful commands")
                    else:
                        print(f"   🔍 DEBUG - Order state NOT changed: successful_commands={command_batch_result.successful_commands}, command_family={command_batch_result.command_family}")
                else:
                    print(f"   🔍 DEBUG - No command_batch_result found")
                
                # Add intent type and order state change flag to the response
                final_response["intent_type"] = intent_result.intent
                final_response["order_state_changed"] = order_state_changed
                return final_response
            else:
                # This shouldn't happen based on the original workflow logic
                return {
                    "response_text": "I'm sorry, I had trouble processing your request. Please try again.",
                    "audio_url": None,
                    "success": False,
                    "intent_type": intent_result.intent
                }
                
        except Exception as e:
            self.logger.error(f"Conversation orchestrator failed: {e}")
            print(f"❌ ORCHESTRATOR ERROR: {e}")
            return {
                "response_text": "I'm sorry, I'm having trouble processing your request. Please try again.",
                "audio_url": None,
                "success": False,
                "error": str(e),
                "intent_type": None
            }
