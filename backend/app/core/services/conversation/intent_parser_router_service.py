"""
Intent Parser Router Service

Routes classified intents to appropriate parsers.
This service takes the classified intent and routes it to the appropriate
rule-based parser to generate command data.

Converted from intent_parser_router_node.py to be a reusable service.
"""

import logging
from typing import Dict, Any, List
from app.commands.intent_classification_schema import IntentType
from app.agents.parser.base_parser import ParserResult
from app.agents.parser.clear_order_parser import ClearOrderParser
from app.agents.parser.confirm_order_parser import ConfirmOrderParser
from app.agents.parser.question_parser import QuestionParser
from app.agents.parser.unknown_parser import UnknownParser
from app.agents.parser.add_item_parser import AddItemParser
from app.agents.parser.remove_item_parser import RemoveItemParser
from app.agents.parser.modify_item_parser import ModifyItemParser

logger = logging.getLogger(__name__)


class IntentParserRouterService:
    """
    Service that routes classified intents to appropriate parsers.
    
    Maps intent types to their corresponding rule-based parsers
    and handles the parsing logic.
    """
    
    def __init__(self):
        """
        Initialize the router service with all available parsers.
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize parsers
        self.parsers = {
            IntentType.CLEAR_ORDER: ClearOrderParser(),
            IntentType.CONFIRM_ORDER: ConfirmOrderParser(),
            IntentType.QUESTION: QuestionParser(),
            IntentType.UNKNOWN: UnknownParser(),
            IntentType.ADD_ITEM: AddItemParser(),
            IntentType.REMOVE_ITEM: RemoveItemParser(),
            IntentType.MODIFY_ITEM: ModifyItemParser()
        }
    
    def _build_parser_context(
        self,
        intent_type: IntentType,
        user_input: str,
        restaurant_id: str,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        order_state: Dict[str, Any],
        current_state: str = "ORDERING",
        shared_db_session = None
    ) -> Dict[str, Any]:
        """
        Build context specific to what each parser needs based on intent type.
        
        Args:
            intent_type: The classified intent type
            user_input: Normalized user input
            restaurant_id: Restaurant identifier
            session_id: Session identifier
            conversation_history: Previous conversation turns
            order_state: Current order state
            current_state: Current conversation state
            
        Returns:
            Context dictionary with only the data the parser needs
        """
        # Base context that all parsers need
        base_context = {
            "user_input": user_input,
            "restaurant_id": restaurant_id,
            "session_id": session_id
        }
        
        # Add intent-specific data
        if intent_type == IntentType.ADD_ITEM:
            # AddItemParser needs full context for menu resolution and order state
            print(f"   🔍 DEBUG - _build_parser_context for ADD_ITEM:")
            print(f"   shared_db_session: {shared_db_session}")
            
            # Create menu service for this parser
            from app.services.menu_service import MenuService
            menu_service = MenuService(shared_db_session)
            
            return {
                **base_context,
                "shared_db_session": shared_db_session,
                "conversation_history": conversation_history,
                "order_state": order_state,
                "current_state": current_state,
                "menu_service": menu_service
            }
        
        elif intent_type == IntentType.REMOVE_ITEM:
            # RemoveItemParser needs order state for item references
            return {
                **base_context,
                "order_state": order_state,
                "conversation_history": conversation_history[-3:],  # Last 3 turns
                "last_mentioned_item": order_state.get("last_mentioned_item_ref")
            }
        
        elif intent_type == IntentType.MODIFY_ITEM:
            # ModifyItemParser needs order state and conversation history
            return {
                **base_context,
                "order_state": order_state,
                "conversation_history": conversation_history[-3:],
                "last_mentioned_item": order_state.get("last_mentioned_item_ref")
            }
        
        elif intent_type == IntentType.QUESTION:
            # QuestionParser needs restaurant context and menu access
            return {
                **base_context,
                "conversation_history": conversation_history[-3:]
            }
        
        elif intent_type in [IntentType.CLEAR_ORDER, IntentType.CONFIRM_ORDER]:
            # Simple parsers that don't need much context
            return {
                **base_context,
                "order_state": order_state  # Just need to know if there's an order
            }
        
        else:
            # Unknown or other intents - minimal context
            return {
                **base_context,
                "conversation_history": conversation_history[-3:]
            }
    
    async def route_to_parser(
        self,
        intent_type: IntentType,
        user_input: str,
        restaurant_id: str,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        order_state: Dict[str, Any],
        current_state: str = "ORDERING",
        shared_db_session = None
    ) -> Dict[str, Any]:
        """
        Route intent to appropriate parser and return result.
        
        Args:
            intent_type: The classified intent type
            user_input: Normalized user input
            restaurant_id: Restaurant identifier
            session_id: Session identifier
            conversation_history: Previous conversation turns
            order_state: Current order state
            current_state: Current conversation state
            
        Returns:
            Dictionary with parsing results and commands
        """
        try:
            # Debug: Show input transformation
            print(f"\n🔍 INTENT PARSER ROUTER - Input transformation:")
            print(f"   Original: '{user_input}'")
            print(f"   Intent: {intent_type}")
            
            # Build context specific to what each parser needs
            parser_context = self._build_parser_context(
                intent_type=intent_type,
                user_input=user_input,
                restaurant_id=restaurant_id,
                session_id=session_id,
                conversation_history=conversation_history,
                order_state=order_state,
                current_state=current_state,
                shared_db_session=shared_db_session
            )
            
            # Debug: Show what context the parser will receive
            print(f"   Parser context keys: {list(parser_context.keys())}")
            if "order_state" in parser_context:
                print(f"   Order items: {len(parser_context['order_state'].get('line_items', []))}")
            if "conversation_history" in parser_context:
                print(f"   Conversation history: {len(parser_context['conversation_history'])} turns")
            if "shared_db_session" in parser_context:
                print(f"   DB session in context: {parser_context['shared_db_session']}")
            else:
                print(f"   ❌ No shared_db_session in parser context!")
            
            # Get the appropriate parser for this intent type
            parser = self.parsers.get(intent_type, self.parsers[IntentType.UNKNOWN])
            
            # Parse the intent using the selected parser
            result = await parser.parse(user_input, parser_context)
            
            if result.success:
                # Handle both single commands and multiple commands
                if result.is_multiple_commands():
                    commands = result.get_commands_list()
                    print(f"\n🔍 INTENT PARSER ROUTER - Multiple commands created:")
                    print(f"   Commands count: {len(commands)}")
                    for i, cmd in enumerate(commands):
                        print(f"     Command {i+1}: {cmd.get('intent', 'UNKNOWN')}")
                else:
                    commands = [result.command_data]
                    print(f"\n🔍 INTENT PARSER ROUTER - Single command created:")
                    print(f"   Command: {result.command_data.get('intent', 'UNKNOWN')}")
                
                return {
                    "success": True,
                    "commands": commands,
                    "response_text": ""  # Will be set by command executor
                }
            else:
                # Parser failed - return error
                print(f"\n❌ INTENT PARSER ROUTER - Parser failed: {result.error_message}")
                return {
                    "success": False,
                    "commands": [],
                    "response_text": "I'm sorry, I didn't understand. Could you please try again?",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Intent parser router failed: {e}")
            # If parsing fails, fall back to unknown parser
            try:
                fallback_result = await self.parsers[IntentType.UNKNOWN].parse(user_input, {
                    "user_input": user_input,
                    "restaurant_id": restaurant_id,
                    "session_id": session_id,
                    "conversation_history": conversation_history[-3:]
                })
                
                if fallback_result.success:
                    return {
                        "success": True,
                        "commands": [fallback_result.command_data] if not fallback_result.is_multiple_commands() else fallback_result.get_commands_list(),
                        "response_text": ""
                    }
                else:
                    return {
                        "success": False,
                        "commands": [],
                        "response_text": "I'm sorry, I didn't understand. Could you please try again?",
                        "error": str(e)
                    }
            except Exception as fallback_error:
                self.logger.error(f"Fallback parser also failed: {fallback_error}")
                return {
                    "success": False,
                    "commands": [],
                    "response_text": "I'm sorry, I didn't understand. Could you please try again?",
                    "error": str(e)
                }
    
    def get_supported_intents(self) -> List[IntentType]:
        """Get list of supported intent types."""
        return list(self.parsers.keys())
