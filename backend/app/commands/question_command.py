"""
Question command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class QuestionCommand(BaseCommand):
    """
    Command to handle customer questions
    Used by AI when customer asks questions about menu, pricing, etc.
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        question: str,
        category: str = "general"
    ):
        """
        Initialize question command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID (may be None for general questions)
            question: The customer's question
            category: Question category (menu, pricing, hours, location, ingredients, general)
        """
        super().__init__(restaurant_id, order_id)
        self.question = question
        self.category = category
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the question command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of handling the question
        """
        try:
            # Generate appropriate response based on question category
            response = self._generate_response(context)
            
            return OrderResult.success(
                message=response,
                data={
                    "question": self.question,
                    "category": self.category,
                    "response_type": "question_answer"
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to handle question: {str(e)}")
    
    def _generate_response(self, context: CommandContext) -> str:
        """Generate appropriate response based on question category"""
        if self.category == "menu":
            return "I'd be happy to help you with our menu! What type of food are you looking for? We have burgers, fries, drinks, and more."
        
        elif self.category == "pricing":
            return "I can help you with pricing! What specific items would you like to know the price for?"
        
        elif self.category == "hours":
            return "We're open 24/7! You can place an order anytime."
        
        elif self.category == "location":
            return "We're located at 123 Main Street. You can find us right off the highway exit."
        
        elif self.category == "ingredients":
            return "I can help you with ingredient information! What specific items would you like to know about?"
        
        else:  # general
            return "I'm here to help! What would you like to know about our menu or ordering process?"
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "question": self.question,
            "category": self.category
        }
