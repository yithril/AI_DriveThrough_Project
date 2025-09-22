"""
Prompts for ADD_ITEM agent
"""

from langchain_core.prompts import PromptTemplate


def get_add_item_prompt(
    user_input: str,
    conversation_history: list,
    order_state: dict,
    menu_items: list,
    restaurant_info: dict
) -> str:
    """
    Get the prompt for ADD_ITEM agent
    
    Args:
        user_input: Normalized user input
        conversation_history: Recent conversation history
        order_state: Current order state
        menu_items: Available menu items
        restaurant_info: Restaurant information
        
    Returns:
        Formatted prompt string for the ADD_ITEM agent
    """
    
    # Format conversation history
    history_text = ""
    if conversation_history:
        history_lines = []
        for turn in conversation_history[-3:]:  # Last 3 turns
            if "user" in turn:
                history_lines.append(f"Customer: {turn['user']}")
            if "ai" in turn:
                history_lines.append(f"Assistant: {turn['ai']}")
        history_text = "\n".join(history_lines)
    
    # Format menu items by category
    menu_text = ""
    if menu_items:
        menu_lines = []
        for category, items in menu_items.items():
            menu_lines.append(f"{category}:")
            for item in items:
                menu_lines.append(f"  - {item}")
        menu_text = "\n".join(menu_lines)
    
    template = """You are an AI assistant for a drive-thru restaurant. Your job is to parse customer requests for adding items to their order and extract the specific items, quantities, sizes, and modifications they want.

FACTS:
- Restaurant: {restaurant_info}
- Available Menu Items:
{menu_text}
- Current Order: {order_state}
- Conversation History: {conversation_history}

INSTRUCTIONS:
1. **Parse the customer's request** to identify all items they want to add
2. **Extract quantities** (e.g., "two burgers" = quantity 2)
3. **Identify sizes** (e.g., "large", "medium", "small")
4. **Parse modifiers** (e.g., "extra cheese", "no pickles", "well done")
5. **Extract special instructions** (e.g., "cook it rare", "extra crispy")
6. **Handle multiple items** in one request (e.g., "I want a burger and fries")
7. **CRITICAL: Detect ambiguity** - If the customer mentions a generic term like "burger", "sandwich", "drink", "fries" and there are multiple options available, use menu_item_id=0 to signal ambiguity
8. **Be conservative** - When in doubt, use menu_item_id=0 rather than guessing

CONSTRAINTS:
- Only suggest items that are actually on the menu
- If an item is not found, use menu_item_id=0
- If size is not specified, use default size
- If quantity is not specified, assume 1

AMBIGUITY DETECTION RULES:
- If customer says "burger" and there are multiple burger types → use menu_item_id=0
- If customer says "sandwich" and there are multiple sandwich types → use menu_item_id=0  
- If customer says "drink" and there are multiple drink types → use menu_item_id=0
- If customer says "fries" and there are multiple fry types → use menu_item_id=0
- If customer says "salad" and there are multiple salad types → use menu_item_id=0
- ONLY use specific menu_item_id when the customer mentions the exact item name
- Always use response_type="success" and phrase_type="LLM_GENERATED" for parsing

TASK:
Parse this customer request: "{user_input}"

OUTPUT FORMAT:
Return a structured response with:
- response_type: "success" or "error"
- phrase_type: AudioPhraseType enum value
- response_text: Natural language response to customer
- confidence: 0.0 to 1.0 confidence in parsing
- items_to_add: List of ItemToAdd objects with menu_item_id, quantity, size, modifiers, special_instructions
- relevant_data: Additional context

EXAMPLES:

### Example 1: Simple single item
Customer: "I want a burger"
Response: {{
  "response_type": "success",
  "phrase_type": "LLM_GENERATED",
  "response_text": "I'll add a burger to your order.",
  "confidence": 0.95,
  "items_to_add": [{{"menu_item_id": 123, "quantity": 1, "size": null, "modifiers": [], "special_instructions": null}}],
  "relevant_data": {{}}
}}

### Example 2: Multiple items with modifiers
Customer: "I want two large burgers with extra cheese and a medium coke"
Response: {{
  "response_type": "success",
  "phrase_type": "LLM_GENERATED", 
  "response_text": "I'll add two large burgers with extra cheese and a medium coke to your order.",
  "confidence": 0.9,
  "items_to_add": [
    {{"menu_item_id": 123, "quantity": 2, "size": "large", "modifiers": ["extra cheese"], "special_instructions": null}},
    {{"menu_item_id": 456, "quantity": 1, "size": "medium", "modifiers": [], "special_instructions": null}}
  ],
  "relevant_data": {{}}
}}

### Example 3: Ambiguous item (multiple options available)
Customer: "I want two large burgers"
Available: Quantum Burger, Classic Burger, Chicken Burger
Response: {{
  "response_type": "success",
  "phrase_type": "LLM_GENERATED",
  "response_text": "I've noted two large burgers for your order.",
  "confidence": 0.8,
  "items_to_add": [{{"menu_item_id": 0, "quantity": 2, "size": "large", "modifiers": [], "special_instructions": null}}],
  "relevant_data": {{"suggested_items": ["Quantum Burger", "Classic Burger", "Chicken Burger"]}}
}}

### Example 4: Item not found
Customer: "I want a chocolate pie"
Response: {{
  "response_type": "success",
  "phrase_type": "LLM_GENERATED",
  "response_text": "I don't see chocolate pie on our menu, but I can add it to your order.",
  "confidence": 0.8,
  "items_to_add": [{{"menu_item_id": 0, "quantity": 1, "size": null, "modifiers": [], "special_instructions": null}}],
  "relevant_data": {{"suggested_alternatives": ["Apple Pie", "Cheesecake"]}}
}}

Return ONLY the JSON response. Do not include any other text."""

    # Create PromptTemplate with input variables
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["user_input", "conversation_history", "order_state", "menu_text", "restaurant_info"]
    )
    
    # Format the template with actual values
    return prompt_template.format(
        user_input=user_input,
        conversation_history=history_text,
        order_state=order_state,
        menu_text=menu_text,
        restaurant_info=restaurant_info
    )