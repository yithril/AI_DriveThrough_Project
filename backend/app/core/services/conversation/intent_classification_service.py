"""
Intent Classification Service

Pure intent detection - extracts what the human wants in a predictable format.
Does NOT validate against menu or state machine - just classifies intent.

Converted from intent_classifier_node.py to be a reusable service.
"""

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from app.commands.intent_classification_schema import IntentType, IntentClassificationResult
from app.agents.prompts.intent_classification_prompts import get_intent_classification_prompt
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings

logger = logging.getLogger(__name__)


class IntentClassificationService:
    """
    Service for classifying user intent using LLM with structured JSON output.
    
    Pure intent detection - extracts what human wants, doesn't validate against menu.
    Handles multiple items, messy input, and conversation context.
    """
    
    def __init__(self):
        """
        Initialize the intent classification service.
        """
        self.logger = logging.getLogger(__name__)
    
    async def classify_intent(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        order_state: Dict[str, Any],
        current_state: str = "ORDERING"
    ) -> IntentClassificationResult:
        """
        Classify user intent using LLM with structured JSON output.
        
        Args:
            user_input: Raw user input text
            conversation_history: Previous conversation turns
            order_state: Current order state
            current_state: Current conversation state
            
        Returns:
            IntentClassificationResult with intent, confidence, and cleansed input
        """
        try:
            # Build context for the LLM (last 3-5 conversation turns)
            context = {
                "user_input": user_input,
                "conversation_history": conversation_history[-5:],  # Last 5 turns
                "order_items": order_state.get("line_items", []),  # Fixed: match prompt template key
                "conversation_state": current_state,
                "last_mentioned_item": order_state.get("last_mentioned_item_ref")
            }
            
            # Get formatted prompt from the dedicated prompt file
            prompt = get_intent_classification_prompt(user_input, context)
            
            # Set up LangChain with function calling (more reliable than structured output)
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1  
            ).with_structured_output(IntentClassificationResult, method="function_calling")  
            
            # Execute with structured output
            result = await llm.ainvoke(prompt)
            self.logger.info(f"LLM parsed result: {result}")
            
            # DEBUG: Log the simplified result
            print(f"\n🔍 DEBUG - SIMPLIFIED AI RESPONSE:")
            print(f"   Intent: {result.intent}")
            print(f"   Confidence: {result.confidence}")
            print(f"   Cleansed Input: {result.cleansed_input}")
            print(f"   Result type: {type(result)}")
            
            self.logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence})")
            self.logger.info(f"Input cleansed: '{user_input}' → '{result.cleansed_input}'")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Intent classification failed: {e}")
            # Fallback to low confidence UNKNOWN
            fallback_result = IntentClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.1,
                cleansed_input=user_input  # Use original input when cleansing fails
            )
            self.logger.warning(f"Using original input as fallback: '{fallback_result.cleansed_input}'")
            return fallback_result
    
    def should_continue_after_classification(self, result: IntentClassificationResult) -> str:
        """
        Determine which step to go to next based on intent classification results.
        
        Args:
            result: Intent classification result
            
        Returns:
            Next step name: "state_transition" or "voice_generation"
        """
        # High confidence (≥0.8) → proceed to state machine validation
        if result.confidence >= 0.8:
            return "state_transition"
        
        # Low confidence (<0.8) → generate "didn't understand" response
        return "voice_generation"
