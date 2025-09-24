"""
Clarification needed command for AI order operations
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class ClarificationNeededCommand(BaseCommand):
    """
    Command to handle ambiguous requests that need clarification
    Used when the AI detects ambiguity in user input (e.g., "I want a burger" when multiple burgers exist)
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        ambiguous_item: str,
        suggested_options: List[str],
        user_input: str,
        clarification_question: Optional[str] = None
    ):
        """
        Initialize clarification needed command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID (if applicable)
            ambiguous_item: The item that was ambiguous (e.g., "burger")
            suggested_options: List of possible options to clarify
            user_input: Original user input that caused the ambiguity
            clarification_question: Custom clarification question (optional)
        """
        super().__init__(restaurant_id, order_id)
        self.ambiguous_item = ambiguous_item
        self.suggested_options = suggested_options
        self.user_input = user_input
        self.clarification_question = clarification_question or self._generate_default_question()
    
    def _generate_default_question(self) -> str:
        """Generate a default clarification question"""
        if len(self.suggested_options) == 1:
            return f"Did you mean {self.suggested_options[0]}?"
        elif len(self.suggested_options) == 2:
            return f"Did you mean {self.suggested_options[0]} or {self.suggested_options[1]}?"
        else:
            options_text = ", ".join(self.suggested_options[:-1]) + f", or {self.suggested_options[-1]}"
            return f"Which {self.ambiguous_item} did you want? We have {options_text}."
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the clarification command
        
        This command doesn't modify the order - it just provides clarification information
        that will be used by the response router to generate an appropriate response.
        
        Args:
            context: Command context providing scoped services
            db: Database session for command execution
            
        Returns:
            OrderResult: Result indicating clarification is needed
        """
        # This command doesn't actually execute anything - it's a signal for clarification
        # The response router will handle generating the appropriate clarification response
        
        return OrderResult.success(
            message="Clarification needed",
            data={
                "clarification_type": "ambiguous_item",
                "ambiguous_item": self.ambiguous_item,
                "suggested_options": self.suggested_options,
                "user_input": self.user_input,
                "clarification_question": self.clarification_question,
                "needs_user_response": True
            }
        )
    
    def _get_parameters(self) -> dict:
        """Get command-specific parameters for logging/debugging"""
        return {
            "ambiguous_item": self.ambiguous_item,
            "suggested_options": self.suggested_options,
            "user_input": self.user_input,
            "clarification_question": self.clarification_question
        }
