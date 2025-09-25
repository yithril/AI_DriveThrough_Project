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

from app.agents.nodes.intent_classifier_node import intent_classifier_node
from app.agents.state.conversation_state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState, OrderState, ConversationContext
from app.commands.intent_classification_schema import IntentType
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
        
        # Verify cleansed input is populated
        assert result_state.normalized_user_input is not None
        assert len(result_state.normalized_user_input) > 0
        
        print(f"✅ Intent classified successfully:")
        print(f"   Intent: {result_state.intent_type}")
        print(f"   Confidence: {result_state.intent_confidence}")
        print(f"   Original text: {result_state.user_input}")
        print(f"   Cleansed input: {result_state.normalized_user_input}")
    
    @pytest.mark.asyncio
    async def test_environment_check(self):
        """
        Check if we have the required environment variables for LLM testing
        """
        from app.core.config import settings
        
        if not settings.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not set - skipping LLM integration test")
        
        print(f"✅ OpenAI API key found, proceeding with integration test")
    
    @pytest.mark.asyncio
    async def test_noisy_input_cleansing(self):
        """
        Test that noisy input gets properly cleansed while preserving important information
        """
        # Create test state with noisy input
        state = ConversationWorkflowState(
            session_id="test-session-456",
            restaurant_id=1,
            user_input="I'd like a Big Mac... Shawn stop hitting your sister... with no pickles and a large fry",
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
        assert result_state.user_input == "I'd like a Big Mac... Shawn stop hitting your sister... with no pickles and a large fry"
        
        # Verify cleansed input removes noise but preserves important info
        assert result_state.normalized_user_input is not None
        assert len(result_state.normalized_user_input) > 0
        assert "Shawn stop hitting your sister" not in result_state.normalized_user_input
        assert "Big Mac" in result_state.normalized_user_input
        assert "no pickles" in result_state.normalized_user_input
        assert "large fry" in result_state.normalized_user_input
        
        print(f"✅ Noisy input cleansed successfully:")
        print(f"   Original: {result_state.user_input}")
        print(f"   Cleansed: {result_state.normalized_user_input}")
        print(f"   Intent: {result_state.intent_type}")
        print(f"   Confidence: {result_state.intent_confidence}")
    
    @pytest.mark.asyncio
    async def test_complex_noisy_multiple_items(self):
        """
        Test complex noisy input with multiple items and lots of background chatter
        """
        # Create test state with very noisy input containing multiple items
        state = ConversationWorkflowState(
            session_id="test-session-789",
            restaurant_id=1,
            user_input="I want a ... oh hi Jeff give me one moment im at the drive thru ... I want a quantum burger, two large fries ... what do you mean the deal...an oreo shake...i told you in the drive thru...yes yes an oreo shake and two onion rings...it's not my fault they can't close the deal",
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
        assert result_state.intent_confidence >= 0.7  # Should be reasonably confident despite noise
        
        # Verify original text is preserved
        assert "oh hi Jeff" in result_state.user_input
        assert "drive thru" in result_state.user_input
        assert "quantum burger" in result_state.user_input
        
        # Verify cleansed input removes noise but preserves all food items
        assert result_state.normalized_user_input is not None
        assert len(result_state.normalized_user_input) > 0
        
        # Should remove background chatter
        assert "oh hi Jeff" not in result_state.normalized_user_input
        assert "give me one moment" not in result_state.normalized_user_input
        assert "what do you mean the deal" not in result_state.normalized_user_input
        assert "it's not my fault they can't close the deal" not in result_state.normalized_user_input
        
        # Should preserve all food items
        assert "quantum burger" in result_state.normalized_user_input
        assert "two large fries" in result_state.normalized_user_input
        assert "oreo shake" in result_state.normalized_user_input
        assert "two onion rings" in result_state.normalized_user_input
        
        print(f"✅ Complex noisy input cleansed successfully:")
        print(f"   Original: {result_state.user_input}")
        print(f"   Cleansed: {result_state.normalized_user_input}")
        print(f"   Intent: {result_state.intent_type}")
        print(f"   Confidence: {result_state.intent_confidence}")


if __name__ == "__main__":
    # Run a quick test
    import asyncio
    
    async def run_test():
        test = TestIntentClassifierIntegration()
        await test.test_environment_check()
        await test.test_multiple_items_happy_case()
        await test.test_noisy_input_cleansing()
        await test.test_complex_noisy_multiple_items()
    
    asyncio.run(run_test())
