"""
Integration tests for ADD_ITEM agent

Tests the ADD_ITEM agent with real LLM calls to ensure it can parse
customer requests and extract menu items, quantities, sizes, and modifications.
"""

import pytest
import os
from unittest.mock import AsyncMock
from app.agents.command_agents.add_item_agent import add_item_agent_node
from app.agents.state import ConversationWorkflowState
from app.models.state_machine_models import OrderState, ConversationContext, ConversationState
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings
from app.tests.helpers.test_data_factory import TestDataFactory


class MockContainer:
    """Mock container for dependency injection"""
    def __init__(self):
        self.services = {}
    
    def menu_service(self):
        return self.services.get('menu_service')
    
    def restaurant_service(self):
        return self.services.get('restaurant_service')
    
    def voice_service(self):
        return self.services.get('voice_service')


class TestAddItemAgentIntegration:
    """Test ADD_ITEM agent integration"""
    
    @pytest.mark.asyncio
    async def test_add_item_agent_quantum_burger(self):
        """Test ADD_ITEM agent with simple quantum burger request"""
        
        print("\n🧪 TESTING ADD_ITEM AGENT - QUANTUM BURGER")
        print("=" * 50)

        user_input = "I would like one quantum burger please"
        restaurant_id = "1"

        state = ConversationWorkflowState(
            session_id="test-session-quantum-1",
            restaurant_id=restaurant_id,
            user_input=user_input,
            normalized_user_input=user_input,  # Using normalized input
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

        # Mock container
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/quantum-burger-test.mp3"
        container.services['voice_service'] = mock_voice_service

        # Mock MenuService
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            TestDataFactory.create_menu_item(1, "Quantum Burger", 9.99, "A delicious quantum burger"),
            TestDataFactory.create_menu_item(2, "Classic Burger", 8.99, "A classic burger"),
            TestDataFactory.create_menu_item(3, "Chicken Sandwich", 7.99, "A tasty chicken sandwich"),
            TestDataFactory.create_menu_item(4, "Fries", 3.99, "Crispy golden fries"),
            TestDataFactory.create_menu_item(5, "Coke", 2.99, "Refreshing cola"),
            TestDataFactory.create_menu_item(6, "Sprite", 2.99, "Lemon-lime soda")
        ]
        mock_menu_service.get_menu_categories.return_value = ["Burgers", "Sides", "Drinks"]
        mock_menu_service.get_menu_items_by_category.return_value = {
            "Burgers": ["Quantum Burger", "Classic Burger"],
            "Sides": ["Fries"],
            "Drinks": ["Coke", "Sprite"]
        }
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "tomato", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "onion", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "cheese", "is_optional": True, "is_allergen": True, "allergen_type": "dairy", "additional_cost": 0.50},
            {"name": "bun", "is_optional": False, "is_allergen": True, "allergen_type": "gluten", "additional_cost": 0.0}
        ]
        mock_menu_service.get_all_ingredients_with_costs.return_value = [
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False},
            {"name": "tomato", "unit_cost": 0.0, "is_allergen": False},
            {"name": "onion", "unit_cost": 0.0, "is_allergen": False},
            {"name": "cheese", "unit_cost": 0.50, "is_allergen": True, "allergen_type": "dairy"},
            {"name": "bun", "unit_cost": 0.0, "is_allergen": True, "allergen_type": "gluten"}
        ]
        container.services['menu_service'] = mock_menu_service

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
        container.services['restaurant_service'] = mock_restaurant_service

        context = {"container": container}

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        # Call the ADD_ITEM agent
        result_state = await add_item_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type == AudioPhraseType.LLM_GENERATED
        assert result_state.audio_url is None  # Will be set by voice service
        
        # Validate structured output using CommandDataValidator
        assert hasattr(result_state, 'commands'), "State should have commands attribute"
        assert result_state.commands is not None, "Commands should not be None"
        assert len(result_state.commands) > 0, "Should have at least one command"
        
        # Use CommandDataValidator to ensure contract compliance
        from app.commands.command_data_validator import CommandDataValidator
        
        for i, command in enumerate(result_state.commands):
            is_valid, errors = CommandDataValidator.validate(command)
            if not is_valid:
                error_summary = CommandDataValidator.get_validation_summary(errors)
                assert False, f"Command {i+1} failed validation: {error_summary}"
        
        # Additional checks for ADD_ITEM specific fields
        first_command = result_state.commands[0]
        assert first_command['intent'] == 'ADD_ITEM', "Command intent should be ADD_ITEM"
        assert 'slots' in first_command, "Command should have slots"
        assert 'menu_item_id' in first_command['slots'], "Should have menu_item_id in slots"
        assert 'quantity' in first_command['slots'], "Should have quantity in slots"
        
        print(f"\n🎯 ADD_ITEM AGENT OUTPUT:")
        print(f"=" * 50)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")
        print(f"📋 Commands: {len(result_state.commands)}")
        for i, cmd in enumerate(result_state.commands):
            print(f"  Command {i+1}: {cmd['intent']} - ID {cmd['slots']['menu_item_id']} x{cmd['slots']['quantity']}")

        print(f"\n✅ Quantum burger test completed!")
        print(f"🎯 Expected: AI should parse 'quantum burger' and extract item details")

    @pytest.mark.asyncio
    async def test_add_item_agent_multiple_items(self):
        """Test ADD_ITEM agent with multiple items request"""
        
        print("\n🧪 TESTING ADD_ITEM AGENT - MULTIPLE ITEMS")
        print("=" * 60)

        user_input = "I want two large burgers and a medium coke"
        restaurant_id = "1"

        state = ConversationWorkflowState(
            session_id="test-session-multiple-1",
            restaurant_id=restaurant_id,
            user_input=user_input,
            normalized_user_input=user_input,
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

        # Mock container
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/multiple-items-test.mp3"
        container.services['voice_service'] = mock_voice_service

        # Mock MenuService
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            TestDataFactory.create_menu_item(1, "Quantum Burger", 9.99, "A delicious quantum burger"),
            TestDataFactory.create_menu_item(2, "Classic Burger", 8.99, "A classic burger"),
            TestDataFactory.create_menu_item(3, "Chicken Sandwich", 7.99, "A tasty chicken sandwich"),
            TestDataFactory.create_menu_item(4, "Fries", 3.99, "Crispy golden fries"),
            TestDataFactory.create_menu_item(5, "Coke", 2.99, "Refreshing cola"),
            TestDataFactory.create_menu_item(6, "Sprite", 2.99, "Lemon-lime soda")
        ]
        mock_menu_service.get_menu_categories.return_value = ["Burgers", "Sides", "Drinks"]
        mock_menu_service.get_menu_items_by_category.return_value = {
            "Burgers": ["Quantum Burger", "Classic Burger"],
            "Sides": ["Fries"],
            "Drinks": ["Coke", "Sprite"]
        }
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0}
        ]
        mock_menu_service.get_all_ingredients_with_costs.return_value = [
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False}
        ]
        container.services['menu_service'] = mock_menu_service

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
        container.services['restaurant_service'] = mock_restaurant_service

        context = {"container": container}

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        # Call the ADD_ITEM agent
        result_state = await add_item_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type == AudioPhraseType.LLM_GENERATED
        assert result_state.audio_url is None
        
        # Validate structured output using CommandDataValidator
        assert hasattr(result_state, 'commands'), "State should have commands attribute"
        assert result_state.commands is not None, "Commands should not be None"
        assert len(result_state.commands) > 0, "Should have at least one command"
        
        # Use CommandDataValidator to ensure contract compliance
        from app.commands.command_data_validator import CommandDataValidator
        
        for i, command in enumerate(result_state.commands):
            is_valid, errors = CommandDataValidator.validate(command)
            if not is_valid:
                error_summary = CommandDataValidator.get_validation_summary(errors)
                assert False, f"Command {i+1} failed validation: {error_summary}"
        
        # Additional checks for ADD_ITEM specific fields
        for cmd in result_state.commands:
            assert cmd['intent'] == 'ADD_ITEM', "Command intent should be ADD_ITEM"
            assert 'slots' in cmd, "Command should have slots"
            assert 'menu_item_id' in cmd['slots'], "Should have menu_item_id in slots"
            assert 'quantity' in cmd['slots'], "Should have quantity in slots"

        print(f"\n🎯 ADD_ITEM AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")
        print(f"📋 Commands: {len(result_state.commands)}")
        for i, cmd in enumerate(result_state.commands):
            print(f"  Command {i+1}: {cmd['intent']} - ID {cmd['slots']['menu_item_id']} x{cmd['slots']['quantity']}")

        print(f"\n✅ Multiple items test completed!")
        print(f"🎯 Expected: AI should parse 'two large burgers and a medium coke' and extract multiple items")

    @pytest.mark.asyncio
    async def test_add_item_agent_with_modifiers(self):
        """Test ADD_ITEM agent with modifiers request"""
        
        print("\n🧪 TESTING ADD_ITEM AGENT - WITH MODIFIERS")
        print("=" * 60)

        user_input = "I want a quantum burger with extra cheese and no pickles"
        restaurant_id = "1"

        state = ConversationWorkflowState(
            session_id="test-session-modifiers-1",
            restaurant_id=restaurant_id,
            user_input=user_input,
            normalized_user_input=user_input,
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

        # Mock container
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/modifiers-test.mp3"
        container.services['voice_service'] = mock_voice_service

        # Mock MenuService
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            TestDataFactory.create_menu_item(1, "Quantum Burger", 9.99, "A delicious quantum burger"),
            TestDataFactory.create_menu_item(2, "Classic Burger", 8.99, "A classic burger"),
            TestDataFactory.create_menu_item(3, "Chicken Sandwich", 7.99, "A tasty chicken sandwich"),
            TestDataFactory.create_menu_item(4, "Fries", 3.99, "Crispy golden fries"),
            TestDataFactory.create_menu_item(5, "Coke", 2.99, "Refreshing cola"),
            TestDataFactory.create_menu_item(6, "Sprite", 2.99, "Lemon-lime soda")
        ]
        mock_menu_service.get_menu_categories.return_value = ["Burgers", "Sides", "Drinks"]
        mock_menu_service.get_menu_items_by_category.return_value = {
            "Burgers": ["Quantum Burger", "Classic Burger"],
            "Sides": ["Fries"],
            "Drinks": ["Coke", "Sprite"]
        }
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "tomato", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "pickles", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
            {"name": "cheese", "is_optional": True, "is_allergen": True, "allergen_type": "dairy", "additional_cost": 0.50}
        ]
        mock_menu_service.get_all_ingredients_with_costs.return_value = [
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False},
            {"name": "tomato", "unit_cost": 0.0, "is_allergen": False},
            {"name": "pickles", "unit_cost": 0.0, "is_allergen": False},
            {"name": "cheese", "unit_cost": 0.50, "is_allergen": True, "allergen_type": "dairy"}
        ]
        container.services['menu_service'] = mock_menu_service

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
        container.services['restaurant_service'] = mock_restaurant_service

        context = {"container": container}

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {mock_menu_service.get_available_items_for_restaurant.return_value}")

        # Call the ADD_ITEM agent
        result_state = await add_item_agent_node(state, context)

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type == AudioPhraseType.LLM_GENERATED
        assert result_state.audio_url is None
        
        # Validate structured output using CommandDataValidator
        assert hasattr(result_state, 'commands'), "State should have commands attribute"
        assert result_state.commands is not None, "Commands should not be None"
        assert len(result_state.commands) > 0, "Should have at least one command"
        
        # Use CommandDataValidator to ensure contract compliance
        from app.commands.command_data_validator import CommandDataValidator
        
        for i, command in enumerate(result_state.commands):
            is_valid, errors = CommandDataValidator.validate(command)
            if not is_valid:
                error_summary = CommandDataValidator.get_validation_summary(errors)
                assert False, f"Command {i+1} failed validation: {error_summary}"
        
        # Additional checks for ADD_ITEM specific fields
        for cmd in result_state.commands:
            assert cmd['intent'] == 'ADD_ITEM', "Command intent should be ADD_ITEM"
            assert 'slots' in cmd, "Command should have slots"
            assert 'menu_item_id' in cmd['slots'], "Should have menu_item_id in slots"
            assert 'modifiers' in cmd['slots'], "Should have modifiers in slots"

        print(f"\n🎯 ADD_ITEM AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")
        print(f"📋 Commands: {len(result_state.commands)}")
        for i, cmd in enumerate(result_state.commands):
            modifiers = cmd['slots'].get('modifiers', [])
            print(f"  Command {i+1}: {cmd['intent']} - ID {cmd['slots']['menu_item_id']} x{cmd['slots']['quantity']} (modifiers: {modifiers})")

        print(f"\n✅ Modifiers test completed!")
        print(f"🎯 Expected: AI should parse 'extra cheese and no pickles' and extract modifiers")


if __name__ == "__main__":
    # Run the tests
    import asyncio
    
    async def run_tests():
        test_instance = TestAddItemAgentIntegration()
        
        print("🚀 Running ADD_ITEM Agent Integration Tests")
        print("=" * 60)
        
        try:
            await test_instance.test_add_item_agent_quantum_burger()
            await test_instance.test_add_item_agent_multiple_items()
            await test_instance.test_add_item_agent_with_modifiers()
            
            print("\n🎉 All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())
