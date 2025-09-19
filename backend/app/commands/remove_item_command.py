"""
Remove item command for AI order operations
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .target_reference import TargetReference
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService


class RemoveItemCommand(BaseCommand):
    """
    Command to remove an item from an order
    Used by AI when customer wants to remove menu items
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        order_item_id: Optional[int] = None,
        target_ref: Optional[str] = None
    ):
        """
        Initialize remove item command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to remove item from
            order_item_id: Direct order item ID to remove (optional)
            target_ref: Target reference to resolve (optional, e.g., "last_item", "line_1")
        """
        super().__init__(restaurant_id, order_id)
        self.order_item_id = order_item_id
        self.target_ref = target_ref
        
        # Must provide either order_item_id or target_ref
        if not self.order_item_id and not self.target_ref:
            raise ValueError("Must provide either order_item_id or target_ref")
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the remove item command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result of removing the item
        """
        try:
            # Create order service
            order_service = OrderService(db)
            
            # Resolve target reference if needed
            if self.target_ref and not self.order_item_id:
                # Get current order items to resolve target reference
                order_result = await order_service.get_order(self.order_id)
                if not order_result.is_success:
                    return OrderResult.error("Could not retrieve order to resolve target reference")
                
                order_items = order_result.data.get("order", {}).get("order_items", [])
                if not order_items:
                    return OrderResult.error("No items in order to remove")
                
                # Resolve target reference to order_item_id
                resolved_item = TargetReference.resolve_target(self.target_ref, order_items)
                if not resolved_item:
                    return OrderResult.error(f"Could not resolve target reference: {self.target_ref}")
                
                self.order_item_id = resolved_item.id
            
            # Remove item from order
            result = await order_service.remove_item_from_order(
                order_id=self.order_id,
                order_item_id=self.order_item_id
            )
            
            # Enhance message for AI
            if result.is_success:
                result.message = "Item removed from order successfully"
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to remove item from order: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "order_item_id": self.order_item_id,
            "target_ref": self.target_ref
        }
