"""
Ingredient repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.ingredient import Ingredient


class IngredientRepository(BaseRepository[Ingredient]):
    """
    Repository for Ingredient model with ingredient-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Ingredient, db)
    
    async def get_by_name_and_restaurant(self, name: str, restaurant_id: int) -> Optional[Ingredient]:
        """
        Get ingredient by name and restaurant
        
        Args:
            name: Ingredient name
            restaurant_id: Restaurant ID
            
        Returns:
            Ingredient or None: Ingredient instance if found
        """
        result = await self.db.execute(
            select(Ingredient)
            .where(Ingredient.name == name, Ingredient.restaurant_id == restaurant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Ingredient]:
        """
        Get all ingredients for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Ingredient]: List of ingredients for the restaurant
        """
        return await self.get_all_by_filter({"restaurant_id": restaurant_id}, skip, limit)
    
    async def get_allergens_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Ingredient]:
        """
        Get all allergen ingredients for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Ingredient]: List of allergen ingredients for the restaurant
        """
        result = await self.db.execute(
            select(Ingredient)
            .where(
                Ingredient.restaurant_id == restaurant_id,
                Ingredient.is_allergen == True
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_allergen_type(self, restaurant_id: int, allergen_type: str, skip: int = 0, limit: int = 100) -> List[Ingredient]:
        """
        Get ingredients by allergen type for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            allergen_type: Type of allergen (nuts, dairy, gluten, etc.)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Ingredient]: List of ingredients with specified allergen type
        """
        result = await self.db.execute(
            select(Ingredient)
            .where(
                Ingredient.restaurant_id == restaurant_id,
                Ingredient.allergen_type == allergen_type
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_ingredients(self, restaurant_id: int, search_term: str, skip: int = 0, limit: int = 100) -> List[Ingredient]:
        """
        Search ingredients by name or description within a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Ingredient]: List of matching ingredients
        """
        result = await self.db.execute(
            select(Ingredient)
            .where(
                Ingredient.restaurant_id == restaurant_id,
                Ingredient.name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_ingredient_with_menu_items(self, ingredient_id: int) -> Optional[Ingredient]:
        """
        Get ingredient with its associated menu items loaded
        
        Args:
            ingredient_id: Ingredient ID
            
        Returns:
            Ingredient or None: Ingredient with menu items if found
        """
        return await self.get_by_id_with_relations(ingredient_id, ["menu_item_ingredients"])
    
    async def count_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count ingredients for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of ingredients for the restaurant
        """
        return await self.count({"restaurant_id": restaurant_id})
    
    async def count_allergens_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count allergen ingredients for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of allergen ingredients for the restaurant
        """
        result = await self.db.execute(
            select(Ingredient.id)
            .where(
                Ingredient.restaurant_id == restaurant_id,
                Ingredient.is_allergen == True
            )
        )
        return len(result.scalars().all())
