"""
Unit tests for Menu Resolution Agent

Tests the refactored agent that uses direct service calls + LLM for disambiguation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agents.command_agents.menu_resolution_agent import menu_resolution_agent
from app.agents.agent_response.menu_resolution_response import MenuResolutionResponse, ResolvedItem
from app.agents.agent_response.item_extraction_response import ItemExtractionResponse, ExtractedItem


class TestMenuResolutionAgent:
    """Unit tests for Menu Resolution Agent"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        factory = Mock()
        factory.create_menu_service.return_value = Mock()
        return factory
    
    @pytest.fixture
    def mock_menu_service(self):
        """Mock menu service"""
        service = Mock()
        service.search_menu_items = AsyncMock()
        service.get_menu_item_by_name = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def context(self, mock_service_factory, mock_db_session):
        """Test context"""
        return {
            "service_factory": mock_service_factory,
            "shared_db_session": mock_db_session,
            "restaurant_id": "1"
        }
    
    @pytest.fixture
    def extraction_response(self):
        """Sample extraction response"""
        return ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="Quantum Cheeseburger",
                    quantity=1,
                    confidence=0.9
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_single_match_success(self, context, extraction_response, mock_service_factory, mock_menu_service):
        """Test successful resolution with single match"""
        # Setup mocks
        mock_service_factory.create_menu_service.return_value = mock_menu_service
        mock_menu_service.search_menu_items.return_value = ["Quantum Cheeseburger"]
        
        mock_menu_item = Mock()
        mock_menu_item.id = 123
        mock_menu_service.get_menu_item_by_name.return_value = mock_menu_item
        
        # Run agent
        result = await menu_resolution_agent(extraction_response, context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is True
        assert result.confidence == 0.9
        assert len(result.resolved_items) == 1
        
        resolved_item = result.resolved_items[0]
        assert resolved_item.item_name == "Quantum Cheeseburger"
        assert resolved_item.resolved_name == "Quantum Cheeseburger"
        assert resolved_item.menu_item_id == 123
        assert resolved_item.confidence == 0.9
        assert resolved_item.is_ambiguous is False
        
        # Verify service calls
        mock_menu_service.search_menu_items.assert_called_once_with(1, "Quantum Cheeseburger")
        mock_menu_service.get_menu_item_by_name.assert_called_once_with(1, "Quantum Cheeseburger")
    
    @pytest.mark.asyncio
    async def test_no_matches_unavailable(self, context, extraction_response, mock_service_factory, mock_menu_service):
        """Test resolution when no matches found"""
        # Setup mocks
        mock_service_factory.create_menu_service.return_value = mock_menu_service
        mock_menu_service.search_menu_items.return_value = []
        
        # Run agent
        result = await menu_resolution_agent(extraction_response, context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is False  # No successful resolutions
        assert len(result.resolved_items) == 1
        
        resolved_item = result.resolved_items[0]
        assert resolved_item.item_name == "Quantum Cheeseburger"
        assert resolved_item.resolved_name is None
        assert resolved_item.menu_item_id == 0
        assert resolved_item.confidence == 0.0
        assert resolved_item.is_ambiguous is False
        assert "don't have" in resolved_item.clarification_question
    
    @pytest.mark.asyncio
    async def test_multiple_matches_llm_disambiguation(self, context, extraction_response, mock_service_factory, mock_menu_service):
        """Test LLM disambiguation for multiple matches"""
        # Setup mocks
        mock_service_factory.create_menu_service.return_value = mock_menu_service
        mock_menu_service.search_menu_items.return_value = ["Quantum Cheeseburger", "Neon Double Burger", "Big Mac"]
        
        mock_menu_item = Mock()
        mock_menu_item.id = 123
        mock_menu_service.get_menu_item_by_name.return_value = mock_menu_item
        
        # Mock LLM response with proper async mock
        with patch('app.agents.command_agents.menu_resolution_agent.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            mock_llm.ainvoke.return_value = Mock(content="Quantum Cheeseburger")
            
            # Run agent
            result = await menu_resolution_agent(extraction_response, context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is True
        assert len(result.resolved_items) == 1
        
        resolved_item = result.resolved_items[0]
        assert resolved_item.item_name == "Quantum Cheeseburger"
        assert resolved_item.resolved_name == "Quantum Cheeseburger"
        assert resolved_item.menu_item_id == 123
        assert resolved_item.confidence == 0.8
        assert resolved_item.is_ambiguous is False
        
        # Verify LLM was called for disambiguation
        mock_llm.ainvoke.assert_called_once()
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert "Quantum Cheeseburger" in call_args
        assert "Neon Double Burger" in call_args
    
    @pytest.mark.asyncio
    async def test_multiple_matches_llm_fails_clarification(self, context, extraction_response, mock_service_factory, mock_menu_service):
        """Test when LLM disambiguation fails and needs clarification"""
        # Setup mocks
        mock_service_factory.create_menu_service.return_value = mock_menu_service
        mock_menu_service.search_menu_items.return_value = ["Quantum Cheeseburger", "Neon Double Burger", "Big Mac"]
        
        # Mock LLM response that doesn't match any option
        with patch('app.agents.command_agents.menu_resolution_agent.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            mock_llm.ainvoke.return_value = Mock(content="Something else")
            
            # Run agent
            result = await menu_resolution_agent(extraction_response, context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is False  # Needs clarification
        assert result.needs_clarification is True
        assert len(result.resolved_items) == 1
        
        resolved_item = result.resolved_items[0]
        assert resolved_item.item_name == "Quantum Cheeseburger"
        assert resolved_item.resolved_name is None
        assert resolved_item.menu_item_id == 0
        assert resolved_item.confidence == 0.5
        assert resolved_item.is_ambiguous is True
        assert len(resolved_item.suggested_options) == 3
        assert "Did you mean" in resolved_item.clarification_question
    
    @pytest.mark.asyncio
    async def test_extraction_failure(self, context):
        """Test handling of failed extraction"""
        # Create failed extraction response with at least one item (Pydantic validation)
        failed_extraction = ItemExtractionResponse(
            success=False,
            confidence=0.0,
            extracted_items=[
                ExtractedItem(item_name="test", quantity=1, confidence=0.0)
            ]
        )
        
        # Run agent
        result = await menu_resolution_agent(failed_extraction, context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is False
        assert result.confidence == 0.0
        assert len(result.resolved_items) == 0  # No items processed when extraction fails
        assert result.needs_clarification is True
    
    @pytest.mark.asyncio
    async def test_missing_context(self, extraction_response):
        """Test handling of missing context"""
        # Create context without required services
        bad_context = {"restaurant_id": "1"}
        
        # Run agent
        result = await menu_resolution_agent(extraction_response, bad_context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is False
        assert result.confidence == 0.0
        assert len(result.resolved_items) == 0
        assert result.needs_clarification is True
        assert "error accessing the menu" in result.clarification_questions[0]
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, context, extraction_response, mock_service_factory, mock_menu_service):
        """Test handling of database errors"""
        # Setup mocks to raise exception
        mock_service_factory.create_menu_service.return_value = mock_menu_service
        mock_menu_service.search_menu_items.side_effect = Exception("Database error")
        
        # Run agent
        result = await menu_resolution_agent(extraction_response, context)
        
        # Verify result - database error should return empty list
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is False
        assert result.confidence == 0.0
        assert len(result.resolved_items) == 0  # No items processed when database error occurs
        assert result.needs_clarification is True
        assert "error accessing the menu" in result.clarification_questions[0]
    
    @pytest.mark.asyncio
    async def test_multiple_items_mixed_results(self, context, mock_service_factory, mock_menu_service):
        """Test resolution of multiple items with mixed results"""
        # Create extraction response with multiple items
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.8,
            extracted_items=[
                ExtractedItem(item_name="Quantum Cheeseburger", quantity=1, confidence=0.9),
                ExtractedItem(item_name="Pizza", quantity=1, confidence=0.7),  # Not available
                ExtractedItem(item_name="Fries", quantity=2, confidence=0.8)
            ]
        )
        
        # Setup mocks
        mock_service_factory.create_menu_service.return_value = mock_menu_service
        
        def mock_search(restaurant_id, query):
            if query == "Quantum Cheeseburger":
                return ["Quantum Cheeseburger"]
            elif query == "Pizza":
                return []
            elif query == "Fries":
                return ["French Fries", "Sweet Potato Fries"]
            return []
        
        mock_menu_service.search_menu_items.side_effect = mock_search
        
        # Mock menu item for successful matches
        mock_menu_item = Mock()
        mock_menu_item.id = 123
        mock_menu_service.get_menu_item_by_name.return_value = mock_menu_item
        
        # Mock LLM for fries disambiguation
        with patch('app.agents.command_agents.menu_resolution_agent.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            mock_llm.ainvoke.return_value = Mock(content="French Fries")
            
            # Run agent
            result = await menu_resolution_agent(extraction_response, context)
        
        # Verify result
        assert isinstance(result, MenuResolutionResponse)
        assert len(result.resolved_items) == 3
        
        # Check Quantum Cheeseburger (success)
        burger_item = next(item for item in result.resolved_items if item.item_name == "Quantum Cheeseburger")
        assert burger_item.resolved_name == "Quantum Cheeseburger"
        assert burger_item.menu_item_id == 123
        assert burger_item.is_ambiguous is False
        
        # Check Pizza (unavailable)
        pizza_item = next(item for item in result.resolved_items if item.item_name == "Pizza")
        assert pizza_item.resolved_name is None
        assert pizza_item.menu_item_id == 0
        assert pizza_item.is_ambiguous is False
        
        # Check Fries (LLM disambiguation)
        fries_item = next(item for item in result.resolved_items if item.item_name == "Fries")
        assert fries_item.resolved_name == "French Fries"
        assert fries_item.menu_item_id == 123
        assert fries_item.is_ambiguous is False
