"""
Clear order command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService


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
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the clear order command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result of clearing the order
        """
        try:
            # Create order service
            order_service = OrderService(db)
            
            # Clear the order
            result = await order_service.clear_order(order_id=self.order_id)
            
            # Enhance message for AI
            if result.is_success:
                result.message = "Order cleared successfully. Ready for new items."
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to clear order: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {}
