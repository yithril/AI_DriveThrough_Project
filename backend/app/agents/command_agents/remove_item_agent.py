"""
REMOVE_ITEM Agent Node

LangGraph node that parses customer requests for removing items from their order.
Uses LLM with structured output to extract target references and removal details.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from app.agents.state import ConversationWorkflowState
from app.agents.agent_response.remove_item_response import RemoveItemResponse
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings

logger = logging.getLogger(__name__)


async def remove_item_agent_node(user_input: str, current_order_items: list) -> RemoveItemResponse:
    """
    REMOVE_ITEM agent node that parses customer requests for removing items from their order.
    
    Args:
        user_input: The user's input text
        current_order_items: List of items currently in the order
        
    Returns:
        RemoveItemResponse with parsed removal requests
    """
    try:
        # Set up LLM with structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        ).with_structured_output(RemoveItemResponse, method="function_calling")
        
        # Create structured prompt
        from app.agents.prompts.remove_item_prompts import get_remove_item_prompt
        
        prompt = get_remove_item_prompt(
            user_input=user_input,
            current_order_items=current_order_items
        )
        
        # Execute with structured output
        response = await llm.ainvoke(prompt)
        logger.info(f"LLM REMOVE_ITEM result: {response}")
        
        # DEBUG: Log the result
        print(f"\n🔍 DEBUG - REMOVE_ITEM AI RESPONSE:")
        print(f"   Confidence: {response.confidence}")
        print(f"   Items to remove: {len(response.items_to_remove)}")
        for i, item in enumerate(response.items_to_remove):
            print(f"     Item {i+1}: ID {item.order_item_id or 'None'} - {item.target_ref or 'None'}")
        
        logger.info(f"REMOVE_ITEM agent processed: {user_input}")
        logger.info(f"Parsed items: {[f'ID {item.order_item_id or item.target_ref}' for item in response.items_to_remove]}")
        
        return response
        
    except Exception as e:
        logger.error(f"REMOVE_ITEM agent failed: {e}")
        raise
