"""
Clarification Agent Prompts

Prompts for the clarification agent that handles order issues and suggests alternatives.
Uses separated facts/instructions structure for clear LLM guidance.
"""

from typing import Dict, Any, List
from app.agents.agent_response import ClarificationContext
from app.dto.order_result import CommandBatchResult


def get_clarification_prompt(
    batch_result: CommandBatchResult,
    context: ClarificationContext
) -> str:
    """
    Generate the main clarification prompt with separated facts and instructions.
    
    Args:
        batch_result: Command execution results
        context: Clarification context with menu and conversation data
        
    Returns:
        Formatted prompt string for LLM
    """
    
    from langchain_core.prompts import PromptTemplate
    
    template = """You are a helpful drive-thru assistant specializing in order clarification and customer service.

FACTS:

CONTEXT:
- Restaurant: {restaurant_name}
- Current Order: {current_order_summary}
- Conversation History: {conversation_history}

COMMAND RESULTS:
- Batch Outcome: {batch_outcome}
- Error Codes: {error_codes}
- Failed Items: {failed_items}
- Success Items: {success_items}

MENU CONTEXT:
- Available Items by Category: {menu_items_by_category}
- Similar Suggestions: {similar_suggestions}

INSTRUCTIONS:
- Never invent menu items. Only use items listed in MENU CONTEXT.
- When an item is not found, suggest similar alternatives from the available menu.
- Look for items that are similar in type (e.g., if "chocolate pie" is not found, suggest "apple pie" or "cheesecake").
- For quantity limits or unreasonable requests, be matter-of-fact and don't suggest alternatives unless they make sense.
- If no similar items exist, ask an open-ended clarifying question.
- Always keep responses to 1–2 sentences.
- If items were successfully added, acknowledge them first before addressing failures.
- For missing sizes/options, list only the actual available options from MENU CONTEXT.
- Use a friendly, sales-oriented tone that encourages ordering.
- Avoid repeating the same clarification question from conversation history.

CONSTRAINTS:
- Do not make up menu items, sizes, or modifications not in MENU CONTEXT.
- Do not offer unavailable sizes or options.
- Do not ask multiple questions in one response.
- Do not reference technical error codes in customer-facing text.
- Do not use technical terms like "batch_result", "validation", or "database".

TASK:
Generate a helpful clarification response that resolves the ordering issue and guides the customer toward a successful order.

EXAMPLES:
- If customer wants "chocolate pie" but it's not available, and you have "apple pie" and "cheesecake" on the menu, say: "We don't have chocolate pie, but we do have apple pie and cheesecake. Would you like one of those instead?"
- If customer wants "large burger" but only "medium" is available, say: "We don't have large burgers, but we do have medium burgers. Would you like a medium burger instead?"
- If customer wants something completely unavailable, say: "We don't have [item], but we do have [similar items]. Would you like to try one of those?"
- If customer wants an unreasonable quantity (like 10,000 items), say: "We can't do that many. How many would you like?" (Don't suggest alternatives unless they make sense)

OUTPUT FORMAT:
Respond with a JSON object matching this exact structure:
{{
  "response_type": "question" or "statement",
  "phrase_type": "CLARIFICATION_QUESTION", "CUSTOM_RESPONSE", or "LLM_GENERATED",
  "response_text": "Your helpful response here (10-200 characters)",
  "confidence": 0.95
}}

RESPONSE TYPE RULES:
- Use "question" when you need more information from the customer
- Use "statement" when you're providing information or confirming something

PHRASE TYPE RULES:
- Use "CLARIFICATION_QUESTION" for questions that need customer input
- Use "CUSTOM_RESPONSE" for statements that provide information
- Use "LLM_GENERATED" for complex responses that need custom text

CONFIDENCE RULES:
- Use 0.9+ for clear, confident responses
- Use 0.7-0.8 for responses with some uncertainty
- Never use below 0.5

Return ONLY the JSON response. Do not include any other text."""

    # Create PromptTemplate with input variables
    prompt_template = PromptTemplate(
        template=template,
        input_variables=[
            "restaurant_name", "current_order_summary", "conversation_history",
            "batch_outcome", "error_codes", "failed_items", "success_items",
            "menu_items_by_category", "similar_suggestions"
        ]
    )
    
    # Format the template with actual values
    return prompt_template.format(
        restaurant_name=context.restaurant_name,
        current_order_summary=context.current_order_summary,
        conversation_history=_format_conversation_history(context.conversation_history),
        batch_outcome=batch_result.batch_outcome,
        error_codes=', '.join(context.error_codes) if context.error_codes else 'None',
        failed_items=', '.join(context.failed_items) if context.failed_items else 'None',
        success_items=', '.join(context.successful_items) if context.successful_items else 'None',
        menu_items_by_category=_organize_menu_by_category(context.available_items),
        similar_suggestions=_build_similar_suggestions(context, context.failed_items)
    )


def _organize_menu_by_category(available_items: List[str]) -> str:
    """Organize menu items by category for better context"""
    if not available_items:
        return "No menu items available"
    
    # For now, just list all items since we don't have category data in the simple list
    # In a full implementation, you'd pass the actual menu items with categories
    # and organize them properly by category name
    
    # Limit to first 20 items to keep prompt manageable
    limited_items = available_items[:20]
    
    if len(available_items) > 20:
        return f"Available items: {', '.join(limited_items)} (and {len(available_items) - 20} more)"
    else:
        return f"Available items: {', '.join(limited_items)}"


def _build_similar_suggestions(context: ClarificationContext, failed_items: List[str]) -> str:
    """Build similar item suggestions for failed items"""
    if not failed_items:
        return "None"
    
    suggestions = []
    for item in failed_items[:3]:  # Limit to 3 failed items
        item_suggestions = context.get_failed_item_suggestions(item)
        if item_suggestions:
            suggestions.append(f"{item} → {', '.join(item_suggestions)}")
    
    return "; ".join(suggestions) if suggestions else "No similar items found"


def _format_conversation_history(history: List[Dict[str, Any]]) -> str:
    """Format conversation history for the prompt"""
    if not history:
        return "No previous conversation"
    
    # Take last 3 turns
    recent_turns = history[-3:]
    formatted_turns = []
    
    for turn in recent_turns:
        user_input = turn.get('user_input', '')
        response_text = turn.get('response_text', '')
        if user_input and response_text:
            formatted_turns.append(f"Customer: {user_input} | Assistant: {response_text}")
    
    return "; ".join(formatted_turns)


def get_clarification_context_builder() -> str:
    """
    Get instructions for building clarification context.
    Used by the clarification agent to gather necessary data.
    """
    return """
    To build effective clarification context, gather:
    
    1. BATCH RESULT DATA:
       - batch_outcome (ALL_SUCCESS, PARTIAL_SUCCESS_ASK, ALL_FAILED, etc.)
       - error_codes (ITEM_NOT_FOUND, SIZE_NOT_AVAILABLE, etc.)
       - failed_items (specific items that couldn't be added)
       - successful_items (items that were added successfully)
    
    2. MENU CONTEXT:
       - available_items (all menu items by category)
       - similar_items (mapping of failed items to alternatives)
    
    3. CONVERSATION CONTEXT:
       - conversation_history (last 3-5 turns)
       - current_order_summary (what's currently in the order)
       - restaurant_name (for personalized responses)
    
    4. ERROR ANALYSIS:
       - Check if we've asked for clarification recently
       - Identify the most common error types
       - Determine if we need alternatives or just clarification
    """
