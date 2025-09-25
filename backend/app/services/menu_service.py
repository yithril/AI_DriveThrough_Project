"""
Menu Service for accessing menu data
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.unit_of_work import UnitOfWork
from app.services.menu_cache_interface import MenuCacheInterface
import logging

logger = logging.getLogger(__name__)


class MenuService:
    """
    Service for accessing menu data across the application.
    Uses cache-first approach with database fallback.
    """
    
    def __init__(self, db: AsyncSession, cache_service: Optional[MenuCacheInterface] = None):
        """
        Initialize MenuService with database session and cache service
        
        Args:
            db: Database session
            cache_service: Menu cache service (optional)
        """
        self.db = db
        self.cache_service = cache_service
    
    async def get_available_items_for_restaurant(self, restaurant_id: int) -> List[str]:
        """
        Get all available menu item names for a restaurant.
        
        This method is designed for AI agents that need to suggest alternatives
        when items are not found. Returns just the item names for simplicity.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            List[str]: List of available menu item names
        """
        try:
            print(f"\n🔍 DEBUG - GET_AVAILABLE_ITEMS:")
            print(f"   Restaurant ID: {restaurant_id}")
            
            # Try cache first
            if self.cache_service:
                try:
                    available_items = await self.cache_service.get_available_items(restaurant_id)
                    if available_items:
                        print(f"   Available items from cache: {available_items}")
                        return available_items
                    print(f"   No cache found, falling back to database")
                except Exception as cache_error:
                    print(f"   Cache error: {cache_error}, falling back to database")
            
            # Fallback to database
            async with UnitOfWork(self.db) as uow:
                menu_items = await uow.menu_items.get_by_restaurant(restaurant_id)
                print(f"   Total menu items in DB: {len(menu_items)}")
                
                available_items = [item.name for item in menu_items if item.is_available]
                print(f"   Available items from DB: {available_items}")
                
                return available_items
        except Exception as e:
            print(f"   Error in get_available_items_for_restaurant: {str(e)}")
            # Log error but return empty list to prevent agent failures
            return []
    
    async def search_menu_items(self, restaurant_id: int, query: str) -> List[str]:
        """
        Search for menu items using flexible keyword matching.
        
        Args:
            restaurant_id: Restaurant ID
            query: Search query
            
        Returns:
            List of matching menu item names
        """
        try:
            # Try cache first
            if self.cache_service:
                try:
                    matching_items = await self.cache_service.search_menu_items(restaurant_id, query)
                    if matching_items:
                        return [item.name for item in matching_items]
                except Exception as cache_error:
                    logger.warning(f"Cache search failed: {cache_error}, falling back to database")
            
            # Fallback to database
            async with UnitOfWork(self.db) as uow:
                menu_items = await uow.menu_items.get_by_restaurant(restaurant_id)
                available_items = [item.name for item in menu_items if item.is_available]
                
                # Flexible keyword matching
                query_words = query.lower().split()
                matching_items = []
                
                for item in available_items:
                    item_lower = item.lower()
                    # Check if any query word is contained in the item name
                    if any(query_word in item_lower for query_word in query_words):
                        matching_items.append(item)
                
                return matching_items
        except Exception as e:
            # Log error but return empty list to prevent agent failures
            return []
    
    async def get_restaurant_name(self, restaurant_id: int) -> str:
        """
        Get restaurant name by ID.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            str: Restaurant name or "Restaurant" as fallback
        """
        try:
            async with UnitOfWork(self.db) as uow:
                restaurant = await uow.restaurants.get_by_id(restaurant_id)
                return restaurant.name if restaurant else "Restaurant"
        except Exception as e:
            return "Restaurant"
    
    async def get_menu_categories(self, restaurant_id: int) -> List[str]:
        """
        Get menu categories for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            List[str]: List of category names
        """
        try:
            async with UnitOfWork(self.db) as uow:
                categories = await uow.categories.get_by_restaurant(restaurant_id)
                return [category.name for category in categories if category.is_active]
        except Exception as e:
            return []
    
    async def get_menu_items_by_category(self, restaurant_id: int) -> Dict[str, List[str]]:
        """
        Get menu items organized by category.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping category names to item names
        """
        try:
            async with UnitOfWork(self.db) as uow:
                menu_items = await uow.menu_items.get_by_restaurant(restaurant_id)
                categories = await uow.categories.get_by_restaurant(restaurant_id)
                
                # Create category mapping
                category_map = {}
                for category in categories:
                    if category.is_active:
                        category_map[category.id] = category.name
                
                # Organize items by category
                items_by_category = {}
                for item in menu_items:
                    if item.is_available and item.category_id in category_map:
                        category_name = category_map[item.category_id]
                        if category_name not in items_by_category:
                            items_by_category[category_name] = []
                        items_by_category[category_name].append(item.name)
                
                return items_by_category
        except Exception as e:
            return {}
    
    async def get_menu_summary(self, restaurant_id: int) -> str:
        """
        Get a summary of the menu for AI agents.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            str: Summary of available menu items
        """
        try:
            items_by_category = await self.get_menu_items_by_category(restaurant_id)
            if not items_by_category:
                return "No menu items available"
            
            summary_parts = []
            for category, items in items_by_category.items():
                items_str = ', '.join(items[:5])  # Limit to 5 items per category
                if len(items) > 5:
                    items_str += f" and {len(items) - 5} more"
                summary_parts.append(f"{category}: {items_str}")
            
            return " | ".join(summary_parts)
        except Exception as e:
            return "Menu information unavailable"
    
    async def get_menu_item_ingredients(self, restaurant_id: int, menu_item_name: str) -> List[Dict[str, Any]]:
        """
        Get ingredients for a specific menu item.
        
        Args:
            restaurant_id: Restaurant ID
            menu_item_name: Name of the menu item
            
        Returns:
            List of ingredient dictionaries with name, quantity, unit, is_optional
        """
        try:
            async with UnitOfWork(self.db) as uow:
                # Find the menu item by name
                menu_items = await uow.menu_items.get_by_restaurant(restaurant_id)
                menu_item = None
                for item in menu_items:
                    if item.name.lower() == menu_item_name.lower():
                        menu_item = item
                        break
                
                if not menu_item:
                    return []
                
                # Get ingredients for this menu item
                ingredients = []
                for menu_item_ingredient in menu_item.ingredients:
                    ingredient = menu_item_ingredient.ingredient
                    ingredients.append({
                        "name": ingredient.name,
                        "quantity": float(menu_item_ingredient.quantity),
                        "unit": menu_item_ingredient.unit,
                        "is_optional": menu_item_ingredient.is_optional,
                        "additional_cost": float(menu_item_ingredient.additional_cost),
                        "is_allergen": ingredient.is_allergen,
                        "allergen_type": ingredient.allergen_type
                    })
                
                return ingredients
        except Exception as e:
            logger.error(f"Failed to get ingredients for menu item {menu_item_name}: {e}")
            return []
    
    async def get_all_ingredients_for_restaurant(self, restaurant_id: int) -> List[str]:
        """
        Get all ingredient names for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            List of ingredient names
        """
        try:
            async with UnitOfWork(self.db) as uow:
                ingredients = await uow.ingredients.get_by_restaurant(restaurant_id)
                return [ingredient.name for ingredient in ingredients]
        except Exception as e:
            logger.error(f"Failed to get ingredients for restaurant {restaurant_id}: {e}")
            return []
    
    async def get_all_ingredients_with_costs(self, restaurant_id: int) -> List[Dict[str, Any]]:
        """
        Get all available ingredients with their costs for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            List of ingredient dictionaries with name, unit_cost, allergen info
        """
        try:
            async with UnitOfWork(self.db) as uow:
                ingredients = await uow.ingredients.get_by_restaurant(restaurant_id)
                return [{
                    "name": ingredient.name,
                    "unit_cost": float(ingredient.unit_cost),
                    "is_allergen": ingredient.is_allergen,
                    "allergen_type": ingredient.allergen_type
                } for ingredient in ingredients]
        except Exception as e:
            logger.error(f"Failed to get ingredients with costs for restaurant {restaurant_id}: {e}")
            return []
