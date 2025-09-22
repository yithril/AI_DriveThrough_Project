"""
Integration tests for REMOVE_ITEM agent
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.agents.command_agents.remove_item_agent import remove_item_agent_node
from app.agents.state import ConversationWorkflowState
from app.constants.audio_phrases import AudioPhraseType


class TestRemoveItemAgentIntegration:
    """Integration tests for REMOVE_ITEM agent"""
    
    @pytest.mark.asyncio
    async def test_remove_item_agent_simple(self):
        """Test basic REMOVE_ITEM agent functionality"""
        print("\n🧪 TESTING REMOVE_ITEM AGENT - SIMPLE")
        print("=" * 60)
        
        # Create test state with a current order containing a Quantum Burger
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            user_input="Remove the quantum burger",
            normalized_user_input="Remove the quantum burger",
            conversation_history=[],
            order_state=[
                {"name": "Quantum Burger", "quantity": 1, "size": "large", "modifiers": ["extra cheese"]},
                {"name": "Fries", "quantity": 1, "size": "medium", "modifiers": []},
                {"name": "Coke", "quantity": 1, "size": "large", "modifiers": []}
            ],
            current_state="ORDERING"
        )
        
        # Mock container
        mock_container = AsyncMock()
        context = {"container": mock_container}
        
        print(f"📝 User Input: '{state.user_input}'")
        print(f"🏪 Restaurant: Test Restaurant")
        print(f"📋 Current Order: {state.order_state}")
        
        # Call the agent directly
        agent_response = await remove_item_agent_node(
            user_input=state.user_input,
            current_order_items=state.order_state
        )
        
        print(f"\n🎯 REMOVE_ITEM AGENT OUTPUT:")
        print("=" * 60)
        print(f"Confidence: {agent_response.confidence}")
        print(f"Items to remove: {len(agent_response.items_to_remove)}")
        for i, item in enumerate(agent_response.items_to_remove):
            print(f"  Item {i+1}: ID {item.order_item_id or 'None'} - {item.target_ref or 'None'}")
        
        # Assertions
        assert agent_response.confidence > 0.0, "Should have confidence > 0"
        assert len(agent_response.items_to_remove) > 0, "Should have items to remove"
        
        # Check the first item
        first_item = agent_response.items_to_remove[0]
        assert first_item.target_ref is not None, "Should have target_ref"
        assert first_item.target_ref == "quantum burger" or first_item.target_ref == "burger", f"Should identify burger, got: {first_item.target_ref}"
        
        print(f"\n✅ Simple remove item test completed!")
        print(f"🎯 Expected: AI should parse 'Remove the quantum burger' and extract removal request")
        print("PASSED")
    
    @pytest.mark.asyncio
    async def test_remove_item_agent_last_item(self):
        """Test REMOVE_ITEM agent with 'last item' reference"""
        print("\n🧪 TESTING REMOVE_ITEM AGENT - LAST ITEM")
        print("=" * 60)
        
        # Create test state
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            user_input="Remove the last thing I ordered",
            normalized_user_input="Remove the last thing I ordered",
            conversation_history=[],
            order_state=[],
            current_state="ORDERING"
        )
        
        # Mock container
        mock_container = AsyncMock()
        context = {"container": mock_container}
        
        print(f"📝 User Input: '{state.user_input}'")
        
        # Call the agent directly
        agent_response = await remove_item_agent_node(
            user_input=state.user_input,
            current_order_items=state.order_state
        )
        
        print(f"\n🎯 REMOVE_ITEM AGENT OUTPUT:")
        print("=" * 60)
        print(f"Confidence: {agent_response.confidence}")
        print(f"Items to remove: {len(agent_response.items_to_remove)}")
        for i, item in enumerate(agent_response.items_to_remove):
            print(f"  Item {i+1}: ID {item.order_item_id or 'None'} - {item.target_ref or 'None'}")
        
        # Assertions
        assert agent_response.confidence > 0.0, "Should have confidence > 0"
        assert len(agent_response.items_to_remove) > 0, "Should have items to remove"
        
        # Check that it used target_ref for "last item"
        first_item = agent_response.items_to_remove[0]
        assert first_item.target_ref == 'last_item', f"Should use 'last_item' target_ref, got: {first_item.target_ref}"
        
        print(f"\n✅ Last item test completed!")
        print(f"🎯 Expected: AI should parse 'Remove the last thing I ordered' and use 'last_item' target_ref")
        print("PASSED")


if __name__ == "__main__":
    import asyncio
    import sys
    import os
    
    # Add the backend directory to the path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    async def main():
        test_instance = TestRemoveItemAgentIntegration()
        
        print("🧪 RUNNING REMOVE_ITEM AGENT INTEGRATION TESTS")
        print("=" * 60)
        
        try:
            await test_instance.test_remove_item_agent_simple()
            await test_instance.test_remove_item_agent_last_item()
            print("\n🎉 ALL TESTS PASSED!")
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
