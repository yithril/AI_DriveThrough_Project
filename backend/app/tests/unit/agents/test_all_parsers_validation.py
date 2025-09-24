"""
Comprehensive validation tests for all parsers used by IntentParserRouter.

Ensures all parsers create valid commands that pass CommandDataValidator
and match the expected contract for CommandExecutor.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.agents.parser.clear_order_parser import ClearOrderParser
from app.agents.parser.confirm_order_parser import ConfirmOrderParser
from app.agents.parser.question_parser import QuestionParser
from app.agents.parser.unknown_parser import UnknownParser
from app.agents.parser.add_item_parser import AddItemParser
from app.agents.parser.remove_item_parser import RemoveItemParser
from app.commands.command_data_validator import CommandDataValidator
from app.commands.intent_classification_schema import IntentType


class TestAllParsersValidation:
    """Test that all parsers create valid commands"""

    @pytest.mark.asyncio
    async def test_clear_order_parser_validation(self):
        """Test ClearOrderParser creates valid commands"""
        parser = ClearOrderParser()
        
        # Test parsing
        result = await parser.parse("clear my order", {})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "CLEAR_ORDER", "Should be CLEAR_ORDER intent"
        assert command["confidence"] == 1.0, "Should have confidence 1.0"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert len(command["slots"]) == 0, "Should have empty slots for clear order"

    @pytest.mark.asyncio
    async def test_confirm_order_parser_validation(self):
        """Test ConfirmOrderParser creates valid commands"""
        parser = ConfirmOrderParser()
        
        # Test parsing
        result = await parser.parse("that's it", {})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "CONFIRM_ORDER", "Should be CONFIRM_ORDER intent"
        assert command["confidence"] == 1.0, "Should have confidence 1.0"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert len(command["slots"]) == 0, "Should have empty slots for confirm order"

    @pytest.mark.asyncio
    async def test_question_parser_validation(self):
        """Test QuestionParser creates valid commands"""
        parser = QuestionParser()
        
        # Test parsing
        result = await parser.parse("What are your hours?", {})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "QUESTION", "Should be QUESTION intent"
        assert command["confidence"] == 1.0, "Should have confidence 1.0"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert "question" in command["slots"], "Should have question in slots"
        assert "category" in command["slots"], "Should have category in slots"
        assert command["slots"]["question"] == "What are your hours?", "Should preserve question"
        assert command["slots"]["category"] == "hours", "Should detect hours category"

    @pytest.mark.asyncio
    async def test_unknown_parser_validation(self):
        """Test UnknownParser creates valid commands"""
        parser = UnknownParser()
        
        # Test parsing
        result = await parser.parse("mumble mumble", {"order_items": []})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "UNKNOWN", "Should be UNKNOWN intent"
        assert command["confidence"] == 1.0, "Should have confidence 1.0"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert "user_input" in command["slots"], "Should have user_input in slots"
        assert "clarifying_question" in command["slots"], "Should have clarifying_question in slots"

    @pytest.mark.asyncio
    async def test_add_item_parser_validation(self):
        """Test AddItemParser creates valid commands"""
        parser = AddItemParser()
        
        # Mock the AddItemAgent to return a structured response
        mock_agent_result = Mock()
        mock_agent_result.add_item_response = Mock()
        mock_agent_result.add_item_response.items_to_add = [
            Mock(
                menu_item_id=1,
                quantity=1,
                size=None,
                modifiers=[],
                special_instructions=None
            )
        ]
        mock_agent_result.add_item_response.confidence = 0.9
        
        # Mock the agent call
        with patch('app.agents.command_agents.add_item_agent.add_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_result
            
            # Test parsing
            result = await parser.parse("I want a burger", {})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "ADD_ITEM", "Should be ADD_ITEM intent"
        assert command["confidence"] == 0.9, "Should preserve confidence"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert "menu_item_id" in command["slots"], "Should have menu_item_id in slots"
        assert "quantity" in command["slots"], "Should have quantity in slots"

    @pytest.mark.asyncio
    async def test_add_item_parser_clarification_validation(self):
        """Test AddItemParser creates valid CLARIFICATION_NEEDED commands"""
        parser = AddItemParser()
        
        # Mock the AddItemAgent to return a clarification response
        mock_agent_result = Mock()
        mock_agent_result.add_item_response = Mock()
        mock_agent_result.add_item_response.items_to_add = [
            Mock(
                menu_item_id=0,  # Ambiguous
                quantity=1,
                ambiguous_item="burger",
                suggested_options=["Quantum Burger", "Classic Burger"],
                clarification_question="Which burger would you like?"
            )
        ]
        mock_agent_result.add_item_response.confidence = 0.8
        
        # Mock the agent call
        with patch('app.agents.command_agents.add_item_agent.add_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_result
            
            # Test parsing
            result = await parser.parse("I want a burger", {})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "CLARIFICATION_NEEDED", "Should be CLARIFICATION_NEEDED intent"
        assert command["confidence"] == 0.8, "Should preserve confidence"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert "ambiguous_item" in command["slots"], "Should have ambiguous_item in slots"
        assert "suggested_options" in command["slots"], "Should have suggested_options in slots"
        assert "clarification_question" in command["slots"], "Should have clarification_question in slots"

    @pytest.mark.asyncio
    async def test_remove_item_parser_validation(self):
        """Test RemoveItemParser creates valid commands"""
        parser = RemoveItemParser()
        
        # Mock the RemoveItemAgent to return a structured response
        mock_agent_response = Mock()
        mock_agent_response.items_to_remove = [
            Mock(
                order_item_id=1,
                target_ref=None,
                removal_reason="Changed my mind"
            )
        ]
        mock_agent_response.confidence = 0.9
        
        # Mock the agent call
        with patch('app.agents.parser.remove_item_parser.remove_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_response
            
            # Test parsing
            result = await parser.parse("remove the burger", {"order_items": []})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "REMOVE_ITEM", "Should be REMOVE_ITEM intent"
        assert command["confidence"] == 0.9, "Should preserve confidence"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert "order_item_id" in command["slots"], "Should have order_item_id in slots"
        assert "target_ref" in command["slots"], "Should have target_ref in slots"
        assert "removal_reason" in command["slots"], "Should have removal_reason in slots"

    @pytest.mark.asyncio
    async def test_remove_item_parser_clarification_validation(self):
        """Test RemoveItemParser creates valid CLARIFICATION_NEEDED commands"""
        parser = RemoveItemParser()
        
        # Mock the RemoveItemAgent to return a clarification response
        mock_agent_response = Mock()
        mock_agent_response.items_to_remove = [
            Mock(
                order_item_id=None,  # Ambiguous
                target_ref=None,
                ambiguous_item="item",
                suggested_options=["Burger", "Fries"],
                clarification_question="Which item would you like to remove?"
            )
        ]
        mock_agent_response.confidence = 0.8
        
        # Mock the agent call
        with patch('app.agents.parser.remove_item_parser.remove_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_response
            
            # Test parsing
            result = await parser.parse("remove something", {"order_items": []})
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        # Validate command structure
        is_valid, errors = CommandDataValidator.validate(result.command_data)
        assert is_valid, f"Command should be valid, got errors: {errors}"
        
        # Check specific fields
        command = result.command_data
        assert command["intent"] == "CLARIFICATION_NEEDED", "Should be CLARIFICATION_NEEDED intent"
        assert command["confidence"] == 0.8, "Should preserve confidence"
        assert isinstance(command["slots"], dict), "Should have slots dict"
        assert "ambiguous_item" in command["slots"], "Should have ambiguous_item in slots"
        assert "suggested_options" in command["slots"], "Should have suggested_options in slots"
        assert "clarification_question" in command["slots"], "Should have clarification_question in slots"

    @pytest.mark.asyncio
    async def test_modify_item_parser_not_implemented(self):
        """Test ModifyItemParser returns error (not yet implemented)"""
        from app.agents.parser.modify_item_parser import ModifyItemParser
        
        parser = ModifyItemParser()
        
        # Test parsing
        result = await parser.parse("change the burger to large", {})
        
        # Assertions - should fail since not implemented
        assert not result.success, "Parser should fail since not implemented"
        assert "not yet implemented" in result.error_message, "Should indicate not implemented"

    def test_all_intent_types_covered(self):
        """Test that all IntentType values have corresponding parsers"""
        from app.agents.nodes.intent_parser_router_node import IntentParserRouter
        
        router = IntentParserRouter()
        supported_intents = router.get_supported_intents()
        
        # Intent types that should be covered by parsers
        required_intents = [
            IntentType.CLEAR_ORDER,
            IntentType.CONFIRM_ORDER,
            IntentType.QUESTION,
            IntentType.UNKNOWN,
            IntentType.ADD_ITEM,
            IntentType.REMOVE_ITEM,
            IntentType.MODIFY_ITEM
        ]
        
        # Check that required intent types are covered
        for intent_type in required_intents:
            assert intent_type in supported_intents, f"IntentType {intent_type} not covered by parsers"
        
        # Check that all supported intents are valid IntentType values
        for intent in supported_intents:
            assert intent in [it.value for it in IntentType], f"Unsupported intent: {intent}"

    def test_parser_contract_consistency(self):
        """Test that all parsers follow the same contract"""
        parsers = [
            ClearOrderParser(),
            ConfirmOrderParser(),
            QuestionParser(),
            UnknownParser(),
            AddItemParser(),
            RemoveItemParser()
        ]
        
        for parser in parsers:
            # Check that parser has required methods
            assert hasattr(parser, 'parse'), f"{parser.__class__.__name__} missing parse method"
            assert hasattr(parser, 'intent_type'), f"{parser.__class__.__name__} missing intent_type"
            
            # Check that intent_type is valid
            assert parser.intent_type in [it.value for it in IntentType], f"Invalid intent_type: {parser.intent_type}"
