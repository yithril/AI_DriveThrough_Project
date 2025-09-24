"""
Unit tests for Response Router Node

Tests the simplified 2-category response routing logic:
- canned_response: Simple, predictable responses (pre-recorded audio)
- clarification_agent: Dynamic content or clarification (LLM + TTS)
"""

import pytest
from app.agents.nodes.response_router_node import response_router_node, should_continue_after_response_router, _get_success_phrase_type
from app.agents.state.conversation_state import ConversationWorkflowState
from app.models.state_machine_models import OrderState, ConversationContext
from app.dto.order_result import CommandBatchResult, OrderResult, ResponsePayload
from app.constants.audio_phrases import AudioPhraseType


class TestResponseRouterNode:
    """Test the response router node"""
    
    @pytest.mark.asyncio
    async def test_route_add_item_success(self):
        """Test routing ADD_ITEM + ALL_SUCCESS to canned response"""
        # Create state with successful ADD_ITEM batch result
        batch_result = CommandBatchResult(
            results=[OrderResult.success("Item added successfully")],
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Item added successfully",
            command_family="ADD_ITEM",
            batch_outcome="ALL_SUCCESS",
            first_error_code=None,
            response_payload=ResponsePayload(
                enum_key="ADDITEM_ALL_SUCCESS",
                args={},
                telemetry={}
            )
        )
        
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            command_batch_result=batch_result
        )
        
        # Execute response router
        result_state = await response_router_node(state)
        
        # Verify routing decision
        assert result_state.next_node == "voice_generation"
        assert result_state.response_phrase_type == AudioPhraseType.ITEM_ADDED_SUCCESS
    
    @pytest.mark.asyncio
    async def test_route_question_success(self):
        """Test routing QUESTION + ALL_SUCCESS to canned response"""
        # Create state with successful QUESTION batch result
        batch_result = CommandBatchResult(
            results=[OrderResult.success("The burger contains beef, lettuce, tomato")],
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Question answered",
            command_family="QUESTION",
            batch_outcome="ALL_SUCCESS",
            first_error_code=None,
            response_payload=ResponsePayload(
                enum_key="QUESTION_ALL_SUCCESS",
                args={},
                telemetry={}
            )
        )
        
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            command_batch_result=batch_result
        )
        
        # Execute response router
        result_state = await response_router_node(state)
        
        # Verify routing decision
        assert result_state.next_node == "voice_generation"
        assert result_state.response_phrase_type == AudioPhraseType.HOW_CAN_I_HELP
    
    @pytest.mark.asyncio
    async def test_route_add_item_partial_success(self):
        """Test routing ADD_ITEM + PARTIAL_SUCCESS to clarification_agent"""
        # Create state with partial success batch result
        batch_result = CommandBatchResult(
            results=[OrderResult.error("Size required")],
            total_commands=1,
            successful_commands=0,
            failed_commands=1,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Partial success",
            command_family="ADD_ITEM",
            batch_outcome="PARTIAL_SUCCESS",
            first_error_code="SIZE_REQUIRED",
            response_payload=ResponsePayload(
                enum_key="ADDITEM_PARTIAL_SUCCESS",
                args={},
                telemetry={}
            )
        )
        
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            command_batch_result=batch_result
        )
        
        # Execute response router
        result_state = await response_router_node(state)
        
        # Verify routing decision
        assert result_state.next_node == "clarification_agent"
    
    @pytest.mark.asyncio
    async def test_route_fatal_system(self):
        """Test routing FATAL_SYSTEM to clarification_agent"""
        # Create state with system error batch result
        batch_result = CommandBatchResult(
            results=[OrderResult.error("Database connection failed")],
            total_commands=1,
            successful_commands=0,
            failed_commands=1,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="System error",
            command_family="ADD_ITEM",
            batch_outcome="FATAL_SYSTEM",
            first_error_code="SYSTEM_ERROR",
            response_payload=ResponsePayload(
                enum_key="ADDITEM_FATAL_SYSTEM",
                args={},
                telemetry={}
            )
        )
        
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            command_batch_result=batch_result
        )
        
        # Execute response router
        result_state = await response_router_node(state)
        
        # Verify routing decision
        assert result_state.next_node == "clarification_agent"
    
    @pytest.mark.asyncio
    async def test_no_batch_result(self):
        """Test handling when no batch result is available"""
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            command_batch_result=None
        )
        
        # Execute response router
        result_state = await response_router_node(state)
        
        # Verify fallback routing
        assert result_state.next_node == "voice_generation"
        assert result_state.response_phrase_type == AudioPhraseType.COME_AGAIN


class TestGetSuccessPhraseType:
    """Test the success phrase type mapping function"""
    
    def test_add_item_success_phrase(self):
        """Test ADD_ITEM maps to ITEM_ADDED_SUCCESS"""
        phrase_type = _get_success_phrase_type("ADD_ITEM")
        assert phrase_type == AudioPhraseType.ITEM_ADDED_SUCCESS
    
    def test_remove_item_success_phrase(self):
        """Test REMOVE_ITEM maps to ITEM_REMOVED_SUCCESS"""
        phrase_type = _get_success_phrase_type("REMOVE_ITEM")
        assert phrase_type == AudioPhraseType.ITEM_REMOVED_SUCCESS
    
    def test_clear_order_success_phrase(self):
        """Test CLEAR_ORDER maps to ORDER_CLEARED_SUCCESS"""
        phrase_type = _get_success_phrase_type("CLEAR_ORDER")
        assert phrase_type == AudioPhraseType.ORDER_CLEARED_SUCCESS
    
    def test_question_success_phrase(self):
        """Test QUESTION maps to HOW_CAN_I_HELP"""
        phrase_type = _get_success_phrase_type("QUESTION")
        assert phrase_type == AudioPhraseType.HOW_CAN_I_HELP
    
    def test_unknown_command_family(self):
        """Test unknown command family maps to THANK_YOU"""
        phrase_type = _get_success_phrase_type("UNKNOWN_COMMAND")
        assert phrase_type == AudioPhraseType.THANK_YOU


class TestShouldContinueAfterResponseRouter:
    """Test the routing decision function"""
    
    def test_should_continue_with_next_node(self):
        """Test routing when next_node is set"""
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            next_node="clarification_agent"
        )
        
        result = should_continue_after_response_router(state)
        assert result == "clarification_agent"
    
    def test_should_continue_without_next_node(self):
        """Test routing when next_node is not set"""
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            next_node=None
        )
        
        result = should_continue_after_response_router(state)
        assert result == "voice_generation"  # Default fallback

    @pytest.mark.asyncio
    async def test_route_clarification_command_success(self):
        """Test routing CLARIFICATION_NEEDED + ALL_SUCCESS to clarification agent"""
        # Create state with successful CLARIFICATION_NEEDED batch result
        clarification_result = OrderResult.success(
            message="Clarification needed",
            data={
                "clarification_type": "ambiguous_item",
                "ambiguous_item": "burger",
                "suggested_options": ["Quantum Burger", "Classic Burger"],
                "user_input": "I want a burger",
                "clarification_question": "Which burger would you like?",
                "needs_user_response": True
            }
        )
        
        batch_result = CommandBatchResult(
            results=[clarification_result],
            total_commands=1,
            successful_commands=1,
            failed_commands=0,
            warnings_count=0,
            errors_by_category={},
            errors_by_code={},
            summary_message="Clarification needed",
            command_family="CLARIFICATION_NEEDED",
            batch_outcome="ALL_SUCCESS",  # Clarification commands return success
            first_error_code=None,
            response_payload=ResponsePayload(
                enum_key="CLARIFICATION_NEEDED_ALL_SUCCESS",
                args={},
                telemetry={}
            )
        )
        
        state = ConversationWorkflowState(
            session_id="test-session",
            restaurant_id="1",
            command_batch_result=batch_result
        )
        
        # Execute response router
        result_state = await response_router_node(state)
        
        # Assertions
        assert result_state.next_node == "clarification_agent"
        assert result_state.order_state_changed == False  # Clarification doesn't change order
        
        # Check that clarification context was prepared
        assert hasattr(result_state, 'clarification_context')
        assert result_state.clarification_context is not None
        assert result_state.clarification_context['clarification_commands'] is not None
        assert len(result_state.clarification_context['clarification_commands']) == 1
        
        # Check clarification data
        clarification_cmd = result_state.clarification_context['clarification_commands'][0]
        assert clarification_cmd['ambiguous_item'] == "burger"
        assert clarification_cmd['suggested_options'] == ["Quantum Burger", "Classic Burger"]
        assert clarification_cmd['clarification_question'] == "Which burger would you like?"
        assert clarification_cmd['needs_user_response'] == True