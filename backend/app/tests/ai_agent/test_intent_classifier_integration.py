"""
Integration tests for AI agents that hit real LLM systems
"""

import sys
import os
import pytest
from pathlib import Path

# Add the app directory to the Python path for proper imports
app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from app.agents.nodes.intent_classifier import intent_classifier_node
from app.agents.state.conversation_state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState, OrderState, ConversationContext
from app.commands.command_contract import IntentType
from app.constants.audio_phrases import AudioPhraseType


class TestIntentClassifierIntegration:
    """Integration tests for intent classifier hitting real LLM"""
    
    @pytest.mark.asyncio
    async def test_multiple_items_happy_case(self):
        """
        Test the happy case: "I'd like a Big Mac, a medium fry, and a large sprite"
        This should classify as ADD_ITEM with multiple items in slots
        """
        # Create test state
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id=1,
            user_input="I'd like a Big Mac, a medium fry, and a large sprite",
            current_state=ConversationState.ORDERING,
            order_state=OrderState(
                line_items=[],
                last_mentioned_item_ref=None,
                totals={}
            ),
            conversation_context=ConversationContext(
                turn_counter=1,
                last_action_uuid=None,
                thinking_since=None,
                timeout_at=None,
                expectation="free_form_ordering"
            ),
            conversation_history=[],
            intent_type=None,
            intent_confidence=0.0,
            intent_slots={},
            transition_requires_command=False,
            transition_is_valid=True,
            response_phrase_type=None
        )
        
        # Call the intent classifier (hits real LLM)
        result_state = await intent_classifier_node(state)
        
        # Assertions
        assert result_state.intent_type == IntentType.ADD_ITEM
        assert result_state.intent_confidence >= 0.8  # Should be high confidence
        
        # Verify original text is preserved
        assert result_state.user_input == "I'd like a Big Mac, a medium fry, and a large sprite"
        
        print(f"✅ Intent classified successfully:")
        print(f"   Intent: {result_state.intent_type}")
        print(f"   Confidence: {result_state.intent_confidence}")
        print(f"   Original text preserved: {result_state.user_input}")
    
    @pytest.mark.asyncio
    async def test_environment_check(self):
        """
        Check if we have the required environment variables for LLM testing
        """
        from app.core.config import settings
        
        if not settings.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not set - skipping LLM integration test")
        
        print(f"✅ OpenAI API key found, proceeding with integration test")


if __name__ == "__main__":
    # Run a quick test
    import asyncio
    
    async def run_test():
        test = TestIntentClassifierIntegration()
        await test.test_environment_check()
        await test.test_multiple_items_happy_case()
    
    asyncio.run(run_test())
