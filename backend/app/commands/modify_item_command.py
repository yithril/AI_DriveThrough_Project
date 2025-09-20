"""
Modify item command for AI order operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from .target_reference import TargetReference
from ..dto.order_result import OrderResult


class ModifyItemCommand(BaseCommand):
    """
    Command to modify an existing order item
    Used by AI when customer wants to change item properties (size, modifiers, etc.)
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        target_ref: str,
        changes: List[Dict[str, Any]]
    ):
        """
        Initialize modify item command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to modify item in
            target_ref: Target reference to resolve (e.g., "last_item", "line_1")
            changes: List of changes to apply (e.g., [{"op": "set_size", "value": "large"}])
        """
        super().__init__(restaurant_id, order_id)
        self.target_ref = target_ref
        self.changes = changes
        
        if not self.changes:
            raise ValueError("Must provide at least one change")
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the modify item command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of modifying the item
        """
        try:
            # Get current order items to resolve target reference
            order_result = await context.order_service.get_order(db, context.get_order_id())
            if not order_result.is_success:
                return OrderResult.error("Could not retrieve order to resolve target reference")
            
            order_items = order_result.data.get("order", {}).get("order_items", [])
            if not order_items:
                return OrderResult.error("No items in order to modify")
            
            # Resolve target reference to order item
            resolved_item = TargetReference.resolve_target(self.target_ref, order_items)
            if not resolved_item:
                return OrderResult.error(f"Could not resolve target reference: {self.target_ref}")
            
            # Convert the old format changes to the new format
            changes_dict = {}
            for change in self.changes:
                op = change.get("op")
                value = change.get("value")
                
                if op == "set_quantity":
                    # Quantity changes should use the dedicated method
                    quantity_result = await context.order_service.update_order_item_quantity(
                        db=db,
                        order_id=context.get_order_id(),
                        order_item_id=resolved_item.id,
                        quantity=value
                    )
                    if not quantity_result.is_success:
                        return quantity_result
                    # Continue with other changes
                else:
                    # Map old format to new format
                    changes_dict[op] = value
            
            # Apply the remaining changes using the new modify method
            if changes_dict:
                result = await context.order_service.modify_order_item(
                    db=db,
                    order_id=context.get_order_id(),
                    order_item_id=resolved_item.id,
                    changes=changes_dict
                )
                
                if result.is_success:
                    # Enhance message for AI
                    result.message = f"Modified {self.target_ref}: {result.message}"
                
                return result
            else:
                # Only quantity change was made
                return OrderResult.success(f"Modified {self.target_ref}: quantity updated")
            
        except Exception as e:
            return OrderResult.error(f"Failed to modify item: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "target_ref": self.target_ref,
            "changes": self.changes
        }
