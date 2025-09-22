"""
LangGraph Workflow Orchestrator

This module contains the main workflow that connects all the nodes together.
Uses LangGraph to orchestrate the conversation flow.
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from app.agents.state import ConversationWorkflowState
from app.agents.nodes import (
    intent_classifier_node,
    should_continue_after_intent_classifier,
    state_transition_node,
    should_continue_after_state_transition,
    command_executor_node,
    should_continue_after_command_executor,
    response_router_node,
    should_continue_after_response_router,
    clarification_agent_node,
    should_continue_after_clarification_agent,
    voice_generation_node,
    should_continue_after_voice_generation,
)
from app.agents.nodes.intent_parser_router_node import (
    intent_parser_router_node,
    should_continue_after_intent_parser_router
)


class ConversationWorkflow:
    """
    Main workflow class that orchestrates the LangGraph nodes.
    
    Uses LangGraph StateGraph to manage the conversation flow between nodes.
    """
    
    def __init__(self, voice_service=None):
        self.voice_service = voice_service
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow with all nodes and routing logic."""
        
        # Create the state graph
        workflow = StateGraph(ConversationWorkflowState)
        
        # Add all the nodes
        workflow.add_node("intent_classifier", intent_classifier_node)
        workflow.add_node("state_transition", state_transition_node)
        workflow.add_node("intent_parser_router", intent_parser_router_node)
        workflow.add_node("command_executor", command_executor_node)
        workflow.add_node("response_router", response_router_node)
        workflow.add_node("clarification_agent", clarification_agent_node)
        workflow.add_node("voice_generation", voice_generation_node)
        
        # Set the entry point
        workflow.set_entry_point("intent_classifier")
        
        # Add conditional routing after each node
        workflow.add_conditional_edges(
            "intent_classifier",
            should_continue_after_intent_classifier,
            {
                "state_transition": "state_transition"
            }
        )
        
        workflow.add_conditional_edges(
            "state_transition",
            should_continue_after_state_transition,
            {
                "intent_parser_router": "intent_parser_router"
            }
        )
        
        workflow.add_conditional_edges(
            "intent_parser_router",
            should_continue_after_intent_parser_router,
            {
                "command_executor": "command_executor"
            }
        )
        
        workflow.add_conditional_edges(
            "command_executor",
            should_continue_after_command_executor,
            {
                "clarification_agent": "clarification_agent",
                "response_router": "response_router"
            }
        )
        
        
        workflow.add_conditional_edges(
            "response_router",
            should_continue_after_response_router,
            {
                "clarification_agent": "clarification_agent",
                "voice_generation": "voice_generation"
            }
        )
        
        workflow.add_conditional_edges(
            "clarification_agent",
            should_continue_after_clarification_agent,
            {
                "voice_generation": "voice_generation"
            }
        )
        
        workflow.add_conditional_edges(
            "voice_generation",
            should_continue_after_voice_generation,
            {
                "END": END
            }
        )
        
        
        return workflow.compile()
    
    async def process_conversation_turn(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """
        Process a single conversation turn through the workflow.
        
        Args:
            state: Initial conversation state
            
        Returns:
            Updated state with final response and audio URL
        """
        # Run the workflow
        result = await self.graph.ainvoke(state)
        return result
    
    def get_workflow_graph(self) -> Dict[str, Any]:
        """
        Get the workflow graph structure for visualization/debugging.
        
        Returns:
            Graph structure showing nodes and edges
        """
        return {
            "nodes": [
                "intent_classifier",
                "state_transition", 
                "intent_parser_router",
                "command_executor",
                "response_router",
                "clarification_agent",
                "voice_generation",
            ],
            "edges": [
                ("intent_classifier", "state_transition"),
                ("state_transition", "intent_parser_router"),
                ("intent_parser_router", "command_executor"),
                ("command_executor", "clarification_agent"),
                ("command_executor", "response_router"),
                ("response_router", "clarification_agent"),
                ("response_router", "voice_generation"),
                ("clarification_agent", "voice_generation"),
                ("voice_generation", "END"),
            ],
            "entry_point": "intent_classifier",
            "end_points": ["voice_generation", "END"]
        }


# Convenience function for creating workflow
def create_conversation_workflow() -> ConversationWorkflow:
    """Create a new conversation workflow instance."""
    return ConversationWorkflow()
