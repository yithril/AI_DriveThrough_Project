"""
Add Item Parser

Parser for ADD_ITEM intents that uses the new two-agent pipeline:
1. Item Extraction Agent - extracts items from user input
2. Menu Resolution Agent - resolves items against menu database
"""

import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from ...commands.intent_classification_schema import IntentType
from ...commands.command_type_schema import CommandType
from ...constants.parser_messages import ParserMessages
from ...agents.command_agents.item_extraction_agent import item_extraction_agent
from ...agents.command_agents.menu_resolution_agent import menu_resolution_agent

logger = logging.getLogger(__name__)


class AddItemParser(BaseParser):
    """
    Parser for ADD_ITEM intents using the new two-agent pipeline
    
    Uses:
    1. Item Extraction Agent - extracts items from user input
    2. Menu Resolution Agent - resolves items against menu database
    """
    
    def __init__(self):
        super().__init__(IntentType.ADD_ITEM)
    
    async def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse ADD_ITEM intent using the two-agent pipeline
        
        Args:
            user_input: Raw user input text
            context: Current conversation context
            
        Returns:
            ParserResult with structured command data
        """
        try:
            # Step 1: Extract items from user input using Item Extraction Agent
            extraction_context = {
                "restaurant_id": context.get("restaurant_id"),
                "conversation_history": context.get("conversation_history", []),
                "order_state": context.get("order_state", {})
            }
            
            extraction_response = await item_extraction_agent(user_input, extraction_context)
            
            if not extraction_response.success:
                logger.warning("Item extraction failed")
                return ParserResult.error_result(ParserMessages.EXTRACTION_FAILED)
            
            # Step 2: Resolve items against menu using Menu Resolution Agent
            resolution_context = {
                "menu_service": context.get("menu_service"),
                "shared_db_session": context.get("shared_db_session"),
                "restaurant_id": context.get("restaurant_id")
            }
            
            resolution_response = await menu_resolution_agent(extraction_response, resolution_context)
            
            if not resolution_response.success:
                logger.warning("Menu resolution failed")
                return ParserResult.error_result(ParserMessages.RESOLUTION_FAILED)
            
            # Step 3: Convert resolved items to commands
            commands = []
            
            for resolved_item in resolution_response.resolved_items:
                if resolved_item.menu_item_id == 0 and not resolved_item.is_ambiguous:
                    # Item not found - create ITEM_UNAVAILABLE command
                    command_data = {
                        "intent": CommandType.ITEM_UNAVAILABLE.value,
                        "confidence": resolution_response.confidence,
                        "slots": {
                            "requested_item": resolved_item.item_name,
                            "message": ParserMessages.ITEM_UNAVAILABLE_TEMPLATE.format(item_name=resolved_item.item_name)
                        }
                    }
                elif resolved_item.is_ambiguous or resolved_item.menu_item_id == 0:
                    # Ambiguous item - create CLARIFICATION_NEEDED command
                    command_data = {
                        "intent": CommandType.CLARIFICATION_NEEDED.value,
                        "confidence": resolution_response.confidence,
                        "slots": {
                            "ambiguous_item": resolved_item.item_name,
                            "suggested_options": resolved_item.suggested_options,
                            "clarification_question": resolved_item.clarification_question
                        }
                    }
                else:
                    # Clear item - create ADD_ITEM command
                    command_data = {
                        "intent": CommandType.ADD_ITEM.value,
                        "confidence": resolution_response.confidence,
                        "slots": {
                            "menu_item_id": resolved_item.menu_item_id,
                            "quantity": resolved_item.quantity,
                            "size": resolved_item.size,
                            "modifiers": resolved_item.modifiers,
                            "special_instructions": resolved_item.special_instructions
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
                # Always return multiple commands (even for single items) for consistency
                logger.info(f"Commands created: {[cmd['intent'] for cmd in commands]}")
                return ParserResult.success_multiple_commands(commands)
            else:
                logger.warning("No valid commands could be created from agent responses")
                return ParserResult.error_result(ParserMessages.NO_COMMANDS_GENERATED)
            
        except Exception as e:
            logger.error(f"ADD_ITEM parser failed: {e}")
            return ParserResult.error_result(ParserMessages.PARSING_FAILED.format(error=str(e)))
