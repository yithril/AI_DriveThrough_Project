"""
Add Item Parser

LLM-based parser for ADD_ITEM intents that wraps the existing ADD_ITEM agent.
Extracts structured data from natural language input using OpenAI GPT-4.
"""

import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from ...commands.intent_classification_schema import IntentType
from ...agents.command_agents.add_item_agent import add_item_agent
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
            
            # Call the AddItemAgent to get structured response
            from app.agents.command_agents.add_item_agent import add_item_agent
            
            # Create context for the agent
            agent_context = {
                "service_factory": context.get("service_factory"),
                "shared_db_session": context.get("shared_db_session"),
                "conversation_history": state.conversation_history,
                "order_state": state.order_state.__dict__ if state.order_state else {},
                "restaurant_id": state.restaurant_id
            }
            
            # Call the agent to get structured response
            agent_result = await add_item_agent(state.normalized_user_input, agent_context)
            
            # Extract the structured response from the agent
            if agent_result and hasattr(agent_result, 'items_to_add'):
                response = agent_result
                commands = []
                
                # Create commands from the structured data
                for item in response.items_to_add:
                    if item.menu_item_id == 0:
                        # Ambiguous item - create CLARIFICATION_NEEDED command
                        command_data = {
                            "intent": "CLARIFICATION_NEEDED",
                            "confidence": response.confidence,
                            "slots": {
                                "ambiguous_item": item.ambiguous_item,
                                "suggested_options": item.suggested_options,
                                "clarification_question": item.clarification_question
                            }
                        }
                    else:
                        # Clear item - create ADD_ITEM command
                        command_data = {
                            "intent": "ADD_ITEM",
                            "confidence": response.confidence,
                            "slots": {
                                "menu_item_id": item.menu_item_id,
                                "quantity": item.quantity,
                                "size": item.size,
                                "modifiers": item.modifiers,
                                "special_instructions": item.special_instructions
                            }
                        }
                    
                    # Validate the command structure
                    from app.commands.command_data_validator import CommandDataValidator
                    is_valid, errors = CommandDataValidator.validate(command_data)
                    
                    if is_valid:
                        commands.append(command_data)
                        logger.info(f"Valid command created: {command_data['intent']}")
                    else:
                        logger.warning(f"Invalid command structure: {errors}")
                
                if commands:
                    logger.info(f"ADD_ITEM parser created {len(commands)} valid commands")
                    # Return all commands
                    return ParserResult.success_result(commands)
                else:
                    logger.warning("No valid commands could be created from agent response")
                    return ParserResult.error_result("No valid commands generated from agent response")
            else:
                logger.warning("ADD_ITEM agent returned no structured response")
                return ParserResult.error_result("No structured response from ADD_ITEM agent")
            
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
