"""
Unit tests for ConversationOrchestrator

Tests the new service-based orchestrator with all different routes and integrations.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.core.conversation_orchestrator import ConversationOrchestrator
from app.core.service_factory import ServiceFactory
from app.commands.intent_classification_schema import IntentType, IntentClassificationResult
from app.models.state_machine_models import ConversationState
from app.dto.order_result import OrderResult, CommandBatchResult


class TestConversationOrchestrator:
    """Test cases for the new service-based ConversationOrchestrator"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory with all required services"""
        factory = Mock(spec=ServiceFactory)
        
        # Mock all the services the orchestrator needs
        factory.create_voice_service.return_value = AsyncMock()
        factory.create_order_service.return_value = AsyncMock()
        factory.create_order_session_service.return_value = AsyncMock()
        factory.create_customization_validator.return_value = Mock()
        
        return factory
    
    @pytest.fixture
    def orchestrator(self, mock_service_factory):
        """Create orchestrator with mocked dependencies"""
        return ConversationOrchestrator(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_low_confidence_intent_goes_to_voice_generation(self, orchestrator, mocker):
        """Test that low confidence intents go directly to voice generation"""
        # Mock intent classification service to return low confidence
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.UNKNOWN,
            confidence=0.5,  # Low confidence
            cleansed_input="mumble mumble"
        )
        
        # Mock voice generation service
        mock_voice_service = mocker.patch.object(orchestrator.voice_generation_service, 'generate_voice_response')
        mock_voice_service.return_value = {
            "success": True,
            "response_text": "I'm sorry, I didn't understand. Could you please try again?",
            "audio_url": "http://example.com/audio.mp3"
        }
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="mumble mumble",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify intent classification was called
        mock_intent_service.assert_called_once()
        
        # Verify voice generation was called directly (bypassing other steps)
        mock_voice_service.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert "didn't understand" in result["response_text"]
        assert result["audio_url"] == "http://example.com/audio.mp3"
    
    @pytest.mark.asyncio
    async def test_invalid_state_transition_goes_to_voice_generation(self, orchestrator, mocker):
        """Test that invalid state transitions go directly to voice generation"""
        # Mock intent classification service to return high confidence
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.ADD_ITEM,
            confidence=0.9,
            cleansed_input="add a burger"
        )
        
        # Mock state transition service to return invalid transition
        mock_state_service = mocker.patch.object(orchestrator.state_transition_service, 'validate_transition')
        mock_state_service.return_value = {
            "is_valid": False,
            "target_state": ConversationState.ORDERING,
            "requires_command": False,
            "response_phrase_type": None,
            "current_state": ConversationState.ORDERING
        }
        
        # Mock voice generation service
        mock_voice_service = mocker.patch.object(orchestrator.voice_generation_service, 'generate_voice_response')
        mock_voice_service.return_value = {
            "success": True,
            "response_text": "I'm sorry, I can't help with that right now. Please try ordering something.",
            "audio_url": "http://example.com/audio.mp3"
        }
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="add a burger",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify state transition was called
        mock_state_service.assert_called_once()
        
        # Verify voice generation was called directly (bypassing other steps)
        mock_voice_service.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert "can't help with that" in result["response_text"]
    
    @pytest.mark.asyncio
    async def test_successful_add_item_flow(self, orchestrator, mocker):
        """Test successful ADD_ITEM processing through all steps"""
        # Mock intent classification service
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.ADD_ITEM,
            confidence=0.9,
            cleansed_input="add a burger"
        )
        
        # Mock state transition service
        mock_state_service = mocker.patch.object(orchestrator.state_transition_service, 'validate_transition')
        mock_state_service.return_value = {
            "is_valid": True,
            "target_state": ConversationState.ORDERING,
            "requires_command": True,
            "response_phrase_type": None,
            "current_state": ConversationState.ORDERING
        }
        
        # Mock intent parser router service
        mock_parser_service = mocker.patch.object(orchestrator.intent_parser_router_service, 'route_to_parser')
        mock_parser_service.return_value = {
            "success": True,
            "commands": [{"intent": "ADD_ITEM", "menu_item_id": 1, "quantity": 1}],
            "response_text": ""
        }
        
        # Mock command executor service
        mock_command_service = mocker.patch.object(orchestrator.command_executor_service, 'execute_commands')
        mock_command_service.return_value = {
            "success": True,
            "command_batch_result": Mock(spec=CommandBatchResult),
            "response_text": "Item added successfully"
        }
        
        # Mock response aggregator service
        mock_aggregator_service = mocker.patch.object(orchestrator.response_aggregator_service, 'aggregate_response')
        mock_aggregator_service.return_value = {
            "success": True,
            "response_text": "Your order has been updated.",
            "response_phrase_type": None
        }
        
        # Mock voice generation service
        mock_voice_service = mocker.patch.object(orchestrator.voice_generation_service, 'generate_voice_response')
        mock_voice_service.return_value = {
            "success": True,
            "response_text": "Your order has been updated.",
            "audio_url": "http://example.com/audio.mp3"
        }
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="add a burger",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify all services were called in the correct order
        mock_intent_service.assert_called_once()
        mock_state_service.assert_called_once()
        mock_parser_service.assert_called_once()
        mock_command_service.assert_called_once()
        mock_aggregator_service.assert_called_once()
        mock_voice_service.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert "order has been updated" in result["response_text"]
        assert result["audio_url"] == "http://example.com/audio.mp3"
    
    @pytest.mark.asyncio
    async def test_parser_failure_returns_error(self, orchestrator, mocker):
        """Test that parser failures return appropriate error responses"""
        # Mock intent classification service
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.ADD_ITEM,
            confidence=0.9,
            cleansed_input="add a burger"
        )
        
        # Mock state transition service
        mock_state_service = mocker.patch.object(orchestrator.state_transition_service, 'validate_transition')
        mock_state_service.return_value = {
            "is_valid": True,
            "target_state": ConversationState.ORDERING,
            "requires_command": True,
            "response_phrase_type": None,
            "current_state": ConversationState.ORDERING
        }
        
        # Mock intent parser router service to return failure
        mock_parser_service = mocker.patch.object(orchestrator.intent_parser_router_service, 'route_to_parser')
        mock_parser_service.return_value = {
            "success": False,
            "commands": [],
            "response_text": "I'm sorry, I didn't understand. Could you please try again?",
            "error": "Parser failed"
        }
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="add a burger",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify parser was called
        mock_parser_service.assert_called_once()
        
        # Verify result
        assert result["success"] is False
        assert "didn't understand" in result["response_text"]
        assert result["audio_url"] is None
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, orchestrator, mocker):
        """Test that exceptions are properly handled"""
        # Mock intent classification service to raise exception
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.side_effect = Exception("Intent classification failed")
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="add a burger",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify result
        assert result["success"] is False
        assert "trouble processing" in result["response_text"]
        assert result["audio_url"] is None
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_clear_order_flow(self, orchestrator, mocker):
        """Test CLEAR_ORDER processing through all steps"""
        # Mock intent classification service
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.CLEAR_ORDER,
            confidence=0.9,
            cleansed_input="clear my order"
        )
        
        # Mock state transition service
        mock_state_service = mocker.patch.object(orchestrator.state_transition_service, 'validate_transition')
        mock_state_service.return_value = {
            "is_valid": True,
            "target_state": ConversationState.ORDERING,
            "requires_command": True,
            "response_phrase_type": None,
            "current_state": ConversationState.ORDERING
        }
        
        # Mock intent parser router service
        mock_parser_service = mocker.patch.object(orchestrator.intent_parser_router_service, 'route_to_parser')
        mock_parser_service.return_value = {
            "success": True,
            "commands": [{"intent": "CLEAR_ORDER"}],
            "response_text": ""
        }
        
        # Mock command executor service
        mock_command_service = mocker.patch.object(orchestrator.command_executor_service, 'execute_commands')
        mock_command_service.return_value = {
            "success": True,
            "command_batch_result": Mock(spec=CommandBatchResult),
            "response_text": "Order cleared successfully"
        }
        
        # Mock response aggregator service
        mock_aggregator_service = mocker.patch.object(orchestrator.response_aggregator_service, 'aggregate_response')
        mock_aggregator_service.return_value = {
            "success": True,
            "response_text": "Your order has been cleared.",
            "response_phrase_type": None
        }
        
        # Mock voice generation service
        mock_voice_service = mocker.patch.object(orchestrator.voice_generation_service, 'generate_voice_response')
        mock_voice_service.return_value = {
            "success": True,
            "response_text": "Your order has been cleared.",
            "audio_url": "http://example.com/audio.mp3"
        }
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="clear my order",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify all services were called
        mock_intent_service.assert_called_once()
        mock_state_service.assert_called_once()
        mock_parser_service.assert_called_once()
        mock_command_service.assert_called_once()
        mock_aggregator_service.assert_called_once()
        mock_voice_service.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert "order has been cleared" in result["response_text"]
        assert result["audio_url"] == "http://example.com/audio.mp3"
    
    @pytest.mark.asyncio
    async def test_question_intent_flow(self, orchestrator, mocker):
        """Test QUESTION intent processing through all steps"""
        # Mock intent classification service
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.QUESTION,
            confidence=0.9,
            cleansed_input="what do you have"
        )
        
        # Mock state transition service
        mock_state_service = mocker.patch.object(orchestrator.state_transition_service, 'validate_transition')
        mock_state_service.return_value = {
            "is_valid": True,
            "target_state": ConversationState.ORDERING,
            "requires_command": True,
            "response_phrase_type": None,
            "current_state": ConversationState.ORDERING
        }
        
        # Mock intent parser router service
        mock_parser_service = mocker.patch.object(orchestrator.intent_parser_router_service, 'route_to_parser')
        mock_parser_service.return_value = {
            "success": True,
            "commands": [{"intent": "QUESTION", "question_type": "menu_inquiry"}],
            "response_text": ""
        }
        
        # Mock command executor service
        mock_command_service = mocker.patch.object(orchestrator.command_executor_service, 'execute_commands')
        mock_command_service.return_value = {
            "success": True,
            "command_batch_result": Mock(spec=CommandBatchResult),
            "response_text": "Here's our menu"
        }
        
        # Mock response aggregator service
        mock_aggregator_service = mocker.patch.object(orchestrator.response_aggregator_service, 'aggregate_response')
        mock_aggregator_service.return_value = {
            "success": True,
            "response_text": "Here's our menu",
            "response_phrase_type": None
        }
        
        # Mock voice generation service
        mock_voice_service = mocker.patch.object(orchestrator.voice_generation_service, 'generate_voice_response')
        mock_voice_service.return_value = {
            "success": True,
            "response_text": "Here's our menu",
            "audio_url": "http://example.com/audio.mp3"
        }
        
        # Test the orchestrator
        result = await orchestrator.process_conversation_turn(
            user_input="what do you have",
            session_id="test-session",
            restaurant_id=1
        )
        
        # Verify all services were called
        mock_intent_service.assert_called_once()
        mock_state_service.assert_called_once()
        mock_parser_service.assert_called_once()
        mock_command_service.assert_called_once()
        mock_aggregator_service.assert_called_once()
        mock_voice_service.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert "menu" in result["response_text"]
        assert result["audio_url"] == "http://example.com/audio.mp3"
    
    @pytest.mark.asyncio
    async def test_service_integration_with_conversation_history(self, orchestrator, mocker):
        """Test that conversation history is properly passed to services"""
        # Mock all services
        mock_intent_service = mocker.patch.object(orchestrator.intent_classification_service, 'classify_intent')
        mock_intent_service.return_value = IntentClassificationResult(
            intent=IntentType.ADD_ITEM,
            confidence=0.9,
            cleansed_input="add a burger"
        )
        
        mock_state_service = mocker.patch.object(orchestrator.state_transition_service, 'validate_transition')
        mock_state_service.return_value = {
            "is_valid": True,
            "target_state": ConversationState.ORDERING,
            "requires_command": True,
            "response_phrase_type": None,
            "current_state": ConversationState.ORDERING
        }
        
        mock_parser_service = mocker.patch.object(orchestrator.intent_parser_router_service, 'route_to_parser')
        mock_parser_service.return_value = {
            "success": True,
            "commands": [{"intent": "ADD_ITEM", "menu_item_id": 1, "quantity": 1}],
            "response_text": ""
        }
        
        mock_command_service = mocker.patch.object(orchestrator.command_executor_service, 'execute_commands')
        mock_command_service.return_value = {
            "success": True,
            "command_batch_result": Mock(spec=CommandBatchResult),
            "response_text": "Item added successfully"
        }
        
        mock_aggregator_service = mocker.patch.object(orchestrator.response_aggregator_service, 'aggregate_response')
        mock_aggregator_service.return_value = {
            "success": True,
            "response_text": "Your order has been updated.",
            "response_phrase_type": None
        }
        
        mock_voice_service = mocker.patch.object(orchestrator.voice_generation_service, 'generate_voice_response')
        mock_voice_service.return_value = {
            "success": True,
            "response_text": "Your order has been updated.",
            "audio_url": "http://example.com/audio.mp3"
        }
        
        # Test with conversation history and order state
        conversation_history = [
            {"user": "Hello", "assistant": "Hi! What can I get you?"},
            {"user": "I want a burger", "assistant": "Great! I'll add that to your order."}
        ]
        order_state = {
            "line_items": [{"item": "burger", "quantity": 1}],
            "total": 10.99
        }
        
        result = await orchestrator.process_conversation_turn(
            user_input="add fries too",
            session_id="test-session",
            restaurant_id=1,
            conversation_history=conversation_history,
            order_state=order_state
        )
        
        # Verify that conversation history and order state were passed to services
        mock_intent_service.assert_called_once()
        call_args = mock_intent_service.call_args
        assert call_args[1]["conversation_history"] == conversation_history
        assert call_args[1]["order_state"] == order_state
        
        # Verify result
        assert result["success"] is True
        assert "order has been updated" in result["response_text"]
