"""
Unknown command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class UnknownCommand(BaseCommand):
    """
    Command to handle unknown or unclear intents
    Used by AI when customer input is unclear or doesn't match any known intent
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        user_input: str,
        clarifying_question: str = "I'm sorry, I didn't understand. Could you please repeat that?"
    ):
        """
        Initialize unknown command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID (may be None for general unknown intents)
            user_input: The customer's unclear input
            clarifying_question: Question to ask for clarification
        """
        super().__init__(restaurant_id, order_id)
        self.user_input = user_input
        self.clarifying_question = clarifying_question
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the unknown command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of handling the unknown intent
        """
        try:
            # Return the clarifying question as the response
            return OrderResult.success(
                message=self.clarifying_question,
                data={
                    "user_input": self.user_input,
                    "clarifying_question": self.clarifying_question,
                    "response_category": "clarification_needed",
                    "needs_clarification": True
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to handle unknown intent: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "user_input": self.user_input,
            "clarifying_question": self.clarifying_question
        }
