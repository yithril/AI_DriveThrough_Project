"""
Prompts for Item Extraction Agent
"""

def build_item_extraction_prompt(user_input: str, conversation_history: list, order_state: dict, restaurant_id: str) -> str:
    """
    Build the prompt for item extraction.
    
    Args:
        user_input: The user's input text
        conversation_history: Recent conversation history
        order_state: Current order state
        restaurant_id: Restaurant ID for context
        
    Returns:
        Formatted prompt string
    """
    
    # Build conversation context
    history_text = ""
    if conversation_history:
        history_text = "Recent conversation:\n"
        for turn in conversation_history[-3:]:  # Last 3 turns
            if isinstance(turn, dict):
                user_msg = turn.get("user", "")
                ai_msg = turn.get("ai", "")
                if user_msg:
                    history_text += f"Customer: {user_msg}\n"
                if ai_msg:
                    history_text += f"Assistant: {ai_msg}\n"
    
    # Build order context
    order_text = ""
    if order_state and hasattr(order_state, 'line_items') and order_state.line_items:
        order_text = "Current order:\n"
        for item in order_state.line_items:
            order_text += f"- {item.get('name', 'Unknown item')} (qty: {item.get('quantity', 1)})\n"
    
    prompt = f"""
You are an AI assistant that extracts food items from customer orders at a drive-thru restaurant.

Your job is to extract:
1. Item names/descriptions (as mentioned by the customer)
2. Quantities (explicit numbers or implicit like "a burger" = 1)
3. Sizes (small, medium, large, etc.)
4. Modifiers (extra cheese, no pickles, etc.)
5. Special instructions (well done, rare, etc.)

{history_text}

{order_text}

Customer says: "{user_input}"

EXTRACTION RULES:
- Extract items exactly as the customer described them
- Don't try to resolve menu items or guess IDs
- If quantity is not specified, assume 1
- Capture all modifiers and special instructions
- If something is unclear, set confidence < 0.8
- If multiple items are mentioned, extract each separately

EXAMPLES:
"I want a Big Mac" → item_name: "Big Mac", quantity: 1, confidence: 0.9
"Two large fries" → item_name: "fries", quantity: 2, size: "large", confidence: 0.9
"A burger with no pickles" → item_name: "burger", quantity: 1, modifiers: ["no pickles"], confidence: 0.8
"I'll have the special" → item_name: "special", quantity: 1, confidence: 0.6 (unclear what special)

Return structured data with all extracted items.
"""
    
    return prompt
