"""
Unit tests for StateTransitionService
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.core.services.conversation.state_transition_service import StateTransitionService
from app.commands.intent_classification_schema import IntentType
from app.models.state_machine_models import ConversationState


class TestStateTransitionService:
    """Test cases for StateTransitionService"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        factory = Mock()
        factory.create_order_session_service.return_value = AsyncMock()
        return factory
    
    @pytest.fixture
    def service(self, mock_service_factory):
        """Create service with mocked dependencies"""
        return StateTransitionService(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_validate_transition_success(self, service, mocker):
        """Test successful state transition"""
        # Mock the state machine
        mock_state_machine = mocker.patch.object(service, 'state_machine')
        mock_transition = Mock()
        mock_transition.is_valid = True
        mock_transition.target_state = ConversationState.ORDERING
        mock_transition.requires_command = True
        mock_transition.response_phrase_type = None
        mock_state_machine.get_transition.return_value = mock_transition
        
        # Mock the order session service
        mock_order_session = service.service_factory.create_order_session_service.return_value
        mock_order_session.update_session = AsyncMock()
        
        # Test the service
        result = await service.validate_transition(
            current_state=ConversationState.ORDERING,
            intent_type=IntentType.ADD_ITEM,
            session_id="test-session"
        )
        
        # Verify result
        assert result["is_valid"] is True
        assert result["target_state"] == ConversationState.ORDERING
        assert result["requires_command"] is True
        
        # Verify order session was updated
        mock_order_session.update_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_transition_invalid(self, service, mocker):
        """Test invalid state transition"""
        # Mock the state machine
        mock_state_machine = mocker.patch.object(service, 'state_machine')
        mock_transition = Mock()
        mock_transition.is_valid = False
        mock_transition.target_state = None
        mock_transition.requires_command = False
        mock_transition.response_phrase_type = None
        mock_state_machine.get_transition.return_value = mock_transition
        
        # Test the service
        result = await service.validate_transition(
            current_state=ConversationState.ORDERING,
            intent_type=IntentType.UNKNOWN,
            session_id="test-session"
        )
        
        # Verify result
        assert result["is_valid"] is False
        assert result["target_state"] is None
        assert result["requires_command"] is False
    
    @pytest.mark.asyncio
    async def test_validate_transition_exception(self, service, mocker):
        """Test state transition with exception"""
        # Mock the state machine to raise exception
        mock_state_machine = mocker.patch.object(service, 'state_machine')
        mock_state_machine.get_transition.side_effect = Exception("State machine failed")
        
        # Test the service
        result = await service.validate_transition(
            current_state=ConversationState.ORDERING,
            intent_type=IntentType.ADD_ITEM,
            session_id="test-session"
        )
        
        # Verify error result
        assert result["is_valid"] is False
        assert "error" in result
    
    def test_should_continue_after_transition_requires_command(self, service):
        """Test routing decision when command is required"""
        transition_result = {
            "is_valid": True,
            "requires_command": True
        }
        
        next_step = service.should_continue_after_transition(transition_result)
        assert next_step == "intent_parser_router"
    
    def test_should_continue_after_transition_no_command(self, service):
        """Test routing decision when no command is required"""
        transition_result = {
            "is_valid": True,
            "requires_command": False
        }
        
        next_step = service.should_continue_after_transition(transition_result)
        assert next_step == "voice_generation"
