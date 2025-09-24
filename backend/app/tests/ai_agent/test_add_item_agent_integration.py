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

    @pytest.mark.asyncio
    async def test_add_item_agent_ambiguous_burger(self):
        """Test ADD_ITEM agent with ambiguous burger request (should create clarification command)"""
        
        print("\n🧪 TESTING ADD_ITEM AGENT - AMBIGUOUS BURGER")
        print("=" * 60)

        user_input = "I want a burger"  # Ambiguous - multiple burger options available
        restaurant_id = "1"

        state = ConversationWorkflowState(
            session_id="test-session-ambiguous-1",
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
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/ambiguous-test.mp3"
        container.services['voice_service'] = mock_voice_service

        # Mock MenuService with multiple burger options to create ambiguity     
        mock_menu_service = AsyncMock()
        
        # Create the menu items data
        menu_items = [
            TestDataFactory.create_menu_item(1, "Quantum Burger", 9.99, "A delicious quantum burger"),
            TestDataFactory.create_menu_item(2, "Classic Burger", 8.99, "A classic burger"),
            TestDataFactory.create_menu_item(3, "Chicken Burger", 7.99, "A chicken burger"),
            TestDataFactory.create_menu_item(4, "Fries", 3.99, "Crispy golden fries"),
            TestDataFactory.create_menu_item(5, "Coke", 2.99, "Refreshing cola")
        ]
        
        # Mock the async methods to return the data directly (not coroutines)
        async def mock_get_available_items(restaurant_id):
            return menu_items
        
        async def mock_get_categories(restaurant_id):
            return ["Burgers", "Sides", "Drinks"]
        
        async def mock_get_items_by_category(restaurant_id):
            return {
                "Burgers": ["Quantum Burger", "Classic Burger", "Chicken Burger"],
                "Sides": ["Fries"],
                "Drinks": ["Coke"]
            }
        
        async def mock_get_ingredients(menu_item_id):
            return [
                {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
                {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0}
            ]
        
        async def mock_get_all_ingredients(restaurant_id):
            return [
                {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
                {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False}
            ]
        
        async def mock_get_restaurant_name(restaurant_id):
            return "Test Restaurant"
        
        # Assign the async functions
        mock_menu_service.get_available_items_for_restaurant = mock_get_available_items
        mock_menu_service.get_menu_categories = mock_get_categories
        mock_menu_service.get_menu_items_by_category = mock_get_items_by_category
        mock_menu_service.get_menu_item_ingredients = mock_get_ingredients
        mock_menu_service.get_all_ingredients_with_costs = mock_get_all_ingredients
        mock_menu_service.get_restaurant_name = mock_get_restaurant_name
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

        # Create service factory for the agent
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(container)
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        context = {
            "container": container,
            "service_factory": service_factory,
            "shared_db_session": mock_db_session
        }

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {menu_items}")
        print(f"🔍 Expected: Should detect ambiguity and create CLARIFICATION_NEEDED command")

        # Call the ADD_ITEM agent
        result_state = await add_item_agent_node(state, context)
        
        # Debug output to see what the LLM actually returned
        print(f"\n🔍 DEBUG - AddItemResponse created:")
        if hasattr(result_state, 'add_item_response') and result_state.add_item_response:
            print(f"  Response type: {result_state.add_item_response.response_type}")
            print(f"  Items to add: {len(result_state.add_item_response.items_to_add)}")
            for i, item in enumerate(result_state.add_item_response.items_to_add):
                print(f"  Item {i+1}: menu_item_id={item.menu_item_id}, ambiguous_item={item.ambiguous_item}")

        # Assertions
        assert result_state.response_text is not None
        assert len(result_state.response_text) > 10
        assert result_state.response_phrase_type == AudioPhraseType.LLM_GENERATED
        assert result_state.audio_url is None
        
        # Validate structured response
        assert hasattr(result_state, 'add_item_response'), "State should have add_item_response attribute"
        assert result_state.add_item_response is not None, "AddItemResponse should not be None"
        assert result_state.add_item_response.response_type == "clarification_needed", "Should be clarification_needed"
        assert len(result_state.add_item_response.items_to_add) > 0, "Should have at least one item"
        
        # Check that it's an ambiguous item (menu_item_id = 0)
        ambiguous_item = result_state.add_item_response.items_to_add[0]
        assert ambiguous_item.menu_item_id == 0, "Should be ambiguous item (menu_item_id = 0)"
        assert ambiguous_item.ambiguous_item is not None, "Should have ambiguous_item"
        assert len(ambiguous_item.suggested_options) > 0, "Should have suggested options"
        
        # The agent now returns structured data instead of commands
        # The parser will convert this to commands later
        print(f"\n🎯 ADD_ITEM AGENT OUTPUT:")
        print(f"=" * 60)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")
        print(f"📋 AddItemResponse: {result_state.add_item_response.response_type}")
        print(f"=" * 60)

        print(f"\n✅ Ambiguous burger test completed!")
        print(f"🎯 Expected: AI should detect ambiguity and create structured response")

    @pytest.mark.asyncio
    async def test_add_item_agent_unavailable_ingredient(self):
        """Test ADD_ITEM agent with unavailable ingredient request (should handle gracefully)"""
        
        print("\n🧪 TESTING ADD_ITEM AGENT - UNAVAILABLE INGREDIENT")
        print("=" * 60)
        
        user_input = "I want a burger with foie gras"  # Unavailable ingredient
        restaurant_id = "1"
        
        state = ConversationWorkflowState(
            session_id="test-session-unavailable-1",
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
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/unavailable-ingredient-test.mp3"
        container.services['voice_service'] = mock_voice_service
        
        # Mock MenuService with limited ingredients (no foie gras)
        mock_menu_service = AsyncMock()
        
        # Create the menu items data
        menu_items = [
            TestDataFactory.create_menu_item(1, "Quantum Burger", 9.99, "A delicious quantum burger"),
            TestDataFactory.create_menu_item(2, "Classic Burger", 8.99, "A classic burger"),
            TestDataFactory.create_menu_item(3, "Chicken Burger", 7.99, "A chicken burger"),
            TestDataFactory.create_menu_item(4, "Fries", 3.99, "Crispy golden fries"),
            TestDataFactory.create_menu_item(5, "Coke", 2.99, "Refreshing cola")
        ]
        
        # Mock the async methods to return the data directly (not coroutines)
        async def mock_get_available_items(restaurant_id):
            return menu_items
        
        async def mock_get_categories(restaurant_id):
            return ["Burgers", "Sides", "Drinks"]
        
        async def mock_get_items_by_category(restaurant_id):
            return {
                "Burgers": ["Quantum Burger", "Classic Burger", "Chicken Burger"],
                "Sides": ["Fries"],
                "Drinks": ["Coke"]
            }
        
        async def mock_get_ingredients(menu_item_id):
            # Only return basic ingredients, no foie gras
            return [
                {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
                {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
                {"name": "tomato", "is_optional": True, "is_allergen": False, "additional_cost": 0.0},
                {"name": "cheese", "is_optional": True, "is_allergen": False, "additional_cost": 0.0}
            ]
        
        async def mock_get_all_ingredients(restaurant_id):
            # Only return available ingredients, no foie gras
            return [
                {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
                {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False},
                {"name": "tomato", "unit_cost": 0.0, "is_allergen": False},
                {"name": "cheese", "unit_cost": 0.0, "is_allergen": False}
            ]
        
        async def mock_get_restaurant_name(restaurant_id):
            return "Test Restaurant"
        
        # Assign the async functions
        mock_menu_service.get_available_items_for_restaurant = mock_get_available_items
        mock_menu_service.get_menu_categories = mock_get_categories
        mock_menu_service.get_menu_items_by_category = mock_get_items_by_category
        mock_menu_service.get_menu_item_ingredients = mock_get_ingredients
        mock_menu_service.get_all_ingredients_with_costs = mock_get_all_ingredients
        mock_menu_service.get_restaurant_name = mock_get_restaurant_name
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
        
        # Create service factory for the agent
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(container)
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        context = {
            "container": container,
            "service_factory": service_factory,
            "shared_db_session": mock_db_session
        }
        
        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {menu_items}")
        print(f"🔍 Expected: Should handle unavailable ingredient gracefully")
        
        # Call the ADD_ITEM agent
        result_state = await add_item_agent_node(state, context)
        
        # Debug output to see what the LLM actually returned
        print(f"\n🔍 DEBUG - Commands created:")
        for i, cmd in enumerate(result_state.commands):
            print(f"  Command {i+1}: {cmd}")
        
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
        
        print(f"\n🎯 ADD_ITEM AGENT OUTPUT:")
        print("=" * 60)
        print(f"📝 AI Response: '{result_state.response_text}'")
        print(f"🎵 Phrase Type: {result_state.response_phrase_type}")
        print(f"🔊 Audio URL: {result_state.audio_url}")
        print(f"📋 Commands: {len(result_state.commands)}")
        for i, cmd in enumerate(result_state.commands):
            print(f"  Command {i+1}: {cmd['intent']} - {cmd.get('slots', {}).get('user_input', 'N/A')}")
        
        print("\n✅ Unavailable ingredient test completed!")
        print("🎯 Expected: AI should handle unavailable ingredient gracefully")
        
        # The test passes if the agent responds appropriately (we don't enforce a specific command type)
        print("✅ Test passed: Unavailable ingredient handled gracefully")


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
            await test_instance.test_add_item_agent_ambiguous_burger()
            await test_instance.test_add_item_agent_unavailable_ingredient()
            
            print("\n🎉 All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())
