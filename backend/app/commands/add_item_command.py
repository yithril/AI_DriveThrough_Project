"""
Add item command for AI order operations
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService


# These will be validated against the actual menu item's allowed modifiers and sizes
# No hardcoded validation - let the menu item definition determine what's valid


class AddItemCommand(BaseCommand):
    """
    Command to add an item to an order
    Used by AI when customer wants to add menu items
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        menu_item_id: int,
        quantity: int = 1,
        size: Optional[str] = None,
        modifiers: Optional[List[str]] = None,
        special_instructions: Optional[str] = None
    ):
        """
        Initialize add item command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID to add item to
            menu_item_id: Menu item ID to add
            quantity: Quantity to add (default: 1)
            size: Item size - optional (depends on menu item's available sizes)
            modifiers: List of modifiers - optional (depends on menu item's available modifiers)
            special_instructions: Special instructions for the item
        """
        super().__init__(restaurant_id, order_id)
        self.menu_item_id = menu_item_id
        self.quantity = quantity
        self.size = size
        self.modifiers = modifiers or []
        self.special_instructions = special_instructions
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the add item command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result of adding the item
        """
        try:
            # Create order service
            order_service = OrderService(db)
            
            # Add item to order
            result = await order_service.add_item_to_order(
                order_id=self.order_id,
                menu_item_id=self.menu_item_id,
                quantity=self.quantity,
                customizations=self.modifiers,  # Pass modifiers as customizations for now
                special_instructions=self.special_instructions
            )
            
            # Enhance message for AI
            if result.is_success:
                menu_item_name = result.data.get("order_item", {}).get("menu_item", {}).get("name", "item")
                size_info = f" {self.size}" if self.size else ""
                modifiers_info = f" ({', '.join(self.modifiers)})" if self.modifiers else ""
                result.message = f"Added {self.quantity}x {menu_item_name}{size_info}{modifiers_info} to order"
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Failed to add item to order: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "size": self.size,
            "modifiers": self.modifiers,
            "special_instructions": self.special_instructions
        }
