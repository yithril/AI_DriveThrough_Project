"""
CustomizationValidationService - Validates customizations and calculates extra costs
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.unit_of_work import UnitOfWork
from ..dto.order_result import OrderResult

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Types of validation operations"""
    REMOVE_INGREDIENT = "remove_ingredient"
    ADD_INGREDIENT = "add_ingredient"


@dataclass
class ValidationResult:
    """Result of a customization validation"""
    is_valid: bool
    message: str
    extra_cost: float = 0.0
    validation_type: Optional[ValidationType] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CustomizationValidationService:
    """
    Service for validating customizations and calculating extra costs
    
    Handles scenarios like:
    - "Hold the foie gras" → Validate ingredient exists in menu item
    - "Add mustard" → Validate ingredient available + calculate extra cost
    """
    
    def __init__(self):
        """Initialize the validation service"""
        pass
    
    async def validate_remove_ingredient(
        self, 
        menu_item_id: int, 
        ingredient_name: str, 
        restaurant_id: int,
        uow: UnitOfWork
    ) -> ValidationResult:
        """
        Validate removing an ingredient from a menu item
        
        Args:
            menu_item_id: ID of the menu item
            ingredient_name: Name of ingredient to remove
            restaurant_id: Restaurant ID for scoping
            uow: Unit of work for database access
            
        Returns:
            ValidationResult: Validation result with success/error info
        """
        try:
            logger.info(f"Validating removal of '{ingredient_name}' from menu item {menu_item_id}")
            
            # 1. Get all ingredients for this menu item
            menu_item_ingredients = await uow.menu_item_ingredients.get_by_menu_item(menu_item_id)
            
            # 2. Check if ingredient exists in the menu item
            ingredient_found = False
            for menu_ingredient in menu_item_ingredients:
                if menu_ingredient.ingredient and menu_ingredient.ingredient.name.lower() == ingredient_name.lower():
                    ingredient_found = True
                    break
            
            if not ingredient_found:
                # Get menu item name for better error message
                menu_item = await uow.menu_items.get_by_id(menu_item_id)
                menu_name = menu_item.name if menu_item else f"Menu item {menu_item_id}"
                
                return ValidationResult(
                    is_valid=False,
                    message=f"Cannot remove '{ingredient_name}' - it's not an ingredient in {menu_name}",
                    validation_type=ValidationType.REMOVE_INGREDIENT,
                    errors=[f"'{ingredient_name}' not found in {menu_name}"]
                )
            
            # 3. Success - ingredient can be removed
            logger.info(f"Successfully validated removal of '{ingredient_name}' from menu item {menu_item_id}")
            return ValidationResult(
                is_valid=True,
                message=f"Can remove '{ingredient_name}' from menu item",
                validation_type=ValidationType.REMOVE_INGREDIENT
            )
            
        except Exception as e:
            logger.error(f"Error validating ingredient removal: {str(e)}")
            return ValidationResult(
                is_valid=False,
                message=f"Error validating ingredient removal: {str(e)}",
                validation_type=ValidationType.REMOVE_INGREDIENT,
                errors=[str(e)]
            )
    
    async def validate_add_ingredient(
        self, 
        menu_item_id: int, 
        ingredient_name: str, 
        restaurant_id: int,
        uow: UnitOfWork
    ) -> ValidationResult:
        """
        Validate adding an ingredient to a menu item
        
        Args:
            menu_item_id: ID of the menu item
            ingredient_name: Name of ingredient to add
            restaurant_id: Restaurant ID for scoping
            uow: Unit of work for database access
            
        Returns:
            ValidationResult: Validation result with success/error info and extra cost
        """
        try:
            logger.info(f"Validating addition of '{ingredient_name}' to menu item {menu_item_id}")
            
            # 1. Check if ingredient exists in the restaurant
            ingredient = await uow.ingredients.get_by_name_and_restaurant(ingredient_name, restaurant_id)
            
            if not ingredient:
                return ValidationResult(
                    is_valid=False,
                    message=f"Cannot add '{ingredient_name}' - ingredient not available",
                    validation_type=ValidationType.ADD_INGREDIENT,
                    errors=[f"'{ingredient_name}' not found in restaurant inventory"]
                )
            
            # 2. Calculate extra cost for adding this ingredient
            extra_cost = await self.calculate_extra_cost(menu_item_id, ingredient_name, restaurant_id, uow)
            
            # 3. Success - ingredient can be added
            cost_message = f" (extra cost: ${extra_cost:.2f})" if extra_cost > 0 else " (no extra cost)"
            logger.info(f"Successfully validated addition of '{ingredient_name}' to menu item {menu_item_id}{cost_message}")
            
            return ValidationResult(
                is_valid=True,
                message=f"Can add '{ingredient_name}' to menu item{cost_message}",
                extra_cost=extra_cost,
                validation_type=ValidationType.ADD_INGREDIENT
            )
            
        except Exception as e:
            logger.error(f"Error validating ingredient addition: {str(e)}")
            return ValidationResult(
                is_valid=False,
                message=f"Error validating ingredient addition: {str(e)}",
                validation_type=ValidationType.ADD_INGREDIENT,
                errors=[str(e)]
            )
    
    async def calculate_extra_cost(
        self, 
        menu_item_id: int, 
        ingredient_name: str, 
        restaurant_id: int,
        uow: UnitOfWork
    ) -> float:
        """
        Calculate the extra cost for adding an ingredient to a menu item
        
        Args:
            menu_item_id: ID of the menu item
            ingredient_name: Name of ingredient to add
            restaurant_id: Restaurant ID for scoping
            uow: Unit of work for database access
            
        Returns:
            float: Extra cost for adding the ingredient
        """
        try:
            # 1. Get the ingredient to check its unit cost
            ingredient = await uow.ingredients.get_by_name_and_restaurant(ingredient_name, restaurant_id)
            if not ingredient:
                return 0.0
            
            # 2. Check if this ingredient is already in the menu item
            menu_item_ingredients = await uow.menu_item_ingredients.get_by_menu_item(menu_item_id)
            
            for menu_ingredient in menu_item_ingredients:
                if menu_ingredient.ingredient and menu_ingredient.ingredient.name.lower() == ingredient_name.lower():
                    # Ingredient already exists - return the additional_cost from MenuItemIngredient
                    return float(menu_ingredient.additional_cost) if menu_ingredient.additional_cost else 0.0
            
            # 3. Ingredient not in menu item - use the ingredient's unit_cost
            return float(ingredient.unit_cost) if ingredient.unit_cost else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating extra cost: {str(e)}")
            return 0.0
    
    async def validate_customizations(
        self, 
        menu_item_id: int, 
        customizations: List[str], 
        restaurant_id: int,
        uow: UnitOfWork
    ) -> Dict[str, ValidationResult]:
        """
        Validate a list of customizations for a menu item
        
        Args:
            menu_item_id: ID of the menu item
            customizations: List of customization strings (e.g., ["no onions", "extra cheese"])
            restaurant_id: Restaurant ID for scoping
            uow: Unit of work for database access
            
        Returns:
            Dict[str, ValidationResult]: Validation results for each customization
        """
        results = {}
        total_extra_cost = 0.0
        
        for customization in customizations:
            customization_lower = customization.lower().strip()
            
            if customization_lower.startswith("no "):
                # Remove ingredient
                ingredient_name = customization_lower[3:].strip()
                result = await self.validate_remove_ingredient(
                    menu_item_id, ingredient_name, restaurant_id, uow
                )
                results[customization] = result
                
            elif customization_lower.startswith("extra ") or customization_lower.startswith("add "):
                # Add ingredient
                if customization_lower.startswith("extra "):
                    ingredient_name = customization_lower[6:].strip()
                else:  # "add "
                    ingredient_name = customization_lower[4:].strip()
                
                result = await self.validate_add_ingredient(
                    menu_item_id, ingredient_name, restaurant_id, uow
                )
                results[customization] = result
                
                if result.is_valid:
                    total_extra_cost += result.extra_cost
                    
            else:
                # Generic customization - assume it's valid
                results[customization] = ValidationResult(
                    is_valid=True,
                    message=f"Customization '{customization}' accepted",
                    extra_cost=0.0
                )
        
        logger.info(f"Validated {len(customizations)} customizations, total extra cost: ${total_extra_cost:.2f}")
        return results

