"""
LangGraph Workflow Orchestrator

This module contains the main workflow that connects all the nodes together.
Uses LangGraph to orchestrate the conversation flow.
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from app.agents.state import ConversationWorkflowState
from app.core.database import get_db
from app.core.unit_of_work import UnitOfWork
from app.core.service_factory import create_service_factory
from app.agents.nodes import (
    intent_classifier_node,
    should_continue_after_intent_classifier,
    state_transition_node,
    should_continue_after_state_transition,
    command_executor_node,
    should_continue_after_command_executor,
    final_response_aggregator_node,
    should_continue_after_final_response_aggregator,
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
        
        # Build node-specific service bundles
        # Note: These will be built at runtime when container is available
        # For now, we'll pass None and build bundles in process_conversation_turn
        
        # Add all the nodes
        workflow.add_node("intent_classifier", intent_classifier_node)
        workflow.add_node("state_transition", state_transition_node)
        workflow.add_node("intent_parser_router", intent_parser_router_node)
        workflow.add_node("command_executor", command_executor_node)
        workflow.add_node("final_response_aggregator", final_response_aggregator_node)
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
                "command_executor": "command_executor",
                "voice_generation": "voice_generation"
            }
        )
        
        workflow.add_conditional_edges(
            "command_executor",
            should_continue_after_command_executor,
            {
                "final_response_aggregator": "final_response_aggregator",
                "voice_generation": "voice_generation"
            }
        )
        
        workflow.add_conditional_edges(
            "final_response_aggregator",
            should_continue_after_final_response_aggregator,
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
    
    async def process_conversation_turn(self, state: ConversationWorkflowState, context: Dict[str, Any] = None) -> ConversationWorkflowState:
        """
        Process a single conversation turn through the workflow.
        
        Args:
            state: Initial conversation state
            context: LangGraph context containing services
            
        Returns:
            Updated state with final response and audio URL
        """
        # Create service factory and shared database session for nodes
        if context and "container" in context:
            print(f"\n🔧 WORKFLOW - Setting up context:")
            print(f"   Container: {context['container']}")
            
            container = context["container"]
            service_factory = create_service_factory(container)
            print(f"   Service factory created: {service_factory}")
            
            # Create a shared database session for this workflow execution
            async def get_shared_db_session():
                async for session in get_db():
                    return session
            
            shared_db_session = await get_shared_db_session()
            print(f"   Shared DB session: {shared_db_session}")
            
            context["service_factory"] = service_factory
            context["shared_db_session"] = shared_db_session
            print(f"   Context updated with service factory and shared DB session")
        
        # Run the workflow with context
        if context:
            result = await self.graph.ainvoke(state, config={"configurable": context})
        else:
            result = await self.graph.ainvoke(state)
        
        # LangGraph returns the final state directly
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
                "final_response_aggregator",
                "voice_generation",
            ],
            "edges": [
                ("intent_classifier", "state_transition"),
                ("state_transition", "intent_parser_router"),
                ("intent_parser_router", "command_executor"),
                ("command_executor", "final_response_aggregator"),
                ("final_response_aggregator", "voice_generation"),
                ("voice_generation", "END"),
            ],
            "entry_point": "intent_classifier",
            "end_points": ["voice_generation", "END"]
        }


# Convenience function for creating workflow
def create_conversation_workflow() -> ConversationWorkflow:
    """Create a new conversation workflow instance."""
    return ConversationWorkflow()
