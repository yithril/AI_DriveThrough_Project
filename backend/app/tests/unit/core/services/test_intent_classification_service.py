"""
Unit tests for IntentClassificationService
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.core.services.conversation.intent_classification_service import IntentClassificationService
from app.commands.intent_classification_schema import IntentType, IntentClassificationResult


class TestIntentClassificationService:
    """Test cases for IntentClassificationService"""
    
    @pytest.fixture
    def mock_service_factory(self):
        """Mock service factory"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_service_factory):
        """Create service with mocked dependencies"""
        return IntentClassificationService(mock_service_factory)
    
    @pytest.mark.asyncio
    async def test_classify_intent_success(self, service, mocker):
        """Test successful intent classification"""
        # Mock the LLM response
        mock_llm = mocker.patch('app.core.services.conversation.intent_classification_service.ChatOpenAI')
        mock_llm_instance = AsyncMock()
        mock_llm.return_value.with_structured_output.return_value = mock_llm_instance
        
        # Mock the LLM response
        mock_result = IntentClassificationResult(
            intent=IntentType.ADD_ITEM,
            confidence=0.9,
            cleansed_input="add a burger"
        )
        mock_llm_instance.ainvoke.return_value = mock_result
        
        # Test the service
        result = await service.classify_intent(
            user_input="I want to add a burger",
            conversation_history=[],
            order_state={},
            current_state="ORDERING"
        )
        
        # Verify result
        assert result.intent == IntentType.ADD_ITEM
        assert result.confidence == 0.9
        assert result.cleansed_input == "add a burger"
    
    @pytest.mark.asyncio
    async def test_classify_intent_failure_fallback(self, service, mocker):
        """Test intent classification failure with fallback"""
        # Mock the LLM to raise exception
        mock_llm = mocker.patch('app.core.services.conversation.intent_classification_service.ChatOpenAI')
        mock_llm_instance = AsyncMock()
        mock_llm.return_value.with_structured_output.return_value = mock_llm_instance
        mock_llm_instance.ainvoke.side_effect = Exception("LLM failed")
        
        # Test the service
        result = await service.classify_intent(
            user_input="mumble mumble",
            conversation_history=[],
            order_state={},
            current_state="ORDERING"
        )
        
        # Verify fallback result
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.1
        assert result.cleansed_input == "mumble mumble"
    
    def test_should_continue_after_classification_high_confidence(self, service):
        """Test routing decision for high confidence"""
        result = IntentClassificationResult(
            intent=IntentType.ADD_ITEM,
            confidence=0.9,
            cleansed_input="add a burger"
        )
        
        next_step = service.should_continue_after_classification(result)
        assert next_step == "state_transition"
    
    def test_should_continue_after_classification_low_confidence(self, service):
        """Test routing decision for low confidence"""
        result = IntentClassificationResult(
            intent=IntentType.UNKNOWN,
            confidence=0.5,
            cleansed_input="mumble mumble"
        )
        
        next_step = service.should_continue_after_classification(result)
        assert next_step == "voice_generation"
