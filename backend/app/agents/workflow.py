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
    transition_decision_node,
    should_continue_after_transition_decision,
    command_executor_node,
    should_continue_after_command_executor,
    follow_up_agent_node,
    should_continue_after_follow_up_agent,
    dynamic_voice_response_node,
    should_continue_after_dynamic_voice_response,
    canned_response_node,
    should_continue_after_canned_response
)
from app.agents.parser.intent_parser_router import (
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
        workflow.add_node("transition_decision", transition_decision_node)
        workflow.add_node("intent_parser_router", intent_parser_router_node)
        workflow.add_node("command_executor", command_executor_node)
        workflow.add_node("follow_up_agent", follow_up_agent_node)
        workflow.add_node("dynamic_voice_response", dynamic_voice_response_node)
        workflow.add_node("canned_response", canned_response_node)
        
        # Set the entry point
        workflow.set_entry_point("intent_classifier")
        
        # Add conditional routing after each node
        workflow.add_conditional_edges(
            "intent_classifier",
            should_continue_after_intent_classifier,
            {
                "transition_decision": "transition_decision",
                "canned_response": "canned_response"
            }
        )
        
        workflow.add_conditional_edges(
            "transition_decision",
            should_continue_after_transition_decision,
            {
                "intent_parser_router": "intent_parser_router",
                "canned_response": "canned_response"
            }
        )
        
        workflow.add_conditional_edges(
            "intent_parser_router",
            should_continue_after_intent_parser_router,
            {
                "command_executor": "command_executor",
                "canned_response": "canned_response"
            }
        )
        
        workflow.add_conditional_edges(
            "command_executor",
            should_continue_after_command_executor,
            {
                "follow_up_agent": "follow_up_agent",
                "dynamic_voice_response": "dynamic_voice_response"
            }
        )
        
        workflow.add_conditional_edges(
            "follow_up_agent",
            should_continue_after_follow_up_agent,
            {
                "dynamic_voice_response": "dynamic_voice_response"
            }
        )
        
        workflow.add_conditional_edges(
            "dynamic_voice_response",
            should_continue_after_dynamic_voice_response,
            {
                "END": END
            }
        )
        
        # Canned response goes directly to END (it already has audio)
        workflow.add_conditional_edges(
            "canned_response",
            should_continue_after_canned_response,
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
                "transition_decision", 
                "intent_parser_router",
                "command_executor",
                "follow_up_agent",
                "dynamic_voice_response",
                "canned_response"
            ],
            "edges": [
                ("intent_classifier", "transition_decision"),
                ("intent_classifier", "canned_response"),
                ("transition_decision", "intent_parser_router"),
                ("transition_decision", "canned_response"),
                ("intent_parser_router", "command_executor"),
                ("intent_parser_router", "canned_response"),
                ("command_executor", "follow_up_agent"),
                ("command_executor", "dynamic_voice_response"),
                ("follow_up_agent", "dynamic_voice_response"),
                ("canned_response", "END")
            ],
            "entry_point": "intent_classifier",
            "end_points": ["dynamic_voice_response", "END"]
        }


# Convenience function for creating workflow
def create_conversation_workflow() -> ConversationWorkflow:
    """Create a new conversation workflow instance."""
    return ConversationWorkflow()
