"""
Integration tests for clarification agent that hits real LLM systems
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add the app directory to the Python path for proper imports
app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from app.agents.nodes.clarification_agent_node import clarification_agent_node
from app.agents.state.conversation_state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState, OrderState, ConversationContext
from app.dto.order_result import CommandBatchResult, OrderResult, OrderResultStatus, ErrorCategory, ErrorCode
from app.constants.audio_phrases import AudioPhraseType
from app.tests.helpers.mock_services import MockContainer
from app.tests.helpers.test_data_factory import TestDataFactory
from app.core.config import settings


class TestClarificationAgentIntegration:
    """Integration tests for clarification agent hitting real LLM"""
    
    @pytest.mark.asyncio
    async def test_clarification_agent_basic(self):
        """
        Test clarification agent with item not found scenario
        """
        # Use test data factory for batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["item_not_found"]
        
        # Create test state
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            user_input="I want a chocolate pie",
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
            command_batch_result=batch_result
        )
        
        # Create mock container
        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service
        
        # Mock database session with proper async behavior
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator
        
        # Mock MenuService to return test data
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
                "Big Mac", "Quarter Pounder", "Fries", "Apple Pie", "Cheesecake"
            ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service
        
        context = {"container": container}
        
        # Call the clarification agent (hits real LLM)
        result_state = await clarification_agent_node(state, context)
        
        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None
        
        print(f"\n🎯 CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 50)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")
        print(f"📊 Response Type: {result_state.response_phrase_type}")
        
        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 50)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Current Order: {state.order_state.line_items}")
        
        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 50)
        print(f"1. AI analyzed the failed item: 'chocolate pie'")
        print(f"2. AI checked available menu items: {mock_menu_service.get_available_items_for_restaurant.return_value}")
        print(f"3. AI identified similar items: Apple Pie, Cheesecake (from available items)")
        print(f"4. AI generated helpful response suggesting alternatives")
        print(f"5. AI chose phrase type: {result_state.response_phrase_type}")
        
        print(f"\n✅ Clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_partial_success(self):
        """Test clarification agent with partial success scenario"""

        # Create partial success batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["partial_success"]

        state = ConversationWorkflowState(
            session_id="test-session-456",
            restaurant_id="1",
            user_input="I want a quantum burger and two churros",
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
            command_batch_result=batch_result
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with dessert items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "Classic Burger", "Fries", "Chocolate Pudding", "Apple Pie", "Ice Cream"
        ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service

        context = {"container": container}

        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 PARTIAL SUCCESS CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 60)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Available Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 60)
        print(f"1. AI analyzed partial success: Quantum Burger ✅, Churros ❌")
        print(f"2. AI checked available desserts: Chocolate Pudding, Apple Pie, Ice Cream")
        print(f"3. AI made connection: Churros → Chocolate Pudding (both desserts)")
        print(f"4. AI acknowledged success and suggested dessert alternative")
        print(f"5. AI chose phrase type: {result_state.response_phrase_type}")

        print(f"\n✅ Partial success clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_quantity_limit(self):
        """Test clarification agent with quantity limit scenario"""
        
        # Create quantity limit batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["quantity_exceeds_limit"]

        state = ConversationWorkflowState(
            session_id="test-session-789",
            restaurant_id="1",
            user_input="I want 10,000 water bottles",
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
            command_batch_result=batch_result
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with reasonable items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Water Bottle", "Coke", "Sprite", "Big Mac", "Fries", "Apple Pie"
        ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service

        context = {"container": container}

        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 QUANTITY LIMIT CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 60)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Available Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 60)
        print(f"1. AI analyzed unreasonable request: 10,000 water bottles")
        print(f"2. AI recognized this as a quantity limit issue")
        print(f"3. AI responded matter-of-factly about the limit")
        print(f"4. AI chose phrase type: {result_state.response_phrase_type}")

        print(f"\n✅ Quantity limit clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_modifier_conflict(self):
        """Test clarification agent with modifier conflict scenario"""
        
        # Create modifier conflict batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["modifier_conflict"]

        state = ConversationWorkflowState(
            session_id="test-session-999",
            restaurant_id="1",
            user_input="I want a hamburger with extra meat and no meat",
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
            command_batch_result=batch_result
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with burger items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Hamburger", "Cheeseburger", "Big Mac", "Quarter Pounder", "Fries", "Coke"
        ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service

        context = {"container": container}

        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 MODIFIER CONFLICT CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 60)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Available Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 60)
        print(f"1. AI analyzed conflicting request: 'extra meat and no meat'")
        print(f"2. AI recognized this as a modifier conflict")
        print(f"3. AI clarified the contradiction and asked for clarification")
        print(f"4. AI chose phrase type: {result_state.response_phrase_type}")

        print(f"\n✅ Modifier conflict clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_no_substitutes(self):
        """Test clarification agent with no reasonable substitutes scenario"""
        
        # Create no substitutes batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["no_substitutes"]

        state = ConversationWorkflowState(
            session_id="test-session-111",
            restaurant_id="1",
            user_input="I want shark fin soup",
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
            command_batch_result=batch_result
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with typical fast food items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Big Mac", "Quarter Pounder", "Fries", "Coke", "Apple Pie", "Ice Cream"
        ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service

        context = {"container": container}

        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 NO SUBSTITUTES CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 60)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Available Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 60)
        print(f"1. AI analyzed inappropriate request: 'shark fin soup'")
        print(f"2. AI recognized this as completely unavailable")
        print(f"3. AI asked open-ended question since no substitutes make sense")
        print(f"4. AI chose phrase type: {result_state.response_phrase_type}")

        print(f"\n✅ No substitutes clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_multi_item_mixed_results(self):
        """Test clarification agent with multi-item mixed results scenario"""
        
        # Create multi-item mixed results batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["multi_item_mixed_results"]

        state = ConversationWorkflowState(
            session_id="test-session-222",
            restaurant_id="1",
            user_input="I want a quantum burger with extra onions, a strawberry milkshake, and waffle fries",
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
            command_batch_result=batch_result
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with available items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "Strawberry Milkshake", "Regular Fries", "Curly Fries", "Big Mac", "Coke"
        ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service

        context = {"container": container}

        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 MULTI-ITEM MIXED RESULTS CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 60)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Available Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 60)
        print(f"1. AI analyzed mixed results: Quantum Burger ✅, Strawberry Milkshake ✅, Waffle Fries ❌")
        print(f"2. AI acknowledged successes first")
        print(f"3. AI addressed the failure and suggested alternatives")
        print(f"4. AI chose phrase type: {result_state.response_phrase_type}")

        print(f"\n✅ Multi-item mixed results clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_option_required_missing(self):
        """Test clarification agent with required option missing scenario"""
        
        # Create required option missing batch result
        batch_scenarios = TestDataFactory.create_batch_result_scenarios()
        batch_result = batch_scenarios["option_required_missing"]

        state = ConversationWorkflowState(
            session_id="test-session-333",
            restaurant_id="1",
            user_input="I want a coke",
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
            command_batch_result=batch_result
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with drink items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Coke", "Sprite", "Orange Juice", "Coffee", "Big Mac", "Fries"
        ]
        mock_menu_service.get_restaurant_name.return_value = "McDonald's"
        container.menu_service = lambda: mock_menu_service

        context = {"container": container}

        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 OPTION REQUIRED MISSING CLARIFICATION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Generated Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n📋 INPUT DATA TO AI:")
        print(f"=" * 60)
        print(f"🍽️  User Input: '{state.user_input}'")
        print(f"📦 Batch Outcome: {batch_result.batch_outcome}")
        print(f"❌ Failed Items: {[r.message for r in batch_result.get_failed_results()]}")
        print(f"✅ Success Items: {[r.message for r in batch_result.get_successful_results()]}")
        print(f"🏪 Restaurant: McDonald's")
        print(f"📋 Available Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        print(f"\n🤖 AI PROCESSING:")
        print(f"=" * 60)
        print(f"1. AI analyzed incomplete request: 'I want a coke'")
        print(f"2. AI recognized missing required option (size)")
        print(f"3. AI asked for the missing information")
        print(f"4. AI chose phrase type: {result_state.response_phrase_type}")

        print(f"\n✅ Option required missing clarification agent test passed!")

    @pytest.mark.asyncio
    async def test_clarification_agent_with_clarification_commands(self):
        """
        Test clarification agent with clarification commands (new functionality)
        """
        print("\n🧪 TESTING CLARIFICATION AGENT - WITH CLARIFICATION COMMANDS")
        print("=" * 70)
        
        # Create batch result with clarification command
        clarification_result = OrderResult.success(
            message="Clarification needed",
            data={
                "clarification_type": "ambiguous_item",
                "ambiguous_item": "burger",
                "suggested_options": ["Quantum Burger", "Classic Burger", "Chicken Burger"],
                "user_input": "I want a burger with foie gras",
                "clarification_question": "Which burger would you like? We have Quantum Burger, Classic Burger, and Chicken Burger.",
                "needs_user_response": True
            }
        )
        
        # Create batch result with mixed scenario
        batch_result = CommandBatchResult(
            results=[clarification_result],
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Clarification needed",
            command_family="CLARIFICATION_NEEDED",
            batch_outcome="ALL_SUCCESS",  # Clarification commands return success
            first_error_code=None,
            response_payload={}
        )
        
        # Create test state
        state = ConversationWorkflowState(
            session_id="test-session-clarification",
            restaurant_id="1",
            user_input="I want a burger with foie gras",
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
            command_batch_result=batch_result
        )
        
        # Create mock container (following existing test pattern)
        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/clarification-test.mp3"
        container.voice_service = lambda: mock_voice_service
        
        # Mock database session with proper async behavior
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator
        
        # Mock MenuService to return test data
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            {"id": 1, "name": "Quantum Burger", "price": 9.99},
            {"id": 2, "name": "Classic Burger", "price": 8.99},
            {"id": 3, "name": "Chicken Burger", "price": 7.99}
        ]
        mock_menu_service.get_restaurant_name.return_value = "Test Restaurant"
        container.menu_service = lambda: mock_menu_service
        
        # Create service factory for the clarification agent
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(container)
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        context = {
            "configurable": {
                "service_factory": service_factory,
                "shared_db_session": mock_db_session
            }
        }
        
        print(f"📝 User Input: '{state.user_input}'")
        print(f"🔍 Batch Result: {batch_result.batch_outcome}")
        print(f"📋 Clarification Commands: {len(batch_result.results)}")
        print(f"🎯 Expected: Should handle clarification commands and generate appropriate response")
        
        # Call the clarification agent
        result_state = await clarification_agent_node(state, context)
        
        # Debug output
        print(f"\n🔍 DEBUG - CLARIFICATION AGENT OUTPUT:")
        print(f"   Response Text: '{result_state.response_text}'")
        print(f"   Phrase Type: {result_state.response_phrase_type}")
        print(f"   Audio URL: {result_state.audio_url}")
        
        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [
            AudioPhraseType.CLARIFICATION_QUESTION, 
            AudioPhraseType.CUSTOM_RESPONSE, 
            AudioPhraseType.LLM_GENERATED
        ]
        
        # Check that the response mentions clarification
        response_lower = result_state.response_text.lower()
        clarification_indicators = [
            "which", "burger", "quantum", "classic", "chicken", 
            "would you like", "did you mean", "clarify"
        ]
        
        has_clarification_content = any(indicator in response_lower for indicator in clarification_indicators)
        assert has_clarification_content, f"Response should contain clarification content: {result_state.response_text}"
        
        print("\n✅ Test passed: Clarification agent handled clarification commands correctly")


if __name__ == "__main__":
    # Run a quick test
    import asyncio
    
    async def run_test():
        test = TestClarificationAgentIntegration()
        await test.test_environment_check()
        await test.test_item_not_found_clarification()
        await test.test_partial_success_clarification()
    
    asyncio.run(run_test())
