"""
Small talk command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class SmallTalkCommand(BaseCommand):
    """
    Command to handle small talk and social interactions
    Used by AI when customer engages in casual conversation
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        user_input: str,
        response_type: str = "general"
    ):
        """
        Initialize small talk command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID (may be None for general small talk)
            user_input: The customer's input
            response_type: Type of response (greeting, thanks, goodbye, compliment, general)
        """
        super().__init__(restaurant_id, order_id)
        self.user_input = user_input
        self.response_type = response_type
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the small talk command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of handling the small talk
        """
        try:
            # Generate appropriate response based on response type
            response = self._generate_response()
            
            return OrderResult.success(
                message=response,
                data={
                    "user_input": self.user_input,
                    "response_type": self.response_type,
                    "response_category": "small_talk"
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to handle small talk: {str(e)}")
    
    def _generate_response(self) -> str:
        """Generate appropriate response based on response type"""
        if self.response_type == "greeting":
            return "Hello! Welcome to our drive-thru. How can I help you today?"
        
        elif self.response_type == "thanks":
            return "You're very welcome! Is there anything else I can help you with?"
        
        elif self.response_type == "goodbye":
            return "Thank you for choosing us! Have a great day and drive safely!"
        
        elif self.response_type == "compliment":
            return "Thank you so much! That's very kind of you to say. How can I help you with your order today?"
        
        else:  # general
            return "That's nice to hear! What can I help you with for your order today?"
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "user_input": self.user_input,
            "response_type": self.response_type
        }
