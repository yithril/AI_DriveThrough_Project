"""
Integration tests for Agent + Parser flow

Tests the complete flow from agent to parser to ensure:
1. Agent extracts correct menu item IDs from tool results
2. Parser creates correct commands for multiple items
3. The flow from agent → parser → commands works correctly
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agents.command_agents.add_item_agent import add_item_agent
from app.agents.parser.add_item_parser import AddItemParser
from app.agents.state import ConversationWorkflowState
from app.models.state_machine_models import OrderState, ConversationContext, ConversationState
from app.constants.audio_phrases import AudioPhraseType
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


class TestAgentParserIntegration:
    """Test Agent + Parser integration"""

    @pytest.mark.asyncio
    async def test_agent_parser_multi_item_flow(self):
        """Test complete flow: Agent → Parser → Commands for multiple items"""
        
        print("\n🧪 TESTING AGENT + PARSER INTEGRATION - MULTI ITEM")
        print("=" * 70)

        user_input = "I want a quantum burger a nebula wrap and a lunar lemonade please"
        restaurant_id = "1"

        # Create workflow state
        state = ConversationWorkflowState(
            session_id="test-session-multi-1",
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

        # Mock container with services
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/multi-item-test.mp3"
        container.services['voice_service'] = mock_voice_service

        # Mock MenuService with the actual menu items from the database
        mock_menu_service = AsyncMock()
        
        # Create menu items that match the database
        menu_items = [
            TestDataFactory.create_menu_item(1, "Quantum Cheeseburger", 7.99, "A delicious quantum cheeseburger"),
            TestDataFactory.create_menu_item(2, "Neon Double Burger", 8.99, "A neon double burger"),
            TestDataFactory.create_menu_item(3, "Veggie Nebula Wrap", 6.99, "A veggie nebula wrap"),
            TestDataFactory.create_menu_item(4, "Spicy Meteor Chicken", 7.99, "Spicy meteor chicken"),
            TestDataFactory.create_menu_item(5, "Galactic Fries", 3.99, "Galactic fries"),
            TestDataFactory.create_menu_item(6, "Cosmic Onion Rings", 4.99, "Cosmic onion rings"),
            TestDataFactory.create_menu_item(7, "Astro Nuggets", 5.99, "Astro nuggets"),
            TestDataFactory.create_menu_item(8, "Starlight Salad", 6.99, "Starlight salad"),
            TestDataFactory.create_menu_item(9, "Lunar Lemonade", 1.99, "Lunar lemonade"),
            TestDataFactory.create_menu_item(10, "Quantum Cola", 1.99, "Quantum cola")
        ]
        
        # Mock the async methods using AsyncMock properly
        mock_menu_service.get_available_items_for_restaurant = AsyncMock(return_value=menu_items)
        mock_menu_service.get_menu_categories = AsyncMock(return_value=["Sandwiches", "Sides", "Drinks"])
        mock_menu_service.get_menu_items_by_category = AsyncMock(return_value={
            "Sandwiches": ["Quantum Cheeseburger", "Neon Double Burger", "Veggie Nebula Wrap", "Spicy Meteor Chicken"],
            "Sides": ["Galactic Fries", "Cosmic Onion Rings", "Astro Nuggets", "Starlight Salad"],
            "Drinks": ["Lunar Lemonade", "Quantum Cola"]
        })
        mock_menu_service.get_menu_item_ingredients = AsyncMock(return_value=[
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0}
        ])
        mock_menu_service.get_all_ingredients_with_costs = AsyncMock(return_value=[
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False}
        ])
        mock_menu_service.get_restaurant_name = AsyncMock(return_value="Test Restaurant")
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

        # Override the service factory to use mocked services
        service_factory.create_menu_service = lambda db_session: mock_menu_service
        service_factory.create_restaurant_service = lambda db_session: mock_restaurant_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        context = {
            "container": container,
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": state.conversation_history,
            "order_state": state.order_state.__dict__ if state.order_state else {},
            "restaurant_id": state.restaurant_id
        }

        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {len(menu_items)} items available")

        # STEP 1: Test the Agent
        print(f"\n🔍 STEP 1: Testing AddItemAgent")
        print("-" * 40)
        
        agent_result = await add_item_agent(state.normalized_user_input, context)
        
        # Verify agent output
        assert agent_result is not None, "Agent should return AddItemResponse"
        assert hasattr(agent_result, 'items_to_add'), "Agent should return items_to_add"
        
        agent_response = agent_result
        print(f"📝 Agent Response: '{agent_response.response_text}'")
        print(f"🎯 Response Type: {agent_response.response_type}")
        print(f"📋 Items to Add: {len(agent_response.items_to_add)}")
        
        for i, item in enumerate(agent_response.items_to_add):
            print(f"  Item {i+1}: ID={item.menu_item_id}, Qty={item.quantity}")
        
        # STEP 2: Test the Parser
        print(f"\n🔍 STEP 2: Testing AddItemParser")
        print("-" * 40)
        
        # Create parser
        parser = AddItemParser()
        
        # Parse the agent's output
        parser_result = await parser.parse(agent_result, context)
        
        # Verify parser output
        assert parser_result.success, f"Parser should succeed, got: {parser_result.error_message}"
        assert parser_result.command_data is not None, "Parser should return command data"
        
        commands = parser_result.command_data
        print(f"📋 Commands Created: {len(commands)}")
        print(f"📋 Commands Type: {type(commands)}")
        print(f"📋 Commands Content: {commands}")
        
        for i, cmd in enumerate(commands):
            print(f"  Command {i+1}: Type={type(cmd)}, Content={cmd}")
            if isinstance(cmd, dict):
                print(f"    Intent: {cmd.get('intent', 'N/A')}")
                if 'slots' in cmd:
                    print(f"    Slots: {cmd['slots']}")
            else:
                print(f"    Not a dict: {cmd}")
        
        # STEP 3: Validate Commands
        print(f"\n🔍 STEP 3: Validating Commands")
        print("-" * 40)
        
        from app.commands.command_data_validator import CommandDataValidator
        
        # Validate each command
        for i, command in enumerate(commands):
            if isinstance(command, dict):
                is_valid, errors = CommandDataValidator.validate(command)
                if not is_valid:
                    error_summary = CommandDataValidator.get_validation_summary(errors)
                    assert False, f"Command {i+1} failed validation: {error_summary}"
                print(f"  ✅ Command {i+1}: Valid")
            else:
                assert False, f"Command {i+1} is not a dict: {type(command)} - {command}"
        
        # STEP 4: Verify Expected Results
        print(f"\n🔍 STEP 4: Verifying Expected Results")
        print("-" * 40)
        
        # Should have 3 commands (one for each item)
        assert len(commands) == 3, f"Expected 3 commands, got {len(commands)}"
        
        # Extract menu item IDs from commands
        command_ids = []
        for cmd in commands:
            if isinstance(cmd, dict) and 'slots' in cmd:
                command_ids.append(cmd['slots']['menu_item_id'])
            else:
                assert False, f"Command is not properly structured: {cmd}"
        
        print(f"📋 Command IDs: {command_ids}")
        
        # Should have the correct menu item IDs
        expected_ids = [1, 3, 9]  # Quantum Cheeseburger, Veggie Nebula Wrap, Lunar Lemonade
        assert set(command_ids) == set(expected_ids), f"Expected IDs {expected_ids}, got {command_ids}"
        
        # All commands should be ADD_ITEM
        for cmd in commands:
            if isinstance(cmd, dict):
                assert cmd['intent'] == 'ADD_ITEM', f"Expected ADD_ITEM, got {cmd['intent']}"
            else:
                assert False, f"Command is not a dict: {cmd}"
        
        print(f"\n✅ Agent + Parser Integration Test Completed!")
        print(f"🎯 Expected: 3 items → 3 commands with correct IDs")
        print(f"🎯 Result: {len(commands)} commands with IDs {command_ids}")

    @pytest.mark.asyncio
    async def test_agent_parser_single_item_flow(self):
        """Test complete flow: Agent → Parser → Commands for single item"""
        
        print("\n🧪 TESTING AGENT + PARSER INTEGRATION - SINGLE ITEM")
        print("=" * 70)

        user_input = "I want a quantum cheeseburger"
        restaurant_id = "1"

        # Create workflow state
        state = ConversationWorkflowState(
            session_id="test-session-single-1",
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

        # Mock container with services (same as above)
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/single-item-test.mp3"
        container.services['voice_service'] = mock_voice_service

        # Mock MenuService
        mock_menu_service = AsyncMock()
        
        # Create menu items
        menu_items = [
            TestDataFactory.create_menu_item(1, "Quantum Cheeseburger", 7.99, "A delicious quantum cheeseburger"),
            TestDataFactory.create_menu_item(2, "Neon Double Burger", 8.99, "A neon double burger"),
            TestDataFactory.create_menu_item(3, "Veggie Nebula Wrap", 6.99, "A veggie nebula wrap")
        ]
        
        # Mock the async methods using AsyncMock properly
        mock_menu_service.get_available_items_for_restaurant = AsyncMock(return_value=menu_items)
        mock_menu_service.get_menu_categories = AsyncMock(return_value=["Sandwiches"])
        mock_menu_service.get_menu_items_by_category = AsyncMock(return_value={
            "Sandwiches": ["Quantum Cheeseburger", "Neon Double Burger", "Veggie Nebula Wrap"]
        })
        mock_menu_service.get_menu_item_ingredients = AsyncMock(return_value=[
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0}
        ])
        mock_menu_service.get_all_ingredients_with_costs = AsyncMock(return_value=[
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False}
        ])
        mock_menu_service.get_restaurant_name = AsyncMock(return_value="Test Restaurant")
        container.services['menu_service'] = mock_menu_service

        # Mock RestaurantService
        mock_restaurant_service = AsyncMock()
        mock_restaurant_service.get_restaurant_info.return_value = {
            "id": 1,
            "name": "Test Restaurant",
            "description": "A test restaurant"
        }
        container.services['restaurant_service'] = mock_restaurant_service

        # Create service factory
        from app.core.service_factory import ServiceFactory
        service_factory = ServiceFactory(container)
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        context = {
            "container": container,
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": state.conversation_history,
            "order_state": state.order_state.__dict__ if state.order_state else {},
            "restaurant_id": state.restaurant_id
        }

        print(f"📝 User Input: '{user_input}'")

        # Test Agent
        agent_result = await add_item_agent(state.normalized_user_input, context)
        
        # Test Parser
        parser = AddItemParser()
        parser_result = await parser.parse(agent_result, context)
        
        # Verify results
        assert parser_result.success, f"Parser should succeed, got: {parser_result.error_message}"
        
        commands = parser_result.command_data
        assert len(commands) == 1, f"Expected 1 command, got {len(commands)}"
        
        command = commands[0]
        assert command['intent'] == 'ADD_ITEM', f"Expected ADD_ITEM, got {command['intent']}"
        assert command['slots']['menu_item_id'] == 1, f"Expected menu_item_id 1, got {command['slots']['menu_item_id']}"
        
        print(f"✅ Single item test completed!")
        print(f"🎯 Result: 1 command with ID {command['slots']['menu_item_id']}")

    @pytest.mark.asyncio
    async def test_agent_parser_mixed_scenario_flow(self):
        """Test complete flow: Agent → Parser → Commands for mixed scenario with unknown items"""
        
        print("\n🧪 TESTING AGENT + PARSER INTEGRATION - MIXED SCENARIO")
        print("=" * 70)
        
        user_input = "I want a pheasant a nebula wrap and a slice of galaxy pie"
        restaurant_id = "1"
        
        # Create workflow state
        state = ConversationWorkflowState(
            session_id="test-session-mixed-1",
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
        
        # Mock container with services
        container = MockContainer()
        
        # Mock voice service
        mock_voice_service = AsyncMock()
        mock_voice_service.generate_audio.return_value = "https://mock-audio-url.com/mixed-scenario-test.mp3"
        container.services['voice_service'] = mock_voice_service
        
        # Mock MenuService with the actual menu items from the database
        mock_menu_service = AsyncMock()
        
        # Create menu items that match the database
        menu_items = [
            TestDataFactory.create_menu_item(1, "Quantum Cheeseburger", 7.99, "A delicious quantum cheeseburger"),        
            TestDataFactory.create_menu_item(2, "Neon Double Burger", 8.99, "A neon double burger"),
            TestDataFactory.create_menu_item(3, "Veggie Nebula Wrap", 6.99, "A veggie nebula wrap"),
            TestDataFactory.create_menu_item(4, "Spicy Meteor Chicken", 7.99, "Spicy meteor chicken"),
            TestDataFactory.create_menu_item(5, "Galactic Fries", 3.99, "Galactic fries"),
            TestDataFactory.create_menu_item(6, "Cosmic Onion Rings", 4.99, "Cosmic onion rings"),
            TestDataFactory.create_menu_item(7, "Astro Nuggets", 5.99, "Astro nuggets"),
            TestDataFactory.create_menu_item(8, "Starlight Salad", 6.99, "Starlight salad"),
            TestDataFactory.create_menu_item(9, "Lunar Lemonade", 1.99, "Lunar lemonade"),
            TestDataFactory.create_menu_item(10, "Quantum Cola", 1.99, "Quantum cola")
        ]
        
        # Mock the async methods using AsyncMock properly
        mock_menu_service.get_available_items_for_restaurant = AsyncMock(return_value=menu_items)
        mock_menu_service.get_menu_categories = AsyncMock(return_value=["Sandwiches", "Sides", "Drinks"])
        mock_menu_service.get_menu_items_by_category = AsyncMock(return_value={
            "Sandwiches": ["Quantum Cheeseburger", "Neon Double Burger", "Veggie Nebula Wrap", "Spicy Meteor Chicken"],   
            "Sides": ["Galactic Fries", "Cosmic Onion Rings", "Astro Nuggets", "Starlight Salad"],
            "Drinks": ["Lunar Lemonade", "Quantum Cola"]
        })
        mock_menu_service.get_menu_item_ingredients = AsyncMock(return_value=[
            {"name": "beef patty", "is_optional": False, "is_allergen": False, "additional_cost": 0.0},
            {"name": "lettuce", "is_optional": False, "is_allergen": False, "additional_cost": 0.0}
        ])
        mock_menu_service.get_all_ingredients_with_costs = AsyncMock(return_value=[
            {"name": "beef patty", "unit_cost": 0.0, "is_allergen": False},
            {"name": "lettuce", "unit_cost": 0.0, "is_allergen": False}
        ])
        mock_menu_service.get_restaurant_name = AsyncMock(return_value="Test Restaurant")
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
        
        # Override the service factory to use mocked services
        service_factory.create_menu_service = lambda db_session: mock_menu_service
        service_factory.create_restaurant_service = lambda db_session: mock_restaurant_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        context = {
            "container": container,
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": state.conversation_history,
            "order_state": state.order_state.__dict__ if state.order_state else {},
            "restaurant_id": state.restaurant_id
        }
        
        print(f"📝 User Input: '{user_input}'")
        print(f"🏪 Restaurant: {mock_restaurant_service.get_restaurant_info.return_value['name']}")
        print(f"📋 Menu Items: {len(menu_items)} items available")
        print(f"🎯 Expected: 1 known item (Nebula Wrap), 2 unknown items (Pheasant, Galaxy Pie)")
        
        # STEP 1: Test the Agent
        print(f"\n🔍 STEP 1: Testing AddItemAgent")
        print("-" * 40)
        
        agent_result = await add_item_agent(state.normalized_user_input, context)
        
        # Verify agent output
        assert agent_result is not None, "Agent should return AddItemResponse"
        assert hasattr(agent_result, 'items_to_add'), "Agent should return items_to_add"
        
        agent_response = agent_result
        print(f"📝 Agent Response: '{agent_response.response_text}'")
        print(f"🎯 Response Type: {agent_response.response_type}")
        print(f"📋 Items to Add: {len(agent_response.items_to_add)}")
        
        for i, item in enumerate(agent_response.items_to_add):
            print(f"  Item {i+1}: ID={item.menu_item_id}, Qty={item.quantity}")
            if hasattr(item, 'ambiguous_item') and item.ambiguous_item:
                print(f"    Ambiguous: {item.ambiguous_item}")
            if hasattr(item, 'suggested_options') and item.suggested_options:
                print(f"    Suggested: {item.suggested_options}")
        
        # STEP 2: Test the Parser
        print(f"\n🔍 STEP 2: Testing AddItemParser")
        print("-" * 40)
        
        # Create parser
        parser = AddItemParser()
        
        # Parse the agent's output
        parser_result = await parser.parse(agent_result, context)
        
        # Verify parser output
        assert parser_result.success, f"Parser should succeed, got: {parser_result.error_message}"
        assert parser_result.command_data is not None, "Parser should return command data"
        
        commands = parser_result.command_data
        print(f"📋 Commands Created: {len(commands)}")
        print(f"📋 Commands Type: {type(commands)}")
        print(f"📋 Commands Content: {commands}")
        
        for i, cmd in enumerate(commands):
            print(f"  Command {i+1}: Type={type(cmd)}, Content={cmd}")
            if isinstance(cmd, dict):
                print(f"    Intent: {cmd.get('intent', 'N/A')}")
                if 'slots' in cmd:
                    print(f"    Slots: {cmd['slots']}")
            else:
                print(f"    Not a dict: {cmd}")
        
        # STEP 3: Validate Commands
        print(f"\n🔍 STEP 3: Validating Commands")
        print("-" * 40)
        
        from app.commands.command_data_validator import CommandDataValidator
        
        # Validate each command
        for i, command in enumerate(commands):
            if isinstance(command, dict):
                is_valid, errors = CommandDataValidator.validate(command)
                if not is_valid:
                    error_summary = CommandDataValidator.get_validation_summary(errors)
                    assert False, f"Command {i+1} failed validation: {error_summary}"
                print(f"  ✅ Command {i+1}: Valid")
            else:
                assert False, f"Command {i+1} is not a dict: {type(command)} - {command}"
        
        # STEP 4: Verify Expected Results
        print(f"\n🔍 STEP 4: Verifying Expected Results")
        print("-" * 40)
        
        # Should have at least 1 command (the known item)
        assert len(commands) >= 1, f"Expected at least 1 command, got {len(commands)}"
        
        # Extract command details
        command_intents = []
        command_ids = []
        clarification_commands = []
        
        for cmd in commands:
            if isinstance(cmd, dict):
                command_intents.append(cmd.get('intent', 'UNKNOWN'))
                if cmd.get('intent') == 'ADD_ITEM' and 'slots' in cmd:
                    command_ids.append(cmd['slots'].get('menu_item_id'))
                elif cmd.get('intent') == 'CLARIFICATION_NEEDED':
                    clarification_commands.append(cmd)
        
        print(f"📋 Command Intents: {command_intents}")
        print(f"📋 Command IDs: {command_ids}")
        print(f"📋 Clarification Commands: {len(clarification_commands)}")
        
        # Should have exactly 3 commands total
        assert len(commands) == 3, f"Expected exactly 3 commands, got: {len(commands)}"

        # The agent is currently being cautious and creating all CLARIFICATION_NEEDED
        # This is actually correct behavior - it's asking for clarification on all items
        assert 'CLARIFICATION_NEEDED' in command_intents, f"Expected CLARIFICATION_NEEDED commands, got: {command_intents}"
        
        # Should have exactly 3 commands total
        add_item_count = command_intents.count('ADD_ITEM')
        clarification_count = command_intents.count('CLARIFICATION_NEEDED')
        
        # The agent is correctly finding matches and creating appropriate commands
        # Should have 1 ADD_ITEM + 2 CLARIFICATION_NEEDED = 3 total commands
        assert add_item_count == 1, f"Expected exactly 1 ADD_ITEM command, got: {add_item_count}"
        assert clarification_count == 2, f"Expected exactly 2 CLARIFICATION_NEEDED commands, got: {clarification_count}"
        assert len(commands) == 3, f"Expected exactly 3 commands total, got: {len(commands)}"
        
        print(f"✅ Agent correctly handled mixed scenario: {add_item_count} ADD_ITEM + {clarification_count} CLARIFICATION_NEEDED")
        
        # The known item should be Nebula Wrap (ID: 3)
        if 3 in command_ids:
            print(f"✅ Found Nebula Wrap (ID: 3) - known item correctly identified")
        
        print(f"\n✅ Agent + Parser Integration Test Completed!")
        print(f"🎯 Expected: Mixed scenario with known and unknown items")
        print(f"🎯 Result: {len(commands)} commands with intents {command_intents}")
        print(f"🎯 Known items: {command_ids}")
        print(f"🎯 Clarification needed: {len(clarification_commands)} items")


if __name__ == "__main__":
    # Run the tests
    import asyncio
    
    async def run_tests():
        test_instance = TestAgentParserIntegration()
        
        print("🚀 Running Agent + Parser Integration Tests")
        print("=" * 70)
        
        try:
            await test_instance.test_agent_parser_single_item_flow()
            await test_instance.test_agent_parser_multi_item_flow()
            
            print("\n🎉 All integration tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())
