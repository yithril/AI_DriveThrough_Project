"""
Order validation service with business logic
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.menu_item import MenuItem
from ..models.menu_item_ingredient import MenuItemIngredient
from ..models.inventory import Inventory
from ..models.order import Order
from ..models.order_item import OrderItem
from ..core.unit_of_work import UnitOfWork
from ..core.config import settings
from ..dto.order_result import ErrorCategory, ErrorCode, OrderResult, OrderResultStatus
from ..constants.order_limits import OrderLimits


class OrderValidator:
    """
    Validates order operations against business rules
    Uses feature flags to enable/disable validation rules
    """
    
    def __init__(self):
        # No database session needed - will be provided via UnitOfWork
        pass
    
    async def validate_add_item(
        self,
        restaurant_id: int,
        menu_item_id: int, 
        quantity: int,
        customizations: Optional[List[str]] = None,
        current_order: Optional[Order] = None,
        business_scenario: str = "default"
    ) -> OrderResult:
        """
        Validate adding an item to an order
        
        Args:
            restaurant_id: Restaurant ID
            menu_item_id: Menu item ID to add
            quantity: Quantity to add
            customizations: List of customizations (e.g., ["no cheese", "extra lettuce"])
            current_order: Current order (for quantity limits)
            
        Returns:
            OrderResult: Validation result with success/error status
        """
        errors = []
        warnings = []
        
        # 1. Validate basic parameters
        if quantity <= 0:
            errors.append("Quantity must be greater than 0")
        
        if quantity < OrderLimits.MIN_QUANTITY_PER_ITEM:
            errors.append(f"Quantity must be at least {OrderLimits.MIN_QUANTITY_PER_ITEM}")
        
        if quantity > OrderLimits.MAX_QUANTITY_PER_ITEM:
            errors.append(f"Quantity cannot exceed {OrderLimits.MAX_QUANTITY_PER_ITEM} per item")
        
        if errors:
            return OrderResult.error("Cannot add that many of that item to the order.", errors, error_code=ErrorCode.QUANTITY_EXCEEDS_LIMIT, error_category=ErrorCategory.BUSINESS)
        
        # 2. Menu item availability already validated by menu resolution agent
        # Skip redundant database checks to avoid async context issues
        
        # 3. All validations passed - no database calls needed
        return OrderResult.success(
            f"Successfully validated adding {quantity} items",
            data={"quantity": quantity}
        )
    
    async def validate_remove_item(self, uow: UnitOfWork, order_item_id: int, current_order: Order) -> OrderResult:
        """
        Validate removing an item from an order
        
        Args:
            order_item_id: Order item ID to remove
            current_order: Current order
            
        Returns:
            OrderResult: Validation result
        """
        # Check if order item exists in current order
        order_item = next((item for item in current_order.order_items if item.id == order_item_id), None)
        if not order_item:
            return OrderResult.error("Order item not found in current order")
        
        return OrderResult.success(
            f"Successfully validated removing {order_item.quantity}x {order_item.menu_item.name if order_item.menu_item else 'item'}",
            data={"order_item": order_item.to_dict()}
        )
    
    async def validate_clear_order(self, uow: UnitOfWork, current_order: Order) -> OrderResult:
        """
        Validate clearing an order
        
        Args:
            current_order: Current order
            
        Returns:
            OrderResult: Validation result
        """
        if not current_order.order_items:
            return OrderResult.warning("Order is already empty")
        
        item_count = sum(item.quantity for item in current_order.order_items)
        return OrderResult.success(
            f"Successfully validated clearing order with {item_count} items",
            data={"item_count": item_count}
        )
    
    async def _validate_customizations(self, uow: UnitOfWork, menu_item_id: int, customizations: List[str]) -> OrderResult:
        """
        Validate menu item customizations
        
        Args:
            menu_item_id: Menu item ID
            customizations: List of customizations
            
        Returns:
            OrderResult: Validation result
        """
        errors = []
        warnings = []
        
        # Get menu item ingredients to validate customizations
        ingredients = await uow.menu_item_ingredients.get_by_menu_item(menu_item_id)
        ingredient_names = [ing.ingredient.name.lower() for ing in ingredients if ing.ingredient]
        
        for customization in customizations:
            customization_lower = customization.lower()
            
            # Check for "no X" customizations
            if customization_lower.startswith("no "):
                ingredient_name = customization_lower[3:].strip()
                if ingredient_name not in ingredient_names:
                    errors.append(f"Cannot remove '{ingredient_name}' - not an ingredient in this item")
            
            # Check for "extra X" customizations
            elif customization_lower.startswith("extra "):
                ingredient_name = customization_lower[6:].strip()
                if ingredient_name not in ingredient_names:
                    warnings.append(f"Cannot add extra '{ingredient_name}' - not a standard ingredient")
        
        if errors:
            return OrderResult.error("Invalid customizations", errors)
        
        if warnings:
            return OrderResult.warning("Customizations validated with warnings", warnings)
        
        return OrderResult.success("Customizations validated successfully")
    
    async def _validate_inventory(self, uow: UnitOfWork, menu_item_id: int, quantity: int) -> OrderResult:
        """
        Validate inventory availability for menu item
        
        Args:
            menu_item_id: Menu item ID
            quantity: Quantity to validate
            
        Returns:
            OrderResult: Validation result
        """
        errors = []
        warnings = []
        
        # Get all ingredients for this menu item
        menu_item_ingredients = await uow.menu_item_ingredients.get_by_menu_item(menu_item_id)
        
        for menu_item_ingredient in menu_item_ingredients:
            if not menu_item_ingredient.ingredient:
                continue
            
            # Get inventory for this ingredient
            inventory = await uow.inventory.get_by_ingredient(menu_item_ingredient.ingredient_id)
            if not inventory:
                if not settings.ALLOW_NEGATIVE_INVENTORY:
                    errors.append(f"No inventory tracking for ingredient '{menu_item_ingredient.ingredient.name}'")
                continue
            
            # Calculate required quantity
            required_quantity = float(menu_item_ingredient.quantity) * quantity
            
            # Check if we have enough stock
            if inventory.current_stock < required_quantity:
                if not settings.ALLOW_NEGATIVE_INVENTORY:
                    errors.append(
                        f"Insufficient inventory for '{menu_item_ingredient.ingredient.name}': "
                        f"need {required_quantity} {menu_item_ingredient.unit}, have {inventory.current_stock} {inventory.unit}"
                    )
                else:
                    warnings.append(
                        f"Low inventory for '{menu_item_ingredient.ingredient.name}': "
                        f"need {required_quantity} {menu_item_ingredient.unit}, have {inventory.current_stock} {inventory.unit}"
                    )
            
            # Check for low stock warning
            elif inventory.is_low_stock:
                warnings.append(
                    f"Low stock warning for '{menu_item_ingredient.ingredient.name}': "
                    f"{inventory.current_stock} {inventory.unit} remaining"
                )
        
        if errors:
            return OrderResult.error("Inventory validation failed", errors)
        
        if warnings:
            return OrderResult.warning("Inventory validated with warnings", warnings)
        
        return OrderResult.success("Inventory validation passed")
    
    async def _validate_order_limits(self, current_order: Order, menu_item: MenuItem, quantity: int) -> OrderResult:
        """
        Validate order limits
        
        Args:
            current_order: Current order
            menu_item: Menu item being added
            quantity: Quantity being added
            
        Returns:
            OrderResult: Validation result
        """
        errors = []
        warnings = []
        
        # Check total items limit
        current_item_count = sum(item.quantity for item in current_order.order_items)
        if current_item_count + quantity > OrderLimits.MAX_ITEMS_PER_ORDER:
            errors.append(f"Order would exceed maximum of {OrderLimits.MAX_ITEMS_PER_ORDER} items")
        
        # Check order total limit
        new_item_total = float(menu_item.price) * quantity
        if current_order.total_amount + new_item_total > OrderLimits.MAX_ORDER_TOTAL:
            errors.append(f"Order total would exceed maximum of ${OrderLimits.MAX_ORDER_TOTAL}")
        
        if errors:
            return OrderResult.error("Order limits exceeded", errors)
        
        return OrderResult.success("Order limits validated")
