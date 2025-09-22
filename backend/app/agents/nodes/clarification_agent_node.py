"""
Clarification Agent Node

Handles complex conversation scenarios that require LLM processing.
Used when commands need clarification, error handling, or dynamic responses.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from app.agents.state import ConversationWorkflowState
from app.agents.agent_response import ClarificationResponse, ClarificationContext
from app.agents.prompts.clarification_prompts import get_clarification_prompt
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings

logger = logging.getLogger(__name__)


async def clarification_agent_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    Generate LLM-based clarification or error handling response using structured output.
    
    Args:
        state: Current conversation workflow state with command batch result
        context: LangGraph context containing services
        
    Returns:
        Updated state with response text and audio URL
    """
    try:
        # Get services from factory
        service_factory = config.get("configurable", {}).get("service_factory") if config else None
        
        if not service_factory:
            logger.error("Service factory not available")
            state.response_text = "I'm sorry, I'm having trouble processing your request. Please try again."
            state.audio_url = None
            return state
        
        voice_service = service_factory.create_voice_service()
        
        # Get shared database session from context
        shared_db_session = config.get("configurable", {}).get("shared_db_session")
        if not shared_db_session:
            logger.error("Shared database session not available")
            state.response_text = "I'm sorry, I'm having trouble processing your request. Please try again."
            state.audio_url = None
            return state
        
        menu_service = service_factory.create_menu_service(shared_db_session)
        
        if not voice_service:
            logger.error("Voice service not available")
            state.response_text = "I'm sorry, I'm having trouble with the audio system. Please try again."
            state.audio_url = None
            return state
        
        # Get the command batch result for context
        batch_result = state.command_batch_result
        
        if not batch_result:
            # No batch result - fallback response
            state.response_text = "I'm sorry, I didn't understand. Could you please try again?"
            state.response_phrase_type = AudioPhraseType.DIDNT_UNDERSTAND
            state.audio_url = await voice_service.generate_audio(
                phrase_type=AudioPhraseType.DIDNT_UNDERSTAND,
                restaurant_id=state.restaurant_id
            )
            return state
        
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
        
        # DEBUG: Show the prompt that was sent to AI
        print(f"\n📤 PROMPT SENT TO AI:")
        print(f"=" * 30)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        
        # Populate state with results
        state.response_text = result.response_text
        state.response_phrase_type = result.phrase_type
        state.custom_response_text = result.response_text if result.phrase_type == AudioPhraseType.LLM_GENERATED else None
        
        # Generate audio using the structured response
        audio_params = result.to_audio_params()
        state.audio_url = await voice_service.generate_audio(
            phrase_type=audio_params["phrase_type"],
            restaurant_id=state.restaurant_id,
            custom_text=audio_params.get("custom_text")
        )
        
        logger.info(f"Generated clarification response: {result.response_text[:100]}...")
        
    except Exception as e:
        logger.error(f"Clarification agent generation failed: {str(e)}")
        # Fallback response
        state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
        state.response_phrase_type = AudioPhraseType.ERROR_MESSAGE
        state.audio_url = None
    
    return state


async def _build_clarification_context(
    batch_result,
    state: ConversationWorkflowState,
    menu_service
) -> ClarificationContext:
    """
    Build clarification context from batch result and state.
    
    Args:
        batch_result: Command execution results
        state: Current workflow state
        container: Service container for menu access
        
    Returns:
        ClarificationContext with all necessary data
    """
    # Extract error details from batch result
    error_codes = list(batch_result.errors_by_code.keys()) if batch_result.errors_by_code else []
    failed_items = [result.message for result in batch_result.get_failed_results()]
    successful_items = [result.message for result in batch_result.get_successful_results()]
    
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
        available_items=available_items,
        similar_items={},  # Let AI figure out similarities from available_items
        conversation_history=state.conversation_history[-5:],  # Last 5 turns
        current_order_summary=order_summary,
        restaurant_name=restaurant_name
    )
    
    print(f"🔍 DEBUG - ClarificationContext:")
    print(f"   Available items: {context.available_items}")
    print(f"   Similar items: {context.similar_items}")
    print(f"   Restaurant name: {context.restaurant_name}")
    
    return context


def _build_order_summary(order_state) -> str:
    """Build a summary of the current order"""
    if not order_state.line_items:
        return "No items in order"
    
    items = []
    for item in order_state.line_items:
        items.append(f"{item.get('quantity', 1)}x {item.get('name', 'Unknown Item')}")
    
    return ", ".join(items)


def should_continue_after_clarification_agent(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after clarification agent.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "voice_generation" (generate audio for clarification response)
    """
    # Clarification responses need to be converted to audio
    return "voice_generation"
