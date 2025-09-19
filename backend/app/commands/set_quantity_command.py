"""
Set quantity command for AI order operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .target_reference import TargetReference
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService


class SetQuantityCommand(BaseCommand):
    """
    Command to set the quantity of an existing order item
    Used by AI when customer wants to change item quantity
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        target_ref: str,
        quantity: int
    ):
        """
        Initialize set quantity command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to modify item in
            target_ref: Target reference to resolve (e.g., "last_item", "line_1")
            quantity: New quantity to set
        """
        super().__init__(restaurant_id, order_id)
        self.target_ref = target_ref
        self.quantity = quantity
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the set quantity command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result of setting the quantity
        """
        try:
            # Create order service
            order_service = OrderService(db)
            
            # Get current order items to resolve target reference
            order_result = await order_service.get_order(self.order_id)
            if not order_result.is_success:
                return OrderResult.error("Could not retrieve order to resolve target reference")
            
            order_items = order_result.data.get("order", {}).get("order_items", [])
            if not order_items:
                return OrderResult.error("No items in order to modify")
            
            # Resolve target reference to order item
            resolved_item = TargetReference.resolve_target(self.target_ref, order_items)
            if not resolved_item:
                return OrderResult.error(f"Could not resolve target reference: {self.target_ref}")
            
            # Update quantity in the database
            # For now, we'll use a placeholder - in full implementation, you'd update the order item
            result = await order_service.update_order_item_quantity(
                order_id=self.order_id,
                order_item_id=resolved_item.id,
                quantity=self.quantity
            )
            
            if result.is_success:
                result.message = f"Updated {self.target_ref} quantity to {self.quantity}"
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to set quantity: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "target_ref": self.target_ref,
            "quantity": self.quantity
        }
