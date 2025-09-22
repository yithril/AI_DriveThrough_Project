"""
Add Item Parser

LLM-based parser for ADD_ITEM intents that wraps the existing ADD_ITEM agent.
Extracts structured data from natural language input using OpenAI GPT-4.
"""

import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from ...commands.intent_classification_schema import IntentType
from ...agents.command_agents.add_item_agent import add_item_agent_node
from ...agents.state import ConversationWorkflowState

logger = logging.getLogger(__name__)


class AddItemParser(BaseParser):
    """
    LLM-based parser for ADD_ITEM intents
    
    Wraps the existing ADD_ITEM agent to follow the standard parser pattern.
    """
    
    def __init__(self):
        super().__init__(IntentType.ADD_ITEM)
    
    async def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse ADD_ITEM intent using the existing ADD_ITEM agent
        
        Args:
            user_input: Raw user input text
            context: Current conversation context
            
        Returns:
            ParserResult with structured command data
        """
        try:
            # Create a mock state for the agent
            from app.models.state_machine_models import OrderState
            
            # Create proper OrderState object
            order_items = context.get("order_items", [])
            order_state = OrderState(
                line_items=order_items,
                last_mentioned_item_ref=None,
                totals={}
            )
            
            state = ConversationWorkflowState(
                session_id=context.get("session_id", "test"),
                restaurant_id=str(context.get("restaurant_id", 1)),
                user_input=user_input,
                normalized_user_input=user_input,
                conversation_history=context.get("conversation_history", []),
                order_state=order_state,
                current_state=context.get("current_state", "IDLE")
            )
            
            # Create context for the agent with service factory and shared session
            agent_context = {
                "service_factory": context.get("service_factory"),  # Pass through service factory
                "shared_db_session": context.get("shared_db_session")  # Pass through shared session
            }
            
            # Call the existing ADD_ITEM agent
            result_state = await add_item_agent_node(state, agent_context)
            
            # Extract command data from the agent's result
            if result_state.commands:
                # The agent creates multiple commands, we need to handle that
                # For now, return the first command as the primary result
                command_data = result_state.commands[0]
                
                logger.info(f"ADD_ITEM parser result: {command_data}")
                return ParserResult.success_result(command_data)
            else:
                logger.warning("ADD_ITEM agent returned no commands")
                return ParserResult.error_result("No commands generated from ADD_ITEM agent")
            
        except Exception as e:
            logger.error(f"ADD_ITEM parser failed: {e}")
            return ParserResult.error_result(f"ADD_ITEM parsing failed: {str(e)}")
    
    async def _extract_customizations(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract customization information from user input
        
        TODO: Use LLM to extract:
        - Ingredient modifications (add/remove/substitute)
        - Cooking preferences (temperature, doneness)
        - Special instructions
        - Allergen considerations
        """
        # TODO: Implement customization extraction
        pass
    
    async def _resolve_menu_item(self, user_input: str, context: Dict[str, Any]) -> int:
        """
        Resolve menu item reference to menu_item_id
        
        TODO: Use LLM to resolve:
        - Ambiguous references ("that burger", "the special")
        - Partial names ("big mac", "quarter pounder")
        - Descriptions ("the one with bacon")
        """
        # TODO: Implement menu item resolution
        pass
    
    async def _extract_quantity(self, user_input: str, context: Dict[str, Any]) -> int:
        """
        Extract quantity from user input
        
        TODO: Use LLM to extract:
        - Explicit numbers ("two burgers")
        - Implicit quantities ("a burger" = 1)
        - Complex expressions ("a couple of", "a few")
        """
        # TODO: Implement quantity extraction
        pass
