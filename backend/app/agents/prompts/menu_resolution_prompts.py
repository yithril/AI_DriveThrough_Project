"""
Prompts for Menu Resolution Agent
"""

def build_menu_resolution_prompt(extraction_response, restaurant_id: str) -> str:
    """
    Build the prompt for menu resolution.
    
    Args:
        extraction_response: Response from item extraction agent
        restaurant_id: Restaurant ID for context
        
    Returns:
        Formatted prompt string
    """
    
    # Build the extracted items list
    items_text = "Extracted items to resolve:\n"
    for i, item in enumerate(extraction_response.extracted_items):
        items_text += f"{i+1}. {item.item_name} (qty: {item.quantity}"
        if item.size:
            items_text += f", size: {item.size}"
        if item.modifiers:
            items_text += f", modifiers: {', '.join(item.modifiers)}"
        if item.special_instructions:
            items_text += f", instructions: {item.special_instructions}"
        items_text += f", confidence: {item.confidence})\n"
    
    prompt = f"""
You are a menu resolution assistant for restaurant ID {restaurant_id}.

{items_text}

RESOLUTION TASKS:
1. Use the search_menu_items tool to find matching menu items
2. Use get_menu_item_details to get full information about items
3. For each extracted item, try to find the best matching menu item
4. If multiple matches exist, provide suggestions
5. If no clear match exists, mark as ambiguous and provide suggestions

RESOLUTION RULES:
- Only return menu_item_id > 0 for items you're confident about
- Use menu_item_id = 0 for ambiguous items
- Provide suggested_options for ambiguous items
- Include clarification_question for ambiguous items
- Set confidence based on how certain you are about the match

CRITICAL: You must return your final response in this EXACT JSON format:

```json
{{
  "success": true,
  "confidence": 0.9,
  "resolved_items": [
    {{
      "item_name": "string",
      "quantity": 1,
      "size": "string | null",
      "modifiers": ["string"],
      "special_instructions": "string | null",
      "menu_item_id": 0,
      "resolved_name": "string | null",
      "is_ambiguous": false,
      "is_unavailable": false,
      "confidence": 0.9,
      "suggested_options": ["string"],
      "clarification_question": "string | null"
    }}
  ],
  "needs_clarification": false,
  "clarification_questions": ["string"]
}}
```

For items that are NOT FOUND on the menu:
- Set "menu_item_id": 0
- Set "is_ambiguous": false
- Set "is_unavailable": true
- Set "clarification_question": "Sorry, we don't have [item_name] on our menu"

For items that are AMBIGUOUS (multiple matches):
- Set "menu_item_id": 0
- Set "is_ambiguous": true
- Set "is_unavailable": false
- Set "suggested_options": ["list of matching items"]
- Set "clarification_question": "Which [item_name] would you like?"

For items that are CLEARLY RESOLVED:
- Set "menu_item_id": [actual_id]
- Set "is_ambiguous": false
- Set "is_unavailable": false
- Set "resolved_name": [actual menu name]

Return ONLY the JSON response, no additional text.
"""
    
    return prompt
