"""
Repeat command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


class RepeatCommand(BaseCommand):
    """
    Command to repeat order items
    Used by AI when customer wants to hear their order repeated
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        scope: str = "full_order",
        target_ref: str = "last_item"
    ):
        """
        Initialize repeat command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to repeat
            scope: What to repeat - "full_order" or "last_item"
            target_ref: Target reference for last_item scope
        """
        super().__init__(restaurant_id, order_id)
        self.scope = scope
        self.target_ref = target_ref
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the repeat command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of repeating the order
        """
        try:
            # Get current order to repeat
            order_result = await context.order_service.get_order(db, context.get_order_id())
            if not order_result.is_success:
                return OrderResult.error("Could not retrieve order to repeat")
            
            order_data = order_result.data.get("order", {})
            order_items = order_data.get("order_items", [])
            
            if not order_items:
                return OrderResult.error("No items in order to repeat")
            
            # Generate repeat message based on scope
            if self.scope == "full_order":
                message = self._generate_full_order_message(order_items, order_data)
            else:  # last_item
                message = self._generate_last_item_message(order_items)
            
            return OrderResult.success(
                message=message,
                data={
                    "repeat_scope": self.scope,
                    "target_ref": self.target_ref,
                    "order_items": order_items,
                    "total_amount": order_data.get("total_amount", 0)
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to repeat order: {str(e)}")
    
    def _generate_full_order_message(self, order_items: list, order_data: dict) -> str:
        """Generate message for full order repeat"""
        if not order_items:
            return "Your order is empty."
        
        total_amount = order_data.get("total_amount", 0)
        item_count = len(order_items)
        
        message = f"Here's your order: "
        for i, item in enumerate(order_items, 1):
            item_name = item.get("menu_item_name", "Unknown item")
            quantity = item.get("quantity", 1)
            price = item.get("price", 0)
            
            if quantity > 1:
                message += f"{quantity}x {item_name} (${price:.2f} each), "
            else:
                message += f"{item_name} (${price:.2f}), "
        
        # Remove trailing comma and add total
        message = message.rstrip(", ") + f". Total: ${total_amount:.2f}"
        
        return message
    
    def _generate_last_item_message(self, order_items: list) -> str:
        """Generate message for last item repeat"""
        if not order_items:
            return "No items in your order."
        
        last_item = order_items[-1]
        item_name = last_item.get("menu_item_name", "Unknown item")
        quantity = last_item.get("quantity", 1)
        price = last_item.get("price", 0)
        
        if quantity > 1:
            return f"Your last item: {quantity}x {item_name} (${price:.2f} each)"
        else:
            return f"Your last item: {item_name} (${price:.2f})"
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "scope": self.scope,
            "target_ref": self.target_ref
        }
