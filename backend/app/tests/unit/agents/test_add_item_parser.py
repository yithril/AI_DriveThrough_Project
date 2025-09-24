"""
Unit tests for AddItemParser
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agents.parser.add_item_parser import AddItemParser
from app.agents.agent_response.add_item_response import AddItemResponse, ItemToAdd
from app.constants.audio_phrases import AudioPhraseType


class TestAddItemParser:
    """Test AddItemParser functionality"""

    @pytest.mark.asyncio
    async def test_parser_with_ambiguous_item(self):
        """Test parser with ambiguous item (should create CLARIFICATION_NEEDED command)"""
        
        # Create mock state
        mock_state = Mock()
        
        # Mock the AddItemAgent to return a structured response
        mock_agent_result = Mock()
        mock_agent_result.add_item_response = AddItemResponse(
            response_type="clarification_needed",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Which burger would you like?",
            confidence=0.8,
            items_to_add=[
                ItemToAdd(
                    menu_item_id=0,  # Ambiguous
                    quantity=1,
                    ambiguous_item="burger",
                    suggested_options=["Quantum Burger", "Classic Burger", "Chicken Burger"],
                    clarification_question="Which burger would you like?"
                )
            ]
        )
        
        # Mock the agent call
        with patch('app.agents.command_agents.add_item_agent.add_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_result
            
            # Mock context
            context = {
                "service_factory": Mock(),
                "shared_db_session": Mock()
            }
            
            # Create parser
            parser = AddItemParser()
            
            # Test parsing
            result = await parser.parse(mock_state, context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        command = result.command_data
        assert command["intent"] == "CLARIFICATION_NEEDED", "Should be CLARIFICATION_NEEDED command"
        assert command["confidence"] == 0.8, "Should preserve confidence"
        assert "slots" in command, "Should have slots"
        
        slots = command["slots"]
        assert slots["ambiguous_item"] == "burger", "Should have ambiguous_item"
        assert slots["suggested_options"] == ["Quantum Burger", "Classic Burger", "Chicken Burger"], "Should have suggested options"
        assert slots["clarification_question"] == "Which burger would you like?", "Should have clarification question"

    @pytest.mark.asyncio
    async def test_parser_with_clear_item(self):
        """Test parser with clear item (should create ADD_ITEM command)"""
        
        # Create mock state
        mock_state = Mock()
        
        # Mock the AddItemAgent to return a structured response
        mock_agent_result = Mock()
        mock_agent_result.add_item_response = AddItemResponse(
            response_type="success",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Added Quantum Burger to your order",
            confidence=0.9,
            items_to_add=[
                ItemToAdd(
                    menu_item_id=1,  # Clear item
                    quantity=1,
                    size="Large",
                    modifiers=["extra cheese"],
                    special_instructions="No pickles"
                )
            ]
        )
        
        # Mock the agent call
        with patch('app.agents.command_agents.add_item_agent.add_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_result
            
            # Mock context
            context = {
                "service_factory": Mock(),
                "shared_db_session": Mock()
            }
            
            # Create parser
            parser = AddItemParser()
            
            # Test parsing
            result = await parser.parse(mock_state, context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        assert result.command_data is not None, "Should return command data"
        
        command = result.command_data
        assert command["intent"] == "ADD_ITEM", "Should be ADD_ITEM command"
        assert command["confidence"] == 0.9, "Should preserve confidence"
        assert "slots" in command, "Should have slots"
        
        slots = command["slots"]
        assert slots["menu_item_id"] == 1, "Should have menu_item_id"
        assert slots["quantity"] == 1, "Should have quantity"
        assert slots["size"] == "Large", "Should have size"
        assert slots["modifiers"] == ["extra cheese"], "Should have modifiers"
        assert slots["special_instructions"] == "No pickles", "Should have special instructions"

    @pytest.mark.asyncio
    async def test_parser_with_no_response(self):
        """Test parser with no AddItemResponse (should fail)"""
        
        # Create mock state without AddItemResponse
        mock_state = Mock()
        mock_state.add_item_response = None
        
        # Mock context
        context = {
            "service_factory": Mock(),
            "shared_db_session": Mock()
        }
        
        # Create parser
        parser = AddItemParser()
        
        # Test parsing
        result = await parser.parse(mock_state, context)
        
        # Assertions
        assert not result.success, "Parser should fail with no response"
        assert "No structured response" in result.error_message, "Should indicate no response"

    @pytest.mark.asyncio
    async def test_parser_command_validation(self):
        """Test that parser creates valid commands that pass CommandDataValidator"""
        
        # Create mock state
        mock_state = Mock()
        
        # Mock the AddItemAgent to return a structured response
        mock_agent_result = Mock()
        mock_agent_result.add_item_response = AddItemResponse(
            response_type="clarification_needed",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Which burger would you like?",
            confidence=0.8,
            items_to_add=[
                ItemToAdd(
                    menu_item_id=0,  # Ambiguous
                    quantity=1,
                    ambiguous_item="burger",
                    suggested_options=["Quantum Burger", "Classic Burger"],
                    clarification_question="Which burger would you like?"
                )
            ]
        )
        
        # Mock the agent call
        with patch('app.agents.command_agents.add_item_agent.add_item_agent_node') as mock_agent:
            mock_agent.return_value = mock_agent_result
            
            # Mock context
            context = {
                "service_factory": Mock(),
                "shared_db_session": Mock()
            }
            
            # Create parser
            parser = AddItemParser()
            
            # Test parsing
            result = await parser.parse(mock_state, context)
        
        # Assertions
        assert result.success, f"Parser should succeed, got: {result.error_message}"
        
        # Validate the command structure
        from app.commands.command_data_validator import CommandDataValidator
        command = result.command_data
        is_valid, errors = CommandDataValidator.validate(command)
        
        assert is_valid, f"Command should be valid, got errors: {errors}"
        assert command["intent"] == "CLARIFICATION_NEEDED", "Should be CLARIFICATION_NEEDED command"
