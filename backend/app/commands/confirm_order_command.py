"""
Confirm order command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class ConfirmOrderCommand(BaseCommand):
    """
    Command to confirm an order
    Used by AI when customer says "that's it", "done", "confirm"
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int
    ):
        """
        Initialize confirm order command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to confirm
        """
        super().__init__(restaurant_id, order_id)
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the confirm order command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of confirming the order
        """
        try:
            # Get current order to validate it has items
            order_result = await context.order_service.get_order(db, context.get_order_id())
            if not order_result.is_success:
                return OrderResult.error("Could not retrieve order to confirm")
            
            order_data = order_result.data.get("order", {})
            order_items = order_data.get("order_items", [])
            
            if not order_items:
                return OrderResult.error("Cannot confirm empty order. Please add items first.")
            
            # Confirm the order (update status to confirmed)
            result = await context.order_service.confirm_order(db, context.get_order_id())
            
            if result.is_success:
                # Get order summary for confirmation message
                total_amount = order_data.get("total_amount", 0)
                item_count = len(order_items)
                
                result.message = f"Order confirmed! {item_count} items, total: ${total_amount:.2f}. Please pull forward to the window."
                
                # Initialize data dict if it doesn't exist
                if result.data is None:
                    result.data = {}
                
                result.data.update({
                    "order_confirmed": True,
                    "item_count": item_count,
                    "total_amount": total_amount,
                    "order_status": "confirmed"
                })
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to confirm order: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {}
