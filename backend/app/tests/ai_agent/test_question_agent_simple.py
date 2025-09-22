"""
Simple test for the Question Agent
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from app.agents.command_agents.question_agent import question_agent_node
from app.agents.state.conversation_state import ConversationWorkflowState
from app.models.state_machine_models import ConversationState, OrderState, ConversationContext
from app.constants.audio_phrases import AudioPhraseType
from app.tests.helpers.mock_services import MockContainer

class TestQuestionAgentSimple:
    """Simple test for the Question Agent"""

    @pytest.mark.asyncio
    async def test_question_agent_simple(self):
        """Test question agent with a simple question about ingredients"""
        
        # Create test state
        state = ConversationWorkflowState(
            session_id="test-session-123",
            restaurant_id="1",
            user_input="Hey, so can I get the quantum burger with no tomatoes?",
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
            command_batch_result=None
        )

        # Create mock container
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with menu items and ingredients
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "Classic Burger", "Chicken Sandwich", "Fries", "Coke", "Sprite"
        ]
        mock_menu_service.get_menu_categories.return_value = ["Burgers", "Sides", "Drinks"]
        mock_menu_service.get_menu_items_by_category.return_value = {
            "Burgers": ["Quantum Burger", "Classic Burger"],
            "Sides": ["Fries"],
            "Drinks": ["Coke", "Sprite"]
        }
        # Mock ingredients for Quantum Burger with pricing
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "tomato", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "onion", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "cheese", "is_optional": True, "is_allergen": True, "allergen_type": "dairy", "additional_cost": 0.50},
            {"name": "bun", "is_optional": False, "is_allergen": True, "allergen_type": "gluten", "additional_cost": 0.0}
        ]
        
        # Mock all available ingredients with costs
        mock_menu_service.get_all_ingredients_with_costs.return_value = [
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False},
            {"name": "tomato", "unit_cost": 0.0, "is_allergen": False},
            {"name": "onion", "unit_cost": 0.0, "is_allergen": False},
            {"name": "cheese", "unit_cost": 0.50, "is_allergen": True, "allergen_type": "dairy"},
            {"name": "bun", "unit_cost": 0.0, "is_allergen": True, "allergen_type": "gluten"},
            {"name": "bacon", "unit_cost": 1.00, "is_allergen": False},
            {"name": "avocado", "unit_cost": 1.50, "is_allergen": False}
        ]
        container.menu_service = lambda: mock_menu_service

        # Mock RestaurantService
        mock_restaurant_service = AsyncMock()
        mock_restaurant_service.get_restaurant_info.return_value = {
            "id": 1,
            "name": "Test Restaurant",
            "description": "A test restaurant",
            "address": "123 Test St",
            "phone": "555-123-4567",
            "hours": "9 AM to 9 PM",
            "is_active": True
        }
        container.restaurant_service = lambda: mock_restaurant_service

        context = {"container": container}

        print(f"\n🧪 TESTING QUESTION AGENT")
        print(f"=" * 50)
        print(f"📝 User Input: '{state.user_input}'")
        print(f"🏪 Restaurant: Test Restaurant")
        print(f"📋 Menu Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        # Call the question agent
        result_state = await question_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]
        assert result_state.audio_url is not None

        print(f"\n🎯 QUESTION AGENT OUTPUT:")
        print(f"=" * 50)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n✅ Question agent test completed!")
    
    @pytest.mark.asyncio
    async def test_question_agent_add_cheese(self):
        """Test question agent with adding cheese to quantum burger"""
        
        print("\n🧪 TESTING QUESTION AGENT - ADD CHEESE")
        print("=" * 50)

        user_input = "Can I add cheese to the quantum burger?"
        restaurant_id = "1"

        state = ConversationWorkflowState(
            session_id="test-session-cheese-1",
            restaurant_id=restaurant_id,
            user_input=user_input,
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
            command_batch_result=None
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/cheese-test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with cheese pricing
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "Classic Burger", "Chicken Sandwich", "Fries", "Coke", "Sprite"
        ]
        mock_menu_service.get_menu_categories.return_value = ["Burgers", "Sides", "Drinks"]
        mock_menu_service.get_menu_items_by_category.return_value = {
            "Burgers": ["Quantum Burger", "Classic Burger"],
            "Sides": ["Fries"],
            "Drinks": ["Coke", "Sprite"]
        }
        
        # Mock ingredients for Quantum Burger with cheese pricing
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "tomato", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "onion", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "cheese", "is_optional": True, "is_allergen": True, "allergen_type": "dairy", "additional_cost": 0.50},
            {"name": "bun", "is_optional": False, "is_allergen": True, "allergen_type": "gluten", "additional_cost": 0.0}
        ]
        
        # Mock all available ingredients with costs
        mock_menu_service.get_all_ingredients_with_costs.return_value = [
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False},
            {"name": "tomato", "unit_cost": 0.0, "is_allergen": False},
            {"name": "onion", "unit_cost": 0.0, "is_allergen": False},
            {"name": "cheese", "unit_cost": 0.50, "is_allergen": True, "allergen_type": "dairy"},
            {"name": "bun", "unit_cost": 0.0, "is_allergen": True, "allergen_type": "gluten"},
            {"name": "bacon", "unit_cost": 1.00, "is_allergen": False},
            {"name": "avocado", "unit_cost": 1.50, "is_allergen": False}
        ]
        container.menu_service = lambda: mock_menu_service

        # Mock RestaurantService
        mock_restaurant_service = AsyncMock()
        mock_restaurant_service.get_restaurant_info.return_value = {
            "id": 1,
            "name": "Test Restaurant",
            "description": "A test restaurant",
            "address": "123 Test St",
            "phone": "555-123-4567",
            "hours": "9 AM to 9 PM",
            "is_active": True
        }
        mock_restaurant_service.get_restaurant_name.return_value = "Test Restaurant"
        mock_restaurant_service.get_restaurant_hours.return_value = "9 AM to 9 PM"
        mock_restaurant_service.get_restaurant_address.return_value = "123 Test St"
        mock_restaurant_service.get_restaurant_phone.return_value = "555-123-4567"
        container.restaurant_service = lambda: mock_restaurant_service

        context = {"container": container}

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_name.return_value}")
        print(f"📋 Menu Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")
        print(f"🧀 Cheese Cost: $0.50 (dairy allergen)")

        # Call the question agent
        result_state = await question_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type == AudioPhraseType.LLM_GENERATED
        assert result_state.audio_url is not None
        assert "cheese" in result_state.response_text.lower()
        assert "quantum burger" in result_state.response_text.lower()

        print(f"\n🎯 QUESTION AGENT OUTPUT:")
        print(f"=" * 50)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n✅ Cheese addition test completed!")
        print(f"💰 Expected: AI should mention the $0.50 cost for cheese")
    
    @pytest.mark.asyncio
    async def test_question_agent_add_bacon_and_sriracha(self):
        """Test question agent with adding bacon and sriracha sauce to quantum burger"""
        
        print("\n🧪 TESTING QUESTION AGENT - ADD BACON & SRIRACHA")
        print("=" * 60)

        user_input = "Can I add bacon and sriracha sauce to the quantum burger?"
        restaurant_id = "1"

        state = ConversationWorkflowState(
            session_id="test-session-bacon-sriracha-1",
            restaurant_id=restaurant_id,
            user_input=user_input,
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
            command_batch_result=None
        )

        container = MockContainer()
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/bacon-sriracha-test.mp3"
        container.voice_service = lambda: mock_voice_service

        # Mock database session
        mock_db_session = AsyncMock()
        async def mock_db_generator():
            yield mock_db_session
        container.get_db = mock_db_generator

        # Mock MenuService with bacon and sriracha pricing
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "Classic Burger", "Chicken Sandwich", "Fries", "Coke", "Sprite"
        ]
        mock_menu_service.get_menu_categories.return_value = ["Burgers", "Sides", "Drinks"]
        mock_menu_service.get_menu_items_by_category.return_value = {
            "Burgers": ["Quantum Burger", "Classic Burger"],
            "Sides": ["Fries"],
            "Drinks": ["Coke", "Sprite"]
        }
        
        # Mock ingredients for Quantum Burger (no bacon or sriracha normally)
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "tomato", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "onion", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "cheese", "is_optional": True, "is_allergen": True, "allergen_type": "dairy", "additional_cost": 0.50},
            {"name": "bun", "is_optional": False, "is_allergen": True, "allergen_type": "gluten", "additional_cost": 0.0}
        ]
        
        # Mock all available ingredients with costs (including bacon and sriracha)
        mock_menu_service.get_all_ingredients_with_costs.return_value = [
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False},
            {"name": "tomato", "unit_cost": 0.0, "is_allergen": False},
            {"name": "onion", "unit_cost": 0.0, "is_allergen": False},
            {"name": "cheese", "unit_cost": 0.50, "is_allergen": True, "allergen_type": "dairy"},
            {"name": "bun", "unit_cost": 0.0, "is_allergen": True, "allergen_type": "gluten"},
            {"name": "bacon", "unit_cost": 1.00, "is_allergen": False},
            {"name": "avocado", "unit_cost": 1.50, "is_allergen": False},
            {"name": "sriracha sauce", "unit_cost": 0.30, "is_allergen": False}
        ]
        container.menu_service = lambda: mock_menu_service

        # Mock RestaurantService
        mock_restaurant_service = AsyncMock()
        mock_restaurant_service.get_restaurant_info.return_value = {
            "id": 1,
            "name": "Test Restaurant",
            "description": "A test restaurant",
            "address": "123 Test St",
            "phone": "555-123-4567",
            "hours": "9 AM to 9 PM",
            "is_active": True
        }
        mock_restaurant_service.get_restaurant_name.return_value = "Test Restaurant"
        mock_restaurant_service.get_restaurant_hours.return_value = "9 AM to 9 PM"
        mock_restaurant_service.get_restaurant_address.return_value = "123 Test St"
        mock_restaurant_service.get_restaurant_phone.return_value = "555-123-4567"
        container.restaurant_service = lambda: mock_restaurant_service

        context = {"container": container}

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_name.return_value}")
        print(f"📋 Menu Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")
        print(f"🥓 Bacon Cost: $1.00")
        print(f"🌶️ Sriracha Cost: $0.30")
        print(f"💰 Total Additional Cost: $1.30")

        # Call the question agent
        result_state = await question_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type == AudioPhraseType.LLM_GENERATED
        assert result_state.audio_url is not None
        assert "bacon" in result_state.response_text.lower()
        assert "sriracha" in result_state.response_text.lower()
        assert "quantum burger" in result_state.response_text.lower()

        print(f"\n🎯 QUESTION AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")

        print(f"\n✅ Bacon & Sriracha addition test completed!")
        print(f"💰 Expected: AI should mention both $1.00 for bacon and $0.30 for sriracha")


if __name__ == "__main__":
    import asyncio
    test = TestQuestionAgentSimple()
    asyncio.run(test.test_question_agent_simple())
