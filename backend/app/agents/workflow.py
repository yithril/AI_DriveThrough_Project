"""
LangGraph Workflow Orchestrator

This module contains the main workflow that connects all the nodes together.
Uses LangGraph to orchestrate the conversation flow.
"""

from typing import Dict, Any, TypedDict
from langgraph import StateGraph, END
from app.agents.state import ConversationWorkflowState
from app.agents.nodes import (
    intent_classifier_node,
    should_continue_after_intent_classifier,
    transition_decision_node,
    should_continue_after_transition_decision,
    command_agent_node,
    should_continue_after_command_agent,
    command_executor_node,
    should_continue_after_command_executor,
    follow_up_agent_node,
    should_continue_after_follow_up_agent,
    voice_generator_node,
    should_continue_after_voice_generator
)


class ConversationWorkflow:
    """
    Main workflow class that orchestrates the LangGraph nodes.
    
    Uses LangGraph StateGraph to manage the conversation flow between nodes.
    """
    
    def __init__(self):
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow with all nodes and routing logic."""
        
        # Create the state graph
        workflow = StateGraph(ConversationWorkflowState)
        
        # Add all the nodes
        workflow.add_node("intent_classifier", intent_classifier_node)
        workflow.add_node("transition_decision", transition_decision_node)
        workflow.add_node("command_agent", command_agent_node)
        workflow.add_node("command_executor", command_executor_node)
        workflow.add_node("follow_up_agent", follow_up_agent_node)
        workflow.add_node("voice_generator", voice_generator_node)
        workflow.add_node("canned_response", self._canned_response_node)
        
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
                "command_agent": "command_agent",
                "canned_response": "canned_response"
            }
        )
        
        workflow.add_conditional_edges(
            "command_agent",
            should_continue_after_command_agent,
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
                "voice_generator": "voice_generator"
            }
        )
        
        workflow.add_conditional_edges(
            "follow_up_agent",
            should_continue_after_follow_up_agent,
            {
                "voice_generator": "voice_generator"
            }
        )
        
        workflow.add_conditional_edges(
            "voice_generator",
            should_continue_after_voice_generator,
            {
                "END": END
            }
        )
        
        # Canned response always goes to voice generator
        workflow.add_edge("canned_response", "voice_generator")
        
        return workflow.compile()
    
    async def _canned_response_node(self, state: ConversationWorkflowState) -> ConversationWorkflowState:
        """
        Handle canned responses for invalid intents or low confidence.
        
        Args:
            state: Current conversation workflow state
            
        Returns:
            Updated state with canned response text
        """
        # TODO: Implement canned response logic
        # - Check current state for appropriate canned response
        # - Handle invalid intents with generic responses
        # - Handle low confidence with clarification requests
        
        # Stub implementation
        if state.intent_confidence < 0.5:
            state.response_text = "I'm sorry, I didn't quite catch that. Could you please repeat your order?"
        else:
            state.response_text = "I'm sorry, I can't help with that right now. Please let me know what you'd like to order."
        
        return state
    
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
                "command_agent",
                "command_executor",
                "follow_up_agent",
                "voice_generator",
                "canned_response"
            ],
            "edges": [
                ("intent_classifier", "transition_decision"),
                ("intent_classifier", "canned_response"),
                ("transition_decision", "command_agent"),
                ("transition_decision", "canned_response"),
                ("command_agent", "command_executor"),
                ("command_executor", "follow_up_agent"),
                ("command_executor", "voice_generator"),
                ("follow_up_agent", "voice_generator"),
                ("canned_response", "voice_generator")
            ],
            "entry_point": "intent_classifier",
            "end_point": "voice_generator"
        }


# Convenience function for creating workflow
def create_conversation_workflow() -> ConversationWorkflow:
    """Create a new conversation workflow instance."""
    return ConversationWorkflow()
