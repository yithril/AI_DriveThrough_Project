"""
Intent Classifier Node

Pure intent detection - extracts what the human wants in a predictable format.
Does NOT validate against menu or state machine - just classifies intent.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from app.agents.state import ConversationWorkflowState
from app.commands.intent_classification_schema import IntentType, IntentClassificationResult
from app.agents.prompts.intent_classification_prompts import get_intent_classification_prompt
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings

logger = logging.getLogger(__name__)


async def intent_classifier_node(state: ConversationWorkflowState) -> ConversationWorkflowState:
    """
    Classify user intent using LLM with structured JSON output.
    
    Pure intent detection - extracts what human wants, doesn't validate against menu.
    Handles multiple items, messy input, and conversation context.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Updated state with intent classification results
    """
    try:
        # Build context for the LLM (last 3-5 conversation turns)
        context = {
            "user_input": state.user_input,
            "conversation_history": state.conversation_history[-5:],  # Last 5 turns
            "order_items": state.order_state.line_items,  # Fixed: match prompt template key
            "conversation_state": state.current_state.value,
            "last_mentioned_item": state.order_state.last_mentioned_item_ref
        }
        
        # Get formatted prompt from the dedicated prompt file
        prompt = get_intent_classification_prompt(state.user_input, context)
        
        # Set up LangChain with function calling (more reliable than structured output)
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1  
        ).with_structured_output(IntentClassificationResult, method="function_calling")  
        
        # Execute with structured output
        result = await llm.ainvoke(prompt)
        logger.info(f"LLM parsed result: {result}")
        
        # DEBUG: Log the simplified result
        print(f"\n🔍 DEBUG - SIMPLIFIED AI RESPONSE:")
        print(f"   Intent: {result.intent}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Cleansed Input: {result.cleansed_input}")
        print(f"   Result type: {type(result)}")
        
        # Populate state with results
        state.intent_type = result.intent
        state.intent_confidence = result.confidence
        # No more slots - the original text is preserved in state.user_input
        
        # Use the LLM's cleansed input for normalized_user_input
        state.normalized_user_input = result.cleansed_input
        
        logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence})")
        logger.info(f"Input cleansed: '{state.user_input}' → '{state.normalized_user_input}'")
        
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        # Fallback to low confidence UNKNOWN
        state.intent_type = IntentType.UNKNOWN
        state.intent_confidence = 0.1
        state.intent_slots = {}
        state.response_phrase_type = AudioPhraseType.DIDNT_UNDERSTAND
        # Set normalized input as fallback (use original input when cleansing fails)
        state.normalized_user_input = state.user_input
        logger.warning(f"Using original input as fallback: '{state.normalized_user_input}'")
    
    # Final check for low confidence intents (covers both LLM low confidence and parse errors)
    if state.intent_confidence < 0.8:
        state.intent_type = IntentType.UNKNOWN
        state.response_phrase_type = AudioPhraseType.DIDNT_UNDERSTAND
    
    return state


def should_continue_after_intent_classifier(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next based on intent classification results.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "state_transition" or "voice_generation"
    """
    # High confidence (≥0.8) → proceed to state machine validation
    if state.intent_confidence >= 0.8:
        return "state_transition"
    
    # Low confidence (<0.8) → generate "didn't understand" response
    return "voice_generation"
