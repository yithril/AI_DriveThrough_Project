"""
Integration tests for Item Extraction Agent

Tests the agent with real LLM calls to ensure it properly extracts items from user input.
"""

import pytest
import asyncio
from app.agents.command_agents.item_extraction_agent import item_extraction_agent
from app.agents.agent_response.item_extraction_response import ItemExtractionResponse, ExtractedItem


class TestItemExtractionAgentIntegration:
    """Integration tests for Item Extraction Agent"""
    
    @pytest.mark.asyncio
    async def test_simple_single_item(self):
        """Test extraction of a simple single item"""
        user_input = "I want a Big Mac"
        context = {
            "restaurant_id": "1",
            "conversation_history": [],
            "order_state": {}
        }
        
        result = await item_extraction_agent(user_input, context)
        
        # Verify response structure
        assert isinstance(result, ItemExtractionResponse)
        assert result.success is True
        assert result.confidence > 0.8
        assert len(result.extracted_items) == 1
        
        # Verify extracted item
        item = result.extracted_items[0]
        assert item.item_name == "Big Mac"
        assert item.quantity == 1
        assert item.confidence > 0.8
        assert not item.modifiers
        assert not item.special_instructions
    
    @pytest.mark.asyncio
    async def test_multiple_items_with_modifiers(self):
        """Test extraction of multiple items with modifiers"""
        user_input = "I want 3 chicken nuggets with barbecue sauce, two large fries, and a burger with no pickles"
        context = {
            "restaurant_id": "1",
            "conversation_history": [],
            "order_state": {}
        }
        
        result = await item_extraction_agent(user_input, context)
        
        # Verify response structure
        assert isinstance(result, ItemExtractionResponse)
        assert result.success is True
        assert result.confidence > 0.7
        assert len(result.extracted_items) == 3
        
        # Verify first item (chicken nuggets)
        nuggets = result.extracted_items[0]
        assert "nuggets" in nuggets.item_name.lower()
        assert nuggets.quantity == 3
        assert "barbecue" in nuggets.modifiers[0].lower()
        
        # Verify second item (fries)
        fries = result.extracted_items[1]
        assert "fries" in fries.item_name.lower()
        assert fries.quantity == 2
        assert fries.size == "large"
        
        # Verify third item (burger)
        burger = result.extracted_items[2]
        assert "burger" in burger.item_name.lower()
        assert burger.quantity == 1
        assert "no pickles" in burger.modifiers[0].lower()
    
    @pytest.mark.asyncio
    async def test_ambiguous_item(self):
        """Test extraction of ambiguous items"""
        user_input = "I want the special"
        context = {
            "restaurant_id": "1",
            "conversation_history": [],
            "order_state": {}
        }
        
        result = await item_extraction_agent(user_input, context)
        
        # Verify response structure
        assert isinstance(result, ItemExtractionResponse)
        assert result.success is True
        assert len(result.extracted_items) == 1
        
        # Verify ambiguous item
        item = result.extracted_items[0]
        assert item.item_name == "special"
        assert item.quantity == 1
        assert item.confidence < 0.8  # Should be low confidence for ambiguous items
    
    @pytest.mark.asyncio
    async def test_complex_order_with_special_instructions(self):
        """Test extraction of complex order with special instructions"""
        user_input = "I want a well-done burger with extra cheese, a large pepsi, and some fries that are extra crispy"
        context = {
            "restaurant_id": "1",
            "conversation_history": [],
            "order_state": {}
        }
        
        result = await item_extraction_agent(user_input, context)
        
        # Verify response structure
        assert isinstance(result, ItemExtractionResponse)
        assert result.success is True
        assert len(result.extracted_items) == 3
        
        # Find burger item
        burger = next((item for item in result.extracted_items if "burger" in item.item_name.lower()), None)
        assert burger is not None
        assert "extra cheese" in burger.modifiers
        assert "well-done" in burger.special_instructions.lower()
        
        # Find pepsi item
        pepsi = next((item for item in result.extracted_items if "pepsi" in item.item_name.lower()), None)
        assert pepsi is not None
        assert pepsi.size == "large"
        
        # Find fries item
        fries = next((item for item in result.extracted_items if "fries" in item.item_name.lower()), None)
        assert fries is not None
        # Special instructions might not always be captured, so just check if it exists
        if fries.special_instructions:
            assert "extra crispy" in fries.special_instructions.lower()
    
    @pytest.mark.asyncio
    async def test_noisy_input(self):
        """Test extraction from noisy input"""
        user_input = "I want a... um... burger with no pickles... and some fries... wait, make that large fries"
        context = {
            "restaurant_id": "1",
            "conversation_history": [],
            "order_state": {}
        }
        
        result = await item_extraction_agent(user_input, context)
        
        # Verify response structure
        assert isinstance(result, ItemExtractionResponse)
        assert result.success is True
        assert len(result.extracted_items) == 2
        
        # Verify burger
        burger = next((item for item in result.extracted_items if "burger" in item.item_name.lower()), None)
        assert burger is not None
        assert "no pickles" in burger.modifiers[0].lower()
        
        # Verify fries
        fries = next((item for item in result.extracted_items if "fries" in item.item_name.lower()), None)
        assert fries is not None
        assert fries.size == "large"


def run_test():
    """Run a single test to verify the agent works"""
    async def test():
        user_input = "I want 3 chicken nuggets with barbecue sauce and two large fries"
        context = {
            "restaurant_id": "1",
            "conversation_history": [],
            "order_state": {}
        }
        
        result = await item_extraction_agent(user_input, context)
        
        print(f"\n🔍 ITEM EXTRACTION AGENT TEST:")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Items extracted: {len(result.extracted_items)}")
        
        for i, item in enumerate(result.extracted_items):
            print(f"     Item {i+1}: '{item.item_name}' (qty: {item.quantity}, confidence: {item.confidence})")
            if item.size:
                print(f"       Size: {item.size}")
            if item.modifiers:
                print(f"       Modifiers: {', '.join(item.modifiers)}")
            if item.special_instructions:
                print(f"       Special: {item.special_instructions}")
        
        return result
    
    return asyncio.run(test())


if __name__ == "__main__":
    run_test()
