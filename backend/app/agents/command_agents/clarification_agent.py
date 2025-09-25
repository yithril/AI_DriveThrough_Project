"""
Clarification Agent Service

Handles complex conversation scenarios that require LLM processing.
Used when commands need clarification, error handling, or dynamic responses.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from app.agents.agent_response import ClarificationResponse, ClarificationContext
from app.agents.prompts.clarification_prompts import get_clarification_prompt
from app.core.config import settings

logger = logging.getLogger(__name__)


async def clarification_agent_service(
    batch_result,
    state,
    config = None
) -> ClarificationResponse:
    """
    Generate LLM-based clarification or error handling response using structured output.
    
    Args:
        batch_result: Command execution results
        state: Current conversation workflow state
        config: LangGraph config containing services
        
    Returns:
        ClarificationResponse with structured output
    """
    try:
        # Get services from factory
        service_factory = config.get("configurable", {}).get("service_factory") if config else None
        
        if not service_factory:
            logger.error("Service factory not available")
            return ClarificationResponse(
                response_type="statement",
                phrase_type="DIDNT_UNDERSTAND",
                response_text="I'm sorry, I'm having trouble processing your request. Please try again.",
                confidence=0.0
            )
        
        # Get shared database session from context
        shared_db_session = config.get("configurable", {}).get("shared_db_session")
        if not shared_db_session:
            logger.error("Shared database session not available")
            return ClarificationResponse(
                response_type="statement",
                phrase_type="DIDNT_UNDERSTAND",
                response_text="I'm sorry, I'm having trouble processing your request. Please try again.",
                confidence=0.0
            )
        
        menu_service = service_factory.create_menu_service(shared_db_session)
        
        # Build clarification context
        clarification_context = await _build_clarification_context(
            batch_result=batch_result,
            state=state,
            menu_service=menu_service
        )
        
        # Get formatted prompt
        prompt = get_clarification_prompt(batch_result, clarification_context)
        
        # Set up LangChain with structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        ).with_structured_output(ClarificationResponse, method="function_calling")
        
        # Execute with structured output
        result = await llm.ainvoke(prompt)
        logger.info(f"LLM clarification result: {result}")
        
        # DEBUG: Log the result
        print(f"\n🔍 DEBUG - CLARIFICATION AI RESPONSE:")
        print(f"   Response Type: {result.response_type}")
        print(f"   Phrase Type: {result.phrase_type}")
        print(f"   Text: {result.response_text}")
        print(f"   Confidence: {result.confidence}")
        
        return result
        
    except Exception as e:
        logger.error(f"Clarification agent service failed: {e}")
        return ClarificationResponse(
            response_type="statement",
            phrase_type="DIDNT_UNDERSTAND",
            response_text="I'm sorry, I had trouble processing your request. Please try again.",
            confidence=0.0
        )


async def _build_clarification_context(
    batch_result,
    state,
    menu_service
) -> ClarificationContext:
    """
    Build clarification context from batch result and state.
    
    Args:
        batch_result: Command execution results
        state: Current workflow state
        menu_service: Menu service for context
        
    Returns:
        ClarificationContext with all necessary data
    """
    # Extract error details from batch result
    error_codes = list(batch_result.errors_by_code.keys()) if batch_result.errors_by_code else []
    failed_items = [result.message for result in batch_result.get_failed_results()]
    successful_items = [result.message for result in batch_result.get_successful_results()]
    
    # Extract clarification data from batch result
    clarification_commands = []
    for result in batch_result.results:
        if (result.is_success and result.data and 
            result.data.get("clarification_type") == "ambiguous_item"):
            
            clarification_commands.append({
                "ambiguous_item": result.data.get("ambiguous_item"),
                "suggested_options": result.data.get("suggested_options", []),
                "user_input": result.data.get("user_input"),
                "clarification_question": result.data.get("clarification_question"),
                "needs_user_response": result.data.get("needs_user_response", True)
            })
    
    # Build order summary
    order_summary = _build_order_summary(state.order_state)
    
    # Get menu data using MenuService
    available_items = await menu_service.get_available_items_for_restaurant(int(state.restaurant_id))
    restaurant_name = await menu_service.get_restaurant_name(int(state.restaurant_id))
    
    context = ClarificationContext(
        batch_outcome=batch_result.batch_outcome,
        error_codes=[code.value for code in error_codes],
        failed_items=failed_items,
        successful_items=successful_items,
        clarification_commands=clarification_commands,
        current_order_summary=order_summary,
        available_items=available_items,
        restaurant_name=restaurant_name,
        conversation_history=state.conversation_history,
        similar_suggestions=[]
    )
    
    return context


def _build_order_summary(order_state: Dict[str, Any]) -> str:
    """
    Build a summary of the current order state.
    
    Args:
        order_state: Current order state dictionary
        
    Returns:
        Formatted order summary string
    """
    if not order_state or not order_state.get("items"):
        return "Your order is currently empty."
    
    items = order_state.get("items", [])
    if not items:
        return "Your order is currently empty."
    
    item_summaries = []
    for item in items:
        quantity = item.get("quantity", 1)
        name = item.get("name", "item")
        size = item.get("size")
        
        if size:
            item_summaries.append(f"{quantity} {size} {name}")
        else:
            item_summaries.append(f"{quantity} {name}")
    
    if len(item_summaries) == 1:
        return f"Your current order: {item_summaries[0]}."
    else:
        items_text = ", ".join(item_summaries[:-1]) + f" and {item_summaries[-1]}"
        return f"Your current order: {items_text}."
