"""
Simple intent classification prompts
"""

from typing import Dict, Any
import json
from ...commands.command_contract import get_command_contract_schema


def get_intent_classification_prompt(user_input: str, context: Dict[str, Any]) -> str:
    """
    Build the prompt for LLM intent classification
    
    Args:
        user_input: User's input text
        context: Conversation context
        
    Returns:
        Formatted prompt string
    """
    schema = get_command_contract_schema()
    
    prompt = f"""
You are a drive-thru restaurant AI. Classify the user's intent and return JSON.

CONTEXT:
- Order items: {context.get('order_items', [])}
- Conversation state: {context.get('conversation_state', 'Ordering')}

USER INPUT: "{user_input}"

Return JSON following this schema:
{json.dumps(schema, indent=2)}

INTENT RULES:
- ADD_ITEM: User wants to add food/drink
- REMOVE_ITEM: User wants to remove items (use target_ref: "last_item", "line_1", etc.)
- MODIFY_ITEM: User wants to change item properties
- SET_QUANTITY: User wants to change quantity
- CLEAR_ORDER: User wants to remove all items
- CONFIRM_ORDER: User is done ("that's it", "done")
- REPEAT: User wants to repeat/add copy
- QUESTION: User asks questions
- UNKNOWN: Unclear intent

TARGET REFERENCES:
- "last_item", "it", "that one" → "last_item"
- "line 1" → "line_1"
- "line 2" → "line_2"

MODIFIERS:
- "no pickles" → ["no_pickles"]
- "extra cheese" → ["extra_cheese"]
- "light ice" → ["light_ice"]

Return ONLY the JSON response.
"""
    return prompt
