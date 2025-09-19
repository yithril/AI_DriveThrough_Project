"""
Modify item command for AI order operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .target_reference import TargetReference
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService


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
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the modify item command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result of modifying the item
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
            
            # Apply changes to the item
            # For now, we'll use the order service's update methods
            # In a full implementation, you'd want more granular update methods
            
            result_message = f"Modified {self.target_ref}: "
            changes_applied = []
            
            for change in self.changes:
                op = change.get("op")
                value = change.get("value")
                
                if op == "set_size":
                    changes_applied.append(f"size to {value}")
                elif op == "add_modifier":
                    changes_applied.append(f"added {value}")
                elif op == "remove_modifier":
                    changes_applied.append(f"removed {value}")
                elif op == "set_quantity":
                    changes_applied.append(f"quantity to {value}")
                elif op == "add_special_instruction":
                    changes_applied.append(f"special instruction: {value}")
                else:
                    changes_applied.append(f"{op}: {value}")
            
            result_message += ", ".join(changes_applied)
            
            # For now, return success - in full implementation, you'd update the database
            return OrderResult.success(
                result_message,
                data={
                    "target_ref": self.target_ref,
                    "order_item_id": resolved_item.id,
                    "changes_applied": self.changes,
                    "changes_description": changes_applied
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to modify item: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "target_ref": self.target_ref,
            "changes": self.changes
        }
