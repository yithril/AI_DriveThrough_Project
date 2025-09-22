"""
Unit tests for workflow orchestration

Tests the LangGraph workflow structure, node routing, and state transitions.
Focuses on orchestration logic for the current workflow structure.
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
from app.commands.intent_classification_schema import IntentType
from app.constants.audio_phrases import AudioPhraseType


class TestWorkflowOrchestration:
    """Test the workflow orchestration and routing logic"""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing"""
        return ConversationWorkflow()

    @pytest.mark.asyncio
    async def test_workflow_graph_structure(self, workflow):
        """Test that the workflow graph has the correct structure"""
        graph_info = workflow.get_workflow_graph()
        
        # Check nodes
        expected_nodes = [
            "intent_classifier",
            "state_transition", 
            "intent_parser_router",
            "command_executor",
            "response_router",
            "clarification_agent",
            "voice_generation"
        ]
        
        for node in expected_nodes:
            assert node in graph_info["nodes"]
        
        # Check entry point
        assert graph_info["entry_point"] == "intent_classifier"
        
        # Check end points
        assert "voice_generation" in graph_info["end_points"]
        assert "END" in graph_info["end_points"]

    @pytest.mark.asyncio
    async def test_intent_classifier_to_state_transition_routing(self, workflow):
        """Test routing from intent_classifier to state_transition"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # State that should route to state_transition
        state = (ConversationWorkflowStateBuilder()
                .with_intent_classification(IntentType.ADD_ITEM, 0.9)
                .build())
        
        next_node = should_continue_after_intent_classifier(state)
        assert next_node == "state_transition"

    @pytest.mark.asyncio
    async def test_state_transition_to_intent_parser_router_routing(self, workflow):
        """Test routing from state_transition to intent_parser_router"""
        from app.agents.nodes import should_continue_after_state_transition
        
        # State that should route to intent_parser_router
        state = (ConversationWorkflowStateBuilder()
                .with_intent_classification(IntentType.ADD_ITEM, 0.9)
                .with_transition_result(requires_command=True)
                .build())
        
        next_node = should_continue_after_state_transition(state)
        assert next_node == "intent_parser_router"

    @pytest.mark.asyncio
    async def test_intent_parser_router_to_command_executor_routing(self, workflow):
        """Test routing from intent_parser_router to command_executor"""
        from app.agents.nodes import should_continue_after_intent_parser_router
        
        # State that should route to command_executor
        state = (ConversationWorkflowStateBuilder()
                .with_intent_classification(IntentType.ADD_ITEM, 0.9)
                .with_commands(["add_item"])
                .build())
        
        next_node = should_continue_after_intent_parser_router(state)
        assert next_node == "command_executor"

    @pytest.mark.asyncio
    async def test_command_executor_to_response_router_routing(self, workflow):
        """Test routing from command_executor to response_router on success"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with successful command execution
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(create_successful_command_batch_result())
                .build())
        
        next_node = should_continue_after_command_executor(state)
        assert next_node == "response_router"

    @pytest.mark.asyncio
    async def test_command_executor_to_clarification_agent_routing(self, workflow):
        """Test routing from command_executor to clarification_agent on failure"""
        from app.agents.nodes import should_continue_after_command_executor
        
        # State with failed command execution
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(create_failed_command_batch_result())
                .build())
        
        next_node = should_continue_after_command_executor(state)
        assert next_node == "clarification_agent"

    @pytest.mark.asyncio
    async def test_response_router_to_voice_generation_routing(self, workflow):
        """Test routing from response_router to voice_generation on success"""
        from app.agents.nodes import should_continue_after_response_router
        
        # State with successful batch result
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(create_successful_command_batch_result())
                .build())
        
        next_node = should_continue_after_response_router(state)
        assert next_node == "voice_generation"

    @pytest.mark.asyncio
    async def test_response_router_to_clarification_agent_routing(self, workflow):
        """Test routing from response_router to clarification_agent on failure"""
        from app.agents.nodes import response_router_node, should_continue_after_response_router
        
        # State with failed batch result
        state = (ConversationWorkflowStateBuilder()
                .with_command_batch_result(create_failed_command_batch_result())
                .build())
        
        # First call the response router node to set next_node
        state = await response_router_node(state)
        
        # Then check the routing
        next_node = should_continue_after_response_router(state)
        assert next_node == "clarification_agent"

    @pytest.mark.asyncio
    async def test_clarification_agent_to_voice_generation_routing(self, workflow):
        """Test routing from clarification_agent to voice_generation"""
        from app.agents.nodes import should_continue_after_clarification_agent
        
        # Any state should route to voice_generation
        state = (ConversationWorkflowStateBuilder()
                .with_response("Clarification response")
                .build())
        
        next_node = should_continue_after_clarification_agent(state)
        assert next_node == "voice_generation"

    @pytest.mark.asyncio
    async def test_voice_generation_to_end_routing(self, workflow):
        """Test routing from voice_generation to END"""
        from app.agents.nodes import should_continue_after_voice_generation
        
        # Any state should route to END
        state = (ConversationWorkflowStateBuilder()
                .with_response("Final response")
                .with_audio_url("http://example.com/audio.mp3")
                .build())
        
        next_node = should_continue_after_voice_generation(state)
        assert next_node == "END"

    def test_workflow_entry_point(self, workflow):
        """Test that workflow starts at the correct entry point"""
        # The workflow should start at intent_classifier
        graph = workflow.graph
        assert graph is not None
        
        # Test that the workflow has the correct structure
        graph_info = workflow.get_workflow_graph()
        assert graph_info["entry_point"] == "intent_classifier"
        assert "intent_classifier" in graph_info["nodes"]
        assert "state_transition" in graph_info["nodes"]
        assert "intent_parser_router" in graph_info["nodes"]
        assert "command_executor" in graph_info["nodes"]
        assert "response_router" in graph_info["nodes"]
        assert "clarification_agent" in graph_info["nodes"]
        assert "voice_generation" in graph_info["nodes"]


class TestWorkflowStateTransitions:
    """Test state transitions through the workflow"""

    def test_state_preservation_through_routing(self):
        """Test that state is preserved through routing decisions"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # Create a state with specific data
        state = (ConversationWorkflowStateBuilder()
                .with_user_input("I want a burger")
                .with_intent_classification(IntentType.ADD_ITEM, 0.9)
                .with_restaurant_id(1)
                .build())
        
        # Test routing doesn't modify the state
        next_node = should_continue_after_intent_classifier(state)
        
        # Verify state is preserved
        assert state.user_input == "I want a burger"
        assert state.intent_type == IntentType.ADD_ITEM
        assert state.restaurant_id == "1"

    def test_routing_consistency(self):
        """Test that routing decisions are consistent for the same state"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # Create identical states
        state1 = (ConversationWorkflowStateBuilder()
                 .with_intent_classification(IntentType.ADD_ITEM, 0.9)
                 .build())
        
        state2 = (ConversationWorkflowStateBuilder()
                 .with_intent_classification(IntentType.ADD_ITEM, 0.9)
                 .build())
        
        # Test multiple calls with same state
        result1 = should_continue_after_intent_classifier(state1)
        result2 = should_continue_after_intent_classifier(state2)
        
        assert result1 == result2


class TestWorkflowErrorHandling:
    """Test error handling in the workflow"""

    def test_routing_with_none_values(self):
        """Test routing with None values in state"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # State with None values
        state = (ConversationWorkflowStateBuilder()
                .with_intent_classification(None, 0.0)
                .build())
        
        # Should handle gracefully
        next_node = should_continue_after_intent_classifier(state)
        assert next_node is not None

    def test_routing_with_empty_lists(self):
        """Test routing with empty command lists"""
        from app.agents.nodes import should_continue_after_intent_parser_router
        
        # State with empty commands
        state = (ConversationWorkflowStateBuilder()
                .with_commands([])
                .build())
        
        # Should route appropriately
        next_node = should_continue_after_intent_parser_router(state)
        assert next_node is not None

    def test_routing_with_invalid_confidence(self):
        """Test routing with invalid confidence values"""
        from app.agents.nodes import should_continue_after_intent_classifier
        
        # State with invalid confidence
        state = (ConversationWorkflowStateBuilder()
                .with_intent_classification(IntentType.ADD_ITEM, -0.5)
                .build())
        
        # Should handle gracefully
        next_node = should_continue_after_intent_classifier(state)
        assert next_node is not None
