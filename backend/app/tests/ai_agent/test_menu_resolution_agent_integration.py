"""
Integration tests for Menu Resolution Agent

Tests the agent with real LLM calls and database access to ensure it properly resolves items against the menu.
"""

import pytest
import asyncio
from app.agents.command_agents.menu_resolution_agent import menu_resolution_agent
from app.agents.agent_response.menu_resolution_response import MenuResolutionResponse, ResolvedItem
from app.agents.agent_response.item_extraction_response import ItemExtractionResponse, ExtractedItem
from app.core.service_factory import ServiceFactory
from app.core.database import get_async_session
from unittest.mock import AsyncMock


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


class TestMenuResolutionAgentIntegration:
    """Integration tests for Menu Resolution Agent"""
    
    @pytest.mark.asyncio
    async def test_resolve_clear_items(self):
        """Test resolution of clear, unambiguous items"""
        # Create extraction response with clear items
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="Big Mac",
                    quantity=1,
                    confidence=0.9
                ),
                ExtractedItem(
                    item_name="fries",
                    quantity=2,
                    size="large",
                    confidence=0.9
                )
            ]
        )
        
        # Create context with services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        db_session = AsyncMock()
        
        context = {
            "service_factory": service_factory,
            "shared_db_session": db_session,
            "restaurant_id": "1"
        }
        
        result = await menu_resolution_agent(extraction_response, context)
        
        # Verify response structure
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is True
        assert result.confidence > 0.7
        assert len(result.resolved_items) == 2
        
        # Verify Big Mac resolution
        big_mac = next((item for item in result.resolved_items if "big mac" in item.item_name.lower()), None)
        assert big_mac is not None
        assert big_mac.menu_item_id > 0  # Should be resolved
        assert not big_mac.is_ambiguous
        
        # Verify fries resolution
        fries = next((item for item in result.resolved_items if "fries" in item.item_name.lower()), None)
        assert fries is not None
        assert fries.menu_item_id > 0  # Should be resolved
        assert not fries.is_ambiguous
        assert fries.size == "large"
    
    @pytest.mark.asyncio
    async def test_resolve_ambiguous_items(self):
        """Test resolution of ambiguous items"""
        # Create extraction response with ambiguous items
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.6,
            extracted_items=[
                ExtractedItem(
                    item_name="burger",
                    quantity=1,
                    confidence=0.6
                ),
                ExtractedItem(
                    item_name="special",
                    quantity=1,
                    confidence=0.4
                )
            ]
        )
        
        # Create context with services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        db_session = AsyncMock()
        
        context = {
            "service_factory": service_factory,
            "shared_db_session": db_session,
            "restaurant_id": "1"
        }
        
        result = await menu_resolution_agent(extraction_response, context)
        
        # Verify response structure
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is True
        assert len(result.resolved_items) == 2
        
        # Check for ambiguous items
        ambiguous_items = [item for item in result.resolved_items if item.is_ambiguous]
        assert len(ambiguous_items) > 0  # Should have some ambiguous items
        
        # Verify suggestions are provided
        for item in ambiguous_items:
            assert len(item.suggested_options) > 0
            assert item.clarification_question is not None
    
    @pytest.mark.asyncio
    async def test_resolve_nonexistent_items(self):
        """Test resolution of items that don't exist on menu"""
        # Create extraction response with nonexistent items
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.8,
            extracted_items=[
                ExtractedItem(
                    item_name="pizza",
                    quantity=1,
                    confidence=0.8
                ),
                ExtractedItem(
                    item_name="sushi",
                    quantity=2,
                    confidence=0.8
                )
            ]
        )
        
        # Create context with services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        db_session = AsyncMock()
        
        context = {
            "service_factory": service_factory,
            "shared_db_session": db_session,
            "restaurant_id": "1"
        }
        
        result = await menu_resolution_agent(extraction_response, context)
        
        # Verify response structure
        assert isinstance(result, MenuResolutionResponse)
        assert result.success is True
        assert len(result.resolved_items) == 2
        
        # All items should be ambiguous (not found)
        for item in result.resolved_items:
            assert item.is_ambiguous
            assert item.menu_item_id == 0
            assert len(item.suggested_options) > 0
            assert item.clarification_question is not None


def run_test():
    """Run a single test to verify the agent works"""
    async def test():
        # Create extraction response
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="Big Mac",
                    quantity=1,
                    confidence=0.9
                ),
                ExtractedItem(
                    item_name="fries",
                    quantity=2,
                    size="large",
                    confidence=0.9
                )
            ]
        )
        
        # Create context with services
        container = MockContainer()
        service_factory = ServiceFactory(container)
        db_session = AsyncMock()
        
        context = {
            "service_factory": service_factory,
            "shared_db_session": db_session,
            "restaurant_id": "1"
        }
        
        result = await menu_resolution_agent(extraction_response, context)
        
        print(f"\n🔍 MENU RESOLUTION AGENT TEST:")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Items resolved: {len(result.resolved_items)}")
        
        for i, item in enumerate(result.resolved_items):
            print(f"     Item {i+1}: '{item.item_name}' → ID: {item.menu_item_id} (ambiguous: {item.is_ambiguous})")
            if item.suggested_options:
                print(f"       Suggestions: {', '.join(item.suggested_options)}")
            if item.clarification_question:
                print(f"       Question: {item.clarification_question}")
        
        return result
    
    return asyncio.run(test())


if __name__ == "__main__":
    run_test()
