"""
Simple intent classification prompts
"""

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate


def get_intent_classification_prompt(user_input: str, context: Dict[str, Any]) -> str:
    """
    Build the prompt for LLM intent classification using PromptTemplate
    
    Args:
        user_input: User's input text
        context: Conversation context
        
    Returns:
        Formatted prompt string ready for LangChain
    """
    
    template = """
You are an order taker at a drive-thru restaurant. Classify the user's intent and return JSON.

CONTEXT:
- Order items: {order_items}
- Conversation state: {conversation_state}
- Conversation history: {conversation_history}

USER INPUT: "{user_input}"

REQUIRED JSON FORMAT:
{{
  "intent": "INTENT_TYPE",
  "confidence": 0.95
}}

INTENT TYPES:
- ADD_ITEM: User wants to add food/drink items
- REMOVE_ITEM: User wants to remove specific items
- CLEAR_ORDER: User wants to remove all items
- MODIFY_ITEM: User wants to change item properties
- SET_QUANTITY: User wants to change quantity only
- CONFIRM_ORDER: User is done ordering ("that's it", "done", "that's all")
- REPEAT: User wants to repeat/add copy of existing items
- QUESTION: User asks questions about menu, prices, etc.
- SMALL_TALK: Greetings, thank you, general conversation
- UNKNOWN: Unclear or ambiguous intent

EXAMPLES:
"I'd like a Big Mac and fries" → {{"intent": "ADD_ITEM", "confidence": 0.95}}
"Remove my fries" → {{"intent": "REMOVE_ITEM", "confidence": 0.9}}
"That's all" → {{"intent": "CONFIRM_ORDER", "confidence": 0.95}}
"How much is a burger?" → {{"intent": "QUESTION", "confidence": 0.9}}
"Thank you" → {{"intent": "SMALL_TALK", "confidence": 0.95}}
"Can you repeat that?" → {{"intent": "REPEAT", "confidence": 0.85}}

EDGE CASE GUIDANCE:
- "Cancel my fries" → REMOVE_ITEM (not CLEAR_ORDER)
- "Clear the order" → CLEAR_ORDER
- "I’ll have what she’s having" → REPEAT
- "Is the shake large?" → QUESTION (not MODIFY_ITEM)
- "Make it two" following a referenced item → SET_QUANTITY for that item
- "No pickles" after a burger reference → MODIFY_ITEM for that item

NOISE FILTERING:
Ignore non-food-related speech and focus only on ordering intent.
Example: "I'd like two burgers... Shawn stop hitting your sister... with no pickles"
→ Focus on: "I'd like two burgers with no pickles"


CONFIDENCE SCORING:
- 0.9-1.0: Very clear intent
- 0.7-0.8: Clear intent with minor ambiguity
- 0.5-0.6: Somewhat unclear, needs context
- 0.0-0.4: Very unclear, should be UNKNOWN

Return ONLY the JSON response. Do not include any other text.
"""
    
    # Create PromptTemplate with input variables
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["user_input", "order_items", "conversation_state", "conversation_history"]
    )
    
    # Format the template with actual values
    return prompt_template.format(
        user_input=user_input,
        order_items=context.get('order_items', []),
        conversation_state=context.get('conversation_state', 'Ordering'),
        conversation_history=context.get('conversation_history', [])
    )
