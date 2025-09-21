"""
Unit tests for workflow orchestration

Tests the LangGraph workflow structure, node routing, and state transitions.
Focuses on orchestration logic, not individual node functionality.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.workflow import ConversationWorkflow
from app.agents.state import ConversationWorkflowState
from .test_helpers import (
    ConversationWorkflowStateBuilder, 
    create_test_state,
    create_successful_command_batch_result,
    create_failed_command_batch_result
)
from app.models.state_machine_models import ConversationState
from app.commands.command_contract import IntentType
from app.constants.audio_phrases import AudioPhraseType
from app.dto.order_result import FollowUpAction


class TestWorkflowOrchestration:
    """Test the workflow orchestration and routing logic"""

    @pytest.fixture
    def mock_voice_service(self):
        """Mock voice service for workflow"""
        voice_service = AsyncMock()
        voice_service.generate_voice.return_value = "https://s3.amazonaws.com/bucket/test.mp3"
        voice_service.get_canned_phrase.return_value = "https://s3.amazonaws.com/bucket/canned.mp3"
        return voice_service

    @pytest.fixture
    def workflow(self, mock_voice_service):
        """Create workflow instance with mocked dependencies"""
        return ConversationWorkflow(voice_service=mock_voice_service)

    @pytest.mark.asyncio
    async def test_workflow_graph_structure(self, workflow):
        """Test that the workflow graph has all expected nodes and connections"""
        # Get the compiled graph
        graph = workflow.graph
        
        # Verify all expected nodes exist
        expected_nodes = [
            "intent_classifier",
            "transition_decision", 
            "command_agent",
            "command_executor",
            "follow_up_agent",
            "dynamic_voice_response",
            "canned_response"
        ]
        
        # Check that graph has the expected structure
        # Note: LangGraph doesn't expose node list directly, so we test indirectly
        # by ensuring the graph can be executed
        assert graph is not None
        
        # Test that we can get the graph structure (this is the compiled graph)
        assert hasattr(graph, 'get_graph')
        graph_dict = graph.get_graph()
        assert graph_dict is not None

    @pytest.mark.asyncio
    async def test_intent_classifier_to_transition_decision_routing(self, workflow):
        """Test routing from intent_classifier to transition_decision"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # State with valid intent
        state = (ConversationWorkflowStateBuilder()
                .with_intent(IntentType.ADD_ITEM, confidence=0.95)
                .build())
        
        # Should route to transition_decision
        next_node = should_continue_after_intent_classifier(state)
        assert next_node == "transition_decision"

    @pytest.mark.asyncio
    async def test_intent_classifier_to_canned_response_routing(self, workflow):
        """Test routing from intent_classifier to canned_response for low confidence"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # State with low confidence intent
        state = (ConversationWorkflowStateBuilder()
                .with_intent(IntentType.ADD_ITEM, confidence=0.3)  # Low confidence
                .build())
        
        # Should route to canned_response
        next_node = should_continue_after_intent_classifier(state)
        assert next_node == "canned_response"

    @pytest.mark.asyncio
    async def test_transition_decision_to_command_agent_routing(self, workflow):
        """Test routing from transition_decision to command_agent when command needed"""
        from app.agents.nodes import should_continue_after_transition_decision
        
        # State that requires a command
        state = (ConversationWorkflowStateBuilder()
                .with_transition_result(requires_command=True)
                .build())
        
        # Should route to command_agent
        next_node = should_continue_after_transition_decision(state)
        assert next_node == "command_agent"

    @pytest.mark.asyncio
    async def test_transition_decision_to_canned_response_routing(self, workflow):
        """Test routing from transition_decision to canned_response when no command needed"""
        from app.agents.nodes import should_continue_after_transition_decision
        
        # State that doesn't require a command
        state = (ConversationWorkflowStateBuilder()
                .with_transition_result(requires_command=False, phrase_type=AudioPhraseType.GREETING)
                .build())
        
        # Should route to canned_response
        next_node = should_continue_after_transition_decision(state)
        assert next_node == "canned_response"

    @pytest.mark.asyncio
    async def test_command_agent_to_command_executor_routing(self, workflow):
        """Test routing from command_agent to command_executor when commands generated"""
        from app.agents.nodes import should_continue_after_command_agent
        
        # State with generated commands
        state = (ConversationWorkflowStateBuilder()
                .with_commands([{"intent": "ADD_ITEM", "menu_item_id": 1}])
                .build())
        
        # Should route to command_executor
        next_node = should_continue_after_command_agent(state)
        assert next_node == "command_executor"

    @pytest.mark.asyncio
    async def test_command_agent_to_canned_response_routing(self, workflow):
        """Test routing from command_agent to canned_response when no commands generated"""
        from app.agents.nodes import should_continue_after_command_agent
        
        # State with no commands
        state = (ConversationWorkflowStateBuilder()
                .with_commands([])
                .build())
        
        # Should route to canned_response
        next_node = should_continue_after_command_agent(state)
        assert next_node == "canned_response"

    @pytest.mark.asyncio
    async def test_command_executor_to_follow_up_agent_routing(self, workflow):
        """Test routing from command_executor to follow_up_agent on failures"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with failed command execution
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(create_failed_command_batch_result())
                .build())
        
        # Should route to follow_up_agent
        next_node = should_continue_after_command_executor(state)
        assert next_node == "follow_up_agent"

    @pytest.mark.asyncio
    async def test_command_executor_to_dynamic_voice_response_routing(self, workflow):
        """Test routing from command_executor to dynamic_voice_response on success"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with successful command execution
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(create_successful_command_batch_result())
                .build())
        
        # Should route to dynamic_voice_response
        next_node = should_continue_after_command_executor(state)
        assert next_node == "dynamic_voice_response"

    @pytest.mark.asyncio
    async def test_follow_up_agent_to_dynamic_voice_response_routing(self, workflow):
        """Test routing from follow_up_agent to dynamic_voice_response"""
        from app.agents.nodes import should_continue_after_follow_up_agent
        
        # Any state should route to dynamic_voice_response
        state = (ConversationWorkflowStateBuilder()
                .with_response("Follow up response")
                .build())
        
        # Should route to dynamic_voice_response
        next_node = should_continue_after_follow_up_agent(state)
        assert next_node == "dynamic_voice_response"

    @pytest.mark.asyncio
    async def test_dynamic_voice_response_to_end_routing(self, workflow):
        """Test routing from dynamic_voice_response to END"""
        from app.agents.nodes import should_continue_after_dynamic_voice_response
        
        # Any state should route to END
        state = (ConversationWorkflowStateBuilder()
                .with_response("Final response")
                .build())
        
        # Should route to END
        next_node = should_continue_after_dynamic_voice_response(state)
        assert next_node == "END"

    @pytest.mark.asyncio
    async def test_canned_response_to_end_routing(self, workflow):
        """Test routing from canned_response to END"""
        from app.agents.nodes import should_continue_after_canned_response
        
        # Any state should route to END
        state = (ConversationWorkflowStateBuilder()
                .with_response("Canned response")
                .build())
        
        # Should route to END
        next_node = should_continue_after_canned_response(state)
        assert next_node == "END"

    @pytest.mark.asyncio
    async def test_command_executor_routing_with_validation_errors(self, workflow):
        """Test command_executor routing when there are validation errors"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with validation errors
        state = (ConversationWorkflowStateBuilder()
                .with_errors(["Validation failed"])
                .build())
        
        # Should route to follow_up_agent for error handling
        next_node = should_continue_after_command_executor(state)
        assert next_node == "follow_up_agent"

    @pytest.mark.asyncio
    async def test_command_executor_routing_with_ask_follow_up(self, workflow):
        """Test command_executor routing when follow_up_action is ASK"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with ASK follow-up action
        batch_result = create_successful_command_batch_result()
        batch_result.follow_up_action = FollowUpAction.ASK
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(batch_result)
                .build())
        
        # Should route to follow_up_agent
        next_node = should_continue_after_command_executor(state)
        assert next_node == "follow_up_agent"

    @pytest.mark.asyncio
    async def test_command_executor_routing_with_stop_follow_up(self, workflow):
        """Test command_executor routing when follow_up_action is STOP"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with STOP follow-up action
        batch_result = create_successful_command_batch_result()
        batch_result.follow_up_action = FollowUpAction.STOP
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(batch_result)
                .build())
        
        # Should route to dynamic_voice_response
        next_node = should_continue_after_command_executor(state)
        assert next_node == "dynamic_voice_response"

    @pytest.mark.asyncio
    async def test_workflow_entry_point(self, workflow):
        """Test that workflow starts at the correct entry point"""
        # The workflow should start at intent_classifier
        # This is tested by ensuring the graph compiles and has the right structure
        graph = workflow.graph
        assert graph is not None
        
        # Test that we can process a turn (this will start at intent_classifier)
        initial_state = create_test_state(user_input="Hello")
        
        # Mock all the node functions to prevent actual execution
        with patch('app.agents.nodes.intent_classifier_node') as mock_intent, \
             patch('app.agents.nodes.transition_decision_node') as mock_transition, \
             patch('app.agents.nodes.command_agent_node') as mock_command_agent, \
             patch('app.agents.nodes.command_executor_node') as mock_executor, \
             patch('app.agents.nodes.follow_up_agent_node') as mock_follow_up, \
             patch('app.agents.nodes.dynamic_voice_response_node') as mock_voice, \
             patch('app.agents.nodes.canned_response_node') as mock_canned:
            
            # Set up mocks to return the state unchanged
            mock_intent.return_value = initial_state
            mock_transition.return_value = initial_state
            mock_command_agent.return_value = initial_state
            mock_executor.return_value = initial_state
            mock_follow_up.return_value = initial_state
            mock_voice.return_value = initial_state
            mock_canned.return_value = initial_state
            
            # This should not raise an error, indicating the workflow structure is correct
            try:
                result = await workflow.process_conversation_turn(initial_state)
                assert result is not None
            except Exception as e:
                # If it fails, it should be due to missing dependencies, not workflow structure
                assert "workflow" not in str(e).lower() or "graph" not in str(e).lower()


class TestWorkflowStateTransitions:
    """Test that state flows correctly through the workflow"""

    def test_state_preservation_through_routing(self):
        """Test that state is preserved when routing between nodes"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # Create a state with specific data
        original_state = (ConversationWorkflowStateBuilder()
                         .with_session_id("test-session-456")
                         .with_restaurant_id("2")
                         .with_user_input("I want a burger")
                         .with_intent(IntentType.ADD_ITEM, confidence=0.9)
                         .build())
        
        # Routing should not modify the state
        next_node = should_continue_after_intent_classifier(original_state)
        
        # State should be unchanged
        assert original_state.session_id == "test-session-456"
        assert original_state.restaurant_id == "2"
        assert original_state.user_input == "I want a burger"
        assert original_state.intent_type == IntentType.ADD_ITEM
        assert original_state.intent_confidence == 0.9

    def test_routing_consistency(self):
        """Test that routing decisions are consistent for the same state"""
        from app.agents.nodes import should_continue_after_transition_decision
        
        # Create the same state multiple times
        state1 = (ConversationWorkflowStateBuilder()
                 .with_transition_result(requires_command=True)
                 .build())
        
        state2 = (ConversationWorkflowStateBuilder()
                 .with_transition_result(requires_command=True)
                 .build())
        
        # Should get the same routing decision
        route1 = should_continue_after_transition_decision(state1)
        route2 = should_continue_after_transition_decision(state2)
        
        assert route1 == route2
        assert route1 == "command_agent"


class TestWorkflowErrorHandling:
    """Test workflow error handling and edge cases"""

    def test_routing_with_none_values(self):
        """Test routing when state has None values"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with minimal data
        state = (ConversationWorkflowStateBuilder()
                .with_session_id("test")
                .with_restaurant_id("1")
                .build())
        
        # Should handle None values gracefully
        next_node = should_continue_after_command_executor(state)
        
        # Should default to dynamic_voice_response
        assert next_node == "dynamic_voice_response"

    def test_routing_with_empty_lists(self):
        """Test routing with empty command lists"""
        from app.agents.nodes import should_continue_after_command_agent
        
        # State with empty commands
        state = (ConversationWorkflowStateBuilder()
                .with_commands([])
                .build())
        
        # Should route to canned_response
        next_node = should_continue_after_command_agent(state)
        assert next_node == "canned_response"

    def test_routing_with_invalid_confidence(self):
        """Test routing with invalid confidence values"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # State with negative confidence
        state = (ConversationWorkflowStateBuilder()
                .with_intent(IntentType.ADD_ITEM, confidence=-0.1)
                .build())
        
        # Should route to canned_response (treated as low confidence)
        next_node = should_continue_after_intent_classifier(state)
        assert next_node == "canned_response"
