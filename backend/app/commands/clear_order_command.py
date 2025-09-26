"""
Clear order command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class ClearOrderCommand(BaseCommand):
    """
    Command to clear all items from an order
    Used by AI when customer wants to start over or clear their order
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int
    ):
        """
        Initialize clear order command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to clear
        """
        super().__init__(restaurant_id, order_id)
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the clear order command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of clearing the order
        """
        try:
            # Clear the order using OrderService from context
            result = await context.order_service.clear_order(
                db=db,
                order_id=str(context.get_order_id()),
                session_id=context.get_session_id(),  # NEW: Pass session_id
                restaurant_id=context.restaurant_id    # NEW: Pass restaurant_id
            )
            
            # Enhance message for AI
            if result.is_success:
                result.message = "Order cleared successfully. Ready for new items."
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to clear order: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {}
