"""
Repeat command for AI order operations
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .target_reference import TargetReference
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService


class RepeatCommand(BaseCommand):
    """
    Command to repeat/add a copy of an existing order item
    Used by AI when customer says "repeat that", "same as last time", "add another one"
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        target_ref: str,
        scope: str = "last_item"
    ):
        """
        Initialize repeat command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to add repeated item to
            target_ref: Target reference to repeat (e.g., "last_item", "line_1")
            scope: Scope of repeat ("last_item" or "full_order")
        """
        super().__init__(restaurant_id, order_id)
        self.target_ref = target_ref
        self.scope = scope
        
        if self.scope not in ["last_item", "full_order"]:
            raise ValueError("Scope must be 'last_item' or 'full_order'")
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the repeat command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result of repeating the item(s)
        """
        try:
            # Create order service
            order_service = OrderService(db)
            
            # Get current order items to resolve target reference
            order_result = await order_service.get_order(self.order_id)
            if not order_result.is_success:
                return OrderResult.error("Could not retrieve order to repeat items")
            
            order_items = order_result.data.get("order", {}).get("order_items", [])
            if not order_items:
                return OrderResult.error("No items in order to repeat")
            
            if self.scope == "full_order":
                # Repeat all items in the order
                repeated_count = 0
                for item in order_items:
                    result = await order_service.add_item_to_order(
                        order_id=self.order_id,
                        menu_item_id=item.menu_item_id,
                        quantity=item.quantity,
                        customizations=item.customizations or [],
                        special_instructions=item.special_instructions
                    )
                    if result.is_success:
                        repeated_count += 1
                
                return OrderResult.success(
                    f"Repeated entire order: {repeated_count} items added",
                    data={
                        "scope": self.scope,
                        "items_repeated": repeated_count,
                        "total_items": len(order_items)
                    }
                )
            
            else:
                # Repeat single item (last_item scope)
                resolved_item = TargetReference.resolve_target(self.target_ref, order_items)
                if not resolved_item:
                    return OrderResult.error(f"Could not resolve target reference: {self.target_ref}")
                
                # Add a copy of the resolved item
                result = await order_service.add_item_to_order(
                    order_id=self.order_id,
                    menu_item_id=resolved_item.menu_item_id,
                    quantity=resolved_item.quantity,
                    customizations=resolved_item.customizations or [],
                    special_instructions=resolved_item.special_instructions
                )
                
                if result.is_success:
                    menu_item_name = resolved_item.menu_item.name if resolved_item.menu_item else "item"
                    result.message = f"Added another {resolved_item.quantity}x {menu_item_name} to order"
                
                return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to repeat item: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "target_ref": self.target_ref,
            "scope": self.scope
        }
