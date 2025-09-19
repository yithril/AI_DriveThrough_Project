"""
MenuItemIngredient repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.menu_item_ingredient import MenuItemIngredient


class MenuItemIngredientRepository(BaseRepository[MenuItemIngredient]):
    """
    Repository for MenuItemIngredient model with menu item ingredient-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(MenuItemIngredient, db)
    
    async def get_by_menu_item_and_ingredient(self, menu_item_id: int, ingredient_id: int) -> Optional[MenuItemIngredient]:
        """
        Get menu item ingredient by menu item and ingredient IDs
        
        Args:
            menu_item_id: Menu item ID
            ingredient_id: Ingredient ID
            
        Returns:
            MenuItemIngredient or None: Menu item ingredient instance if found
        """
        result = await self.db.execute(
            select(MenuItemIngredient)
            .where(
                MenuItemIngredient.menu_item_id == menu_item_id,
                MenuItemIngredient.ingredient_id == ingredient_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_menu_item(self, menu_item_id: int, skip: int = 0, limit: int = 100) -> List[MenuItemIngredient]:
        """
        Get all ingredients for a menu item
        
        Args:
            menu_item_id: Menu item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItemIngredient]: List of ingredients for the menu item
        """
        return await self.get_all_by_filter({"menu_item_id": menu_item_id}, skip, limit)
    
    async def get_by_ingredient(self, ingredient_id: int, skip: int = 0, limit: int = 100) -> List[MenuItemIngredient]:
        """
        Get all menu items that use a specific ingredient
        
        Args:
            ingredient_id: Ingredient ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItemIngredient]: List of menu items using the ingredient
        """
        return await self.get_all_by_filter({"ingredient_id": ingredient_id}, skip, limit)
    
    async def get_required_ingredients(self, menu_item_id: int, skip: int = 0, limit: int = 100) -> List[MenuItemIngredient]:
        """
        Get all required (non-optional) ingredients for a menu item
        
        Args:
            menu_item_id: Menu item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItemIngredient]: List of required ingredients for the menu item
        """
        result = await self.db.execute(
            select(MenuItemIngredient)
            .where(
                MenuItemIngredient.menu_item_id == menu_item_id,
                MenuItemIngredient.is_optional == False
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_optional_ingredients(self, menu_item_id: int, skip: int = 0, limit: int = 100) -> List[MenuItemIngredient]:
        """
        Get all optional ingredients for a menu item
        
        Args:
            menu_item_id: Menu item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItemIngredient]: List of optional ingredients for the menu item
        """
        result = await self.db.execute(
            select(MenuItemIngredient)
            .where(
                MenuItemIngredient.menu_item_id == menu_item_id,
                MenuItemIngredient.is_optional == True
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_menu_item_ingredient_with_details(self, menu_item_ingredient_id: int) -> Optional[MenuItemIngredient]:
        """
        Get menu item ingredient with menu item and ingredient details loaded
        
        Args:
            menu_item_ingredient_id: Menu item ingredient ID
            
        Returns:
            MenuItemIngredient or None: Menu item ingredient with details if found
        """
        return await self.get_by_id_with_relations(menu_item_ingredient_id, ["menu_item", "ingredient"])
    
    async def get_ingredients_with_quantities(self, menu_item_id: int, skip: int = 0, limit: int = 100) -> List[MenuItemIngredient]:
        """
        Get all ingredients with quantities for a menu item
        
        Args:
            menu_item_id: Menu item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MenuItemIngredient]: List of ingredients with quantities for the menu item
        """
        result = await self.db.execute(
            select(MenuItemIngredient)
            .where(MenuItemIngredient.menu_item_id == menu_item_id)
            .order_by(MenuItemIngredient.is_optional, MenuItemIngredient.ingredient_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_by_menu_item(self, menu_item_id: int) -> int:
        """
        Count ingredients for a menu item
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            int: Number of ingredients for the menu item
        """
        return await self.count({"menu_item_id": menu_item_id})
    
    async def count_by_ingredient(self, ingredient_id: int) -> int:
        """
        Count menu items that use a specific ingredient
        
        Args:
            ingredient_id: Ingredient ID
            
        Returns:
            int: Number of menu items using the ingredient
        """
        return await self.count({"ingredient_id": ingredient_id})
    
    async def count_required_by_menu_item(self, menu_item_id: int) -> int:
        """
        Count required ingredients for a menu item
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            int: Number of required ingredients for the menu item
        """
        result = await self.db.execute(
            select(MenuItemIngredient.id)
            .where(
                MenuItemIngredient.menu_item_id == menu_item_id,
                MenuItemIngredient.is_optional == False
            )
        )
        return len(result.scalars().all())
    
    async def count_optional_by_menu_item(self, menu_item_id: int) -> int:
        """
        Count optional ingredients for a menu item
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            int: Number of optional ingredients for the menu item
        """
        result = await self.db.execute(
            select(MenuItemIngredient.id)
            .where(
                MenuItemIngredient.menu_item_id == menu_item_id,
                MenuItemIngredient.is_optional == True
            )
        )
        return len(result.scalars().all())
