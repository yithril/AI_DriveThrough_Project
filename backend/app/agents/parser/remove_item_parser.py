"""
Remove Item Parser

LLM-based parser for REMOVE_ITEM intents that wraps the existing REMOVE_ITEM agent.
Extracts structured data from natural language input using OpenAI GPT-4.
"""

import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParserResult
from ...commands.intent_classification_schema import IntentType
from ...agents.command_agents.remove_item_agent import remove_item_agent_node
from ...agents.state import ConversationWorkflowState

logger = logging.getLogger(__name__)


class RemoveItemParser(BaseParser):
    """
    LLM-based parser for REMOVE_ITEM intents
    
    Wraps the existing REMOVE_ITEM agent to follow the standard parser pattern.
    """
    
    def __init__(self):
        super().__init__(IntentType.REMOVE_ITEM)
    
    async def parse(self, user_input: str, context: Dict[str, Any]) -> ParserResult:
        """
        Parse REMOVE_ITEM intent using the existing REMOVE_ITEM agent
        
        Args:
            user_input: Raw user input text
            context: Current conversation context
            
        Returns:
            ParserResult with structured command data
        """
        try:
            # Call the REMOVE_ITEM agent with the data it needs
            agent_response = await remove_item_agent_node(
                user_input=user_input,
                current_order_items=context.get("order_items", [])
            )
            
            # Convert agent response to command data
            if agent_response.items_to_remove:
                # For now, return the first item as the primary result
                first_item = agent_response.items_to_remove[0]
                
                # Check if this item is ambiguous (both order_item_id and target_ref are None)
                if first_item.order_item_id is None and first_item.target_ref is None:
                    # Create clarification command for ambiguous item
                    command_data = {
                        "intent": "CLARIFICATION_NEEDED",
                        "confidence": agent_response.confidence,
                        "slots": {
                            "ambiguous_item": first_item.ambiguous_item or "item",
                            "suggested_options": first_item.suggested_options or [],
                            "user_input": user_input,
                            "clarification_question": first_item.clarification_question
                        }
                    }
                else:
                    # Create normal REMOVE_ITEM command
                    command_data = {
                        "intent": "REMOVE_ITEM",
                        "confidence": agent_response.confidence,
                        "slots": {
                            "order_item_id": first_item.order_item_id,
                            "target_ref": first_item.target_ref,
                            "removal_reason": first_item.removal_reason
                        }
                    }
                
                logger.info(f"REMOVE_ITEM parser result: {command_data}")
                return ParserResult.success_result(command_data)
            else:
                logger.warning("REMOVE_ITEM agent returned no items to remove")
                return ParserResult.error_result("No items to remove found")
            
        except Exception as e:
            logger.error(f"REMOVE_ITEM parser failed: {e}")
            return ParserResult.error_result(f"REMOVE_ITEM parsing failed: {str(e)}")
    
    async def _resolve_target_item(self, user_input: str, context: Dict[str, Any]) -> int:
        """
        Resolve target item reference to order_item_id
        
        TODO: Use LLM to resolve:
        - "that burger" -> specific order item
        - "the fries" -> order item by description
        - "the one with extra cheese" -> order item by customization
        """
        # TODO: Implement target item resolution
        pass
    
    async def _extract_removal_reason(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Extract removal reason from user input
        
        TODO: Use LLM to extract:
        - Explicit reasons ("I don't want it", "Changed my mind")
        - Implicit reasons (context clues)
        """
        # TODO: Implement reason extraction
        pass
