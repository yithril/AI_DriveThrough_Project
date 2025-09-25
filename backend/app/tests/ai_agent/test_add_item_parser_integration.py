"""
Integration tests for AddItemParser with two-agent pipeline

Tests the full pipeline: Item Extraction Agent → Menu Resolution Agent → Commands
Mocks the menu service to test real agent behavior without database dependencies.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from app.agents.parser.add_item_parser import AddItemParser
from app.core.service_factory import ServiceFactory


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


class TestAddItemParserIntegration:
    """Integration tests for AddItemParser with two-agent pipeline"""
    
    @pytest.mark.asyncio
    async def test_parser_with_clear_items(self):
        """Test parser with clear items that exist on menu"""
        
        # Create mock container and services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        
        # Mock menu service with clear items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "Classic Burger", "French Fries", "Large French Fries"
        ]
        mock_menu_service.get_menu_item_ingredients.return_value = [
            {"name": "beef patty"}, {"name": "lettuce"}, {"name": "tomato"}
        ]
        # Mock the new search method
        async def mock_search_menu_items(restaurant_id, query):
            all_items = ["Quantum Burger", "Classic Burger", "French Fries", "Large French Fries"]
            query_lower = query.lower()
            matching = []
            for item in all_items:
                if query_lower in item.lower():
                    matching.append(item)
            return matching
        mock_menu_service.search_menu_items = mock_search_menu_items
        
        # Mock the service factory to return our mocked services
        service_factory.create_menu_service = lambda db_session: mock_menu_service
        service_factory.create_restaurant_service = lambda db_session: AsyncMock()
        
        container.services['menu_service'] = mock_menu_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        # Create context
        context = {
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": [],
            "order_state": {},
            "restaurant_id": "1"
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing with items that should match
        result = await parser.parse("I want a quantum burger and fries", context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Should return a list of commands
        commands = result.command_data
        assert isinstance(commands, list), "Should return list of commands"
        assert len(commands) == 2, "Should have 2 commands for 2 items"
        
        # Check that we got the right types of commands
        command_types = [cmd["intent"] for cmd in commands]
        assert "ADD_ITEM" in command_types, "Should have ADD_ITEM commands for clear matches"
        assert "CLARIFICATION_NEEDED" in command_types, "Should have CLARIFICATION_NEEDED commands for ambiguous items"
    
    @pytest.mark.asyncio
    async def test_parser_with_ambiguous_items(self):
        """Test parser with ambiguous items that need clarification"""
        
        # Create mock container and services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        
        # Mock menu service with items that include ambiguous matches
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "French Fries", "Large French Fries", "Chicken Nuggets", "Salad", "Quantum Burger", "Classic Burger"
        ]
        # Mock the new search method
        async def mock_search_menu_items(restaurant_id, query):
            all_items = ["French Fries", "Large French Fries", "Chicken Nuggets", "Salad", "Quantum Burger", "Classic Burger"]
            query_lower = query.lower()
            matching = []
            for item in all_items:
                if query_lower in item.lower():
                    matching.append(item)
            return matching
        mock_menu_service.search_menu_items = mock_search_menu_items
        
        # Mock the service factory to return our mocked services
        service_factory.create_menu_service = lambda db_session: mock_menu_service
        service_factory.create_restaurant_service = lambda db_session: AsyncMock()
        
        container.services['menu_service'] = mock_menu_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        # Create context
        context = {
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": [],
            "order_state": {},
            "restaurant_id": "1"
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing with ambiguous item
        result = await parser.parse("I want a burger", context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Should return a list of commands
        commands = result.command_data
        assert isinstance(commands, list), "Should return list of commands"
        assert len(commands) == 1, "Should have 1 command"
        
        # Check that we got clarification command
        assert commands[0]["intent"] == "CLARIFICATION_NEEDED", "Should be CLARIFICATION_NEEDED command"
    
    @pytest.mark.asyncio
    async def test_parser_with_mixed_items(self):
        """Test parser with mix of clear and ambiguous items"""
        
        # Create mock container and services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        
        # Mock menu service with some items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "French Fries", "Large French Fries", "Chicken Nuggets", "Quantum Burger", "Classic Burger"
        ]
        # Mock the new search method
        async def mock_search_menu_items(restaurant_id, query):
            all_items = ["French Fries", "Large French Fries", "Chicken Nuggets", "Quantum Burger", "Classic Burger"]
            query_lower = query.lower()
            matching = []
            for item in all_items:
                if query_lower in item.lower():
                    matching.append(item)
            return matching
        mock_menu_service.search_menu_items = mock_search_menu_items
        
        # Mock the service factory to return our mocked services
        service_factory.create_menu_service = lambda db_session: mock_menu_service
        service_factory.create_restaurant_service = lambda db_session: AsyncMock()
        
        container.services['menu_service'] = mock_menu_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        # Create context
        context = {
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": [],
            "order_state": {},
            "restaurant_id": "1"
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing with mixed items
        result = await parser.parse("I want fries and a burger", context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Should return a list of commands
        commands = result.command_data
        assert isinstance(commands, list), "Should return list of commands"
        assert len(commands) == 2, "Should have 2 commands for 2 items"
        
        # Check command types
        command_types = [cmd["intent"] for cmd in commands]
        assert "CLARIFICATION_NEEDED" in command_types, "Should have CLARIFICATION_NEEDED commands for ambiguous items"
    
    @pytest.mark.asyncio
    async def test_parser_with_unknown_items(self):
        """Test parser with items that don't exist on menu"""
        
        # Create mock container and services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        
        # Mock menu service with limited items (no exotic items)
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "French Fries", "Burger", "Salad", "Chicken Nuggets"
        ]
        # Mock the new search method
        async def mock_search_menu_items(restaurant_id, query):
            all_items = ["French Fries", "Burger", "Salad", "Chicken Nuggets"]
            query_lower = query.lower()
            matching = []
            for item in all_items:
                if query_lower in item.lower():
                    matching.append(item)
            return matching
        mock_menu_service.search_menu_items = mock_search_menu_items
        
        container.services['menu_service'] = mock_menu_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        # Create context
        context = {
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": [],
            "order_state": {},
            "restaurant_id": "1"
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing with unknown items
        result = await parser.parse("I want pheasant and sushi", context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Should return a list of commands
        commands = result.command_data
        assert isinstance(commands, list), "Should return list of commands"
        assert len(commands) == 2, "Should have 2 commands for 2 items"
        
        # Check that we got ITEM_UNAVAILABLE commands
        command_types = [cmd["intent"] for cmd in commands]
        assert "ITEM_UNAVAILABLE" in command_types, "Should have ITEM_UNAVAILABLE commands for unknown items"
    
    @pytest.mark.asyncio
    async def test_parser_with_mixed_known_unknown_items(self):
        """Test parser with mix of known and unknown items"""
        
        # Create mock container and services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        
        # Mock menu service with some items
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "French Fries", "Burger", "Salad"
        ]
        # Mock the new search method
        async def mock_search_menu_items(restaurant_id, query):
            all_items = ["French Fries", "Burger", "Salad"]
            query_lower = query.lower()
            matching = []
            for item in all_items:
                if query_lower in item.lower():
                    matching.append(item)
            return matching
        mock_menu_service.search_menu_items = mock_search_menu_items
        
        # Mock the service factory to return our mocked services
        service_factory.create_menu_service = lambda db_session: mock_menu_service
        service_factory.create_restaurant_service = lambda db_session: AsyncMock()
        
        container.services['menu_service'] = mock_menu_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        # Create context
        context = {
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": [],
            "order_state": {},
            "restaurant_id": "1"
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing with mixed items
        result = await parser.parse("I want fries and pheasant", context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Should return a list of commands
        commands = result.command_data
        assert isinstance(commands, list), "Should return list of commands"
        assert len(commands) == 2, "Should have 2 commands for 2 items"
        
        # Check command types
        command_types = [cmd["intent"] for cmd in commands]
        assert "ADD_ITEM" in command_types, "Should have ADD_ITEM commands for known items"
        assert "ITEM_UNAVAILABLE" in command_types, "Should have ITEM_UNAVAILABLE commands for unknown items"


def run_test():
    """Run a single test to verify the parser works"""
    async def test():
        # Create mock container and services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        mock_menu_service.get_available_items_for_restaurant.return_value = [
            "Quantum Burger", "French Fries", "Large French Fries"
        ]
        
        container.services['menu_service'] = mock_menu_service
        
        # Mock database session
        mock_db_session = AsyncMock()
        
        # Create context
        context = {
            "service_factory": service_factory,
            "shared_db_session": mock_db_session,
            "conversation_history": [],
            "order_state": {},
            "restaurant_id": "1"
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing
        result = await parser.parse("I want a quantum burger and large fries", context)
        
        print(f"\n🔍 ADD_ITEM PARSER INTEGRATION TEST:")
        print(f"   Success: {result.success}")
        if result.success:
            print(f"   Commands: {len(result.command_data)}")
            for i, cmd in enumerate(result.command_data):
                print(f"     Command {i+1}: {cmd['intent']}")
                if 'slots' in cmd:
                    print(f"       Slots: {list(cmd['slots'].keys())}")
        else:
            print(f"   Error: {result.error_message}")
        
        return result
    
    return asyncio.run(test())


if __name__ == "__main__":
    run_test()
