"""
Unit tests for IntentParserRouterService
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.core.services.conversation.intent_parser_router_service import IntentParserRouterService
from app.commands.intent_classification_schema import IntentType


class TestIntentParserRouterService:
    """Test cases for IntentParserRouterService"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_service_factory):
        """Create service with mocked dependencies"""
        return IntentParserRouterService(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_route_to_parser_add_item_success(self, service, mocker):
        """Test successful ADD_ITEM parsing"""
        # Mock the add item parser
        mock_parser = service.parsers[IntentType.ADD_ITEM]
        mock_parser.parse = AsyncMock()
        mock_parser.parse.return_value = Mock(
            success=True,
            is_multiple_commands=lambda: False,
            command_data={"intent": "ADD_ITEM", "menu_item_id": 1, "quantity": 1}
        )
        
        # Test the service
        result = await service.route_to_parser(
            intent_type=IntentType.ADD_ITEM,
            user_input="add a burger",
            restaurant_id="1",
            session_id="test-session",
            conversation_history=[],
            order_state={},
            current_state="ORDERING"
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["commands"]) == 1
        assert result["commands"][0]["intent"] == "ADD_ITEM"
    
    @pytest.mark.asyncio
    async def test_route_to_parser_clear_order_success(self, service, mocker):
        """Test successful CLEAR_ORDER parsing"""
        # Mock the clear order parser
        mock_parser = service.parsers[IntentType.CLEAR_ORDER]
        mock_parser.parse = AsyncMock()
        mock_parser.parse.return_value = Mock(
            success=True,
            is_multiple_commands=lambda: False,
            command_data={"intent": "CLEAR_ORDER"}
        )
        
        # Test the service
        result = await service.route_to_parser(
            intent_type=IntentType.CLEAR_ORDER,
            user_input="clear my order",
            restaurant_id="1",
            session_id="test-session",
            conversation_history=[],
            order_state={},
            current_state="ORDERING"
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["commands"]) == 1
        assert result["commands"][0]["intent"] == "CLEAR_ORDER"
    
    @pytest.mark.asyncio
    async def test_route_to_parser_failure(self, service, mocker):
        """Test parser failure"""
        # Mock the parser to return failure
        mock_parser = service.parsers[IntentType.ADD_ITEM]
        mock_parser.parse = AsyncMock()
        mock_parser.parse.return_value = Mock(
            success=False,
            error_message="Parser failed"
        )
        
        # Test the service
        result = await service.route_to_parser(
            intent_type=IntentType.ADD_ITEM,
            user_input="add a burger",
            restaurant_id="1",
            session_id="test-session",
            conversation_history=[],
            order_state={},
            current_state="ORDERING"
        )
        
        # Verify result
        assert result["success"] is False
        assert "didn't understand" in result["response_text"]
        assert len(result["commands"]) == 0
    
    @pytest.mark.asyncio
    async def test_route_to_parser_exception_fallback(self, service, mocker):
        """Test parser exception with fallback to unknown parser"""
        # Mock the main parser to raise exception
        mock_parser = service.parsers[IntentType.ADD_ITEM]
        mock_parser.parse = AsyncMock()
        mock_parser.parse.side_effect = Exception("Parser failed")
        
        # Mock the unknown parser to succeed
        mock_unknown_parser = service.parsers[IntentType.UNKNOWN]
        mock_unknown_parser.parse = AsyncMock()
        mock_unknown_parser.parse.return_value = Mock(
            success=True,
            is_multiple_commands=lambda: False,
            command_data={"intent": "UNKNOWN"}
        )
        
        # Test the service
        result = await service.route_to_parser(
            intent_type=IntentType.ADD_ITEM,
            user_input="add a burger",
            restaurant_id="1",
            session_id="test-session",
            conversation_history=[],
            order_state={},
            current_state="ORDERING"
        )
        
        # Verify fallback was used
        assert result["success"] is True
        assert len(result["commands"]) == 1
        assert result["commands"][0]["intent"] == "UNKNOWN"
    
    def test_get_supported_intents(self, service):
        """Test getting supported intent types"""
        intents = service.get_supported_intents()
        assert IntentType.ADD_ITEM in intents
        assert IntentType.CLEAR_ORDER in intents
        assert IntentType.QUESTION in intents
        assert IntentType.UNKNOWN in intents
