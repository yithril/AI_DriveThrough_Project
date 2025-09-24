"""
Intent Parser Router Node

LangGraph node that routes classified intents to appropriate parsers.
This node takes the classified intent and routes it to the appropriate
rule-based parser to generate command data.
"""

from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.commands.intent_classification_schema import IntentType
from ..parser.base_parser import ParserResult
from ..parser.clear_order_parser import ClearOrderParser
from ..parser.confirm_order_parser import ConfirmOrderParser
from ..parser.question_parser import QuestionParser
from ..parser.unknown_parser import UnknownParser
from ..parser.add_item_parser import AddItemParser
from ..parser.remove_item_parser import RemoveItemParser
from ..parser.modify_item_parser import ModifyItemParser


class IntentParserRouter:
    """
    Router that dispatches classified intents to appropriate parsers.
    
    Maps intent types to their corresponding rule-based parsers
    and handles the parsing logic.
    """
    
    def __init__(self):
        """Initialize the router with all available parsers."""
        self.parsers = {
            IntentType.CLEAR_ORDER: ClearOrderParser(),
            IntentType.CONFIRM_ORDER: ConfirmOrderParser(),
            IntentType.QUESTION: QuestionParser(),
            IntentType.UNKNOWN: UnknownParser(),
            IntentType.ADD_ITEM: AddItemParser(),
            IntentType.REMOVE_ITEM: RemoveItemParser(),
            IntentType.MODIFY_ITEM: ModifyItemParser()
        }
    
    async def parse_intent(self, intent_type: IntentType, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Route intent to appropriate parser and return result.
        
        Args:
            intent_type: The classified intent type
            user_input: Original user input text
            context: Additional context (order state, conversation history, etc.)
            
        Returns:
            ParserResult with command data or error information
        """
        # Get the appropriate parser for this intent type
        parser = self.parsers.get(intent_type, self.parsers[IntentType.UNKNOWN])
        
        try:
            # Parse the intent using the selected parser
            result = await parser.parse(user_input, context)
            return result
        except Exception as e:
            # If parsing fails, fall back to unknown parser
            return await self.parsers[IntentType.UNKNOWN].parse(user_input, context)
    
    def get_supported_intents(self) -> list:
        """Get list of supported intent types."""
        return list(self.parsers.keys())


async def intent_parser_router_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    LangGraph node that routes classified intents to appropriate parsers.
    
    Takes the classified intent from the intent classifier and routes it
    to the appropriate rule-based parser to generate command data.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Updated state with command data for execution
    """
    # Create router instance
    router = IntentParserRouter()
    
    # Get service factory and shared database session from config
    service_factory = config.get("configurable", {}).get("service_factory") if config else None
    shared_db_session = config.get("configurable", {}).get("shared_db_session") if config else None
    
    # Build context for parsers
    context = {
        "order_items": state.order_state.line_items,
        "current_state": state.current_state.value,
        "conversation_history": state.conversation_history[-3:],  # Last 3 turns
        "last_mentioned_item": state.order_state.last_mentioned_item_ref,
        "restaurant_id": state.restaurant_id,
        "session_id": state.session_id,
        "service_factory": service_factory,  # Pass the factory to parsers
        "shared_db_session": shared_db_session  # Pass the shared session to parsers
    }
    
    # Route intent to appropriate parser
    result = await router.parse_intent(
        intent_type=state.intent_type,
        user_input=state.user_input,
        context=context
    )
    
    if result.success:
        # Store command data for command executor
        state.commands = [result.command_data]
        state.response_text = ""  # Will be set by command executor
        print(f"\n🔍 INTENT PARSER ROUTER - Commands created:")
        print(f"   Commands: {state.commands}")
    else:
        # Parser failed - route to canned response
        state.commands = []
        state.response_text = "I'm sorry, I didn't understand. Could you please try again?"
        print(f"\n❌ INTENT PARSER ROUTER - Parser failed: {result.error_message}")
    
    return state


def should_continue_after_intent_parser_router(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after intent parsing.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "command_executor"
    """
    # Always go to command executor - it will handle empty commands appropriately
    return "command_executor"
