"""
Add item command for AI order operations
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult


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
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the add item command
        
        Args:
            context: Command context providing scoped services
            db: Database session
            
        Returns:
            OrderResult: Result of adding the item
        """
        try:
            # Add item to order using OrderService from context
            result = await context.order_service.add_item_to_order(
                db=db,
                order_id=context.get_order_id(),
                menu_item_id=self.menu_item_id,
                quantity=self.quantity,
                customizations=self.modifiers,  # Pass modifiers as customizations for now
                special_instructions=self.special_instructions,
                size=self.size  # Pass size to OrderService for message generation
            )
            
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
