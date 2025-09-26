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
    
    async def search_menu_items(self, restaurant_id: int, query: str) -> List[Any]:
        """
        Search for menu items using flexible keyword matching.
        
        Args:
            restaurant_id: Restaurant ID
            query: Search query
            
        Returns:
            List of matching MenuItem objects
        """
        try:
            print(f"\n🔍 DEBUG - SEARCH_MENU_ITEMS:")
            print(f"   Query: '{query}'")
            print(f"   Restaurant ID: {restaurant_id}")
            
            # Try cache first, then fall back to database
            if self.cache_service:
                try:
                    # Try to get cached menu items (async)
                    cached_items = await self.cache_service.get_menu_items(restaurant_id)
                    if cached_items:
                        print(f"   Cache has {len(cached_items)} items")
                        
                        # Normalize query
                        normalized_query = self._normalize_query(query)
                        print(f"   Normalized query: '{normalized_query}'")
                        
                        # Try exact match first
                        exact_matches = []
                        for item in cached_items:
                            if self._normalize_query(item.name) == normalized_query:
                                exact_matches.append(item)
                                print(f"   ✅ EXACT MATCH: '{item.name}'")
                        
                        if exact_matches:
                            print(f"   Found {len(exact_matches)} exact matches")
                            return exact_matches
                        
                        # Fall back to keyword matching
                        query_words = self._extract_keywords(normalized_query)
                        print(f"   Query keywords: {query_words}")
                        matching_items = []
                        
                        for item in cached_items:
                            item_normalized = self._normalize_query(item.name)
                            item_keywords = self._extract_keywords(item_normalized)
                            print(f"   Checking item: '{item.name}' (keywords: {item_keywords})")
                            
                            # Check if any query keyword matches any item keyword (partial matching)
                            matches = []
                            for query_word in query_words:
                                # Check if query word is contained in any item keyword
                                item_matches = [query_word in item_keyword for item_keyword in item_keywords]
                                matches.append(any(item_matches))
                            print(f"   Keyword matches: {matches}")
                            if any(matches):
                                matching_items.append(item)
                                print(f"   ✅ KEYWORD MATCH: '{item.name}'")
                            else:
                                print(f"   ❌ NO MATCH: '{item.name}'")
                        
                        print(f"   Final matching items: {[item.name for item in matching_items]}")
                        return matching_items
                    else:
                        print(f"   No cached items found - falling back to database")
                        return await self._search_database(restaurant_id, query)
                except Exception as cache_error:
                    print(f"   Cache error: {cache_error}")
                    logger.warning(f"Cache search failed: {cache_error}")
                    return await self._search_database(restaurant_id, query)
            else:
                print(f"   No cache service available - falling back to database")
                return await self._search_database(restaurant_id, query)
                
        except Exception as e:
            print(f"   Error in search_menu_items: {str(e)}")
            # Log error but return empty list to prevent agent failures
            return []
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text for better matching.
        
        Args:
            query: Input query string
            
        Returns:
            Normalized query string
        """
        import re
        import unicodedata
        
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove accents and normalize Unicode
        normalized = unicodedata.normalize('NFKC', normalized)
        
        # Remove punctuation except spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Collapse multiple spaces into single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip leading/trailing whitespace
        return normalized.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text, removing stopwords.
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Common stopwords to remove
        STOPWORDS = {
            'the', 'a', 'an', 'and', 'or', 'but', 'please', 'i', 'would', 'like', 'to', 'add',
            'get', 'want', 'need', 'have', 'can', 'could', 'will', 'shall', 'may', 'might',
            'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'do', 'does', 'did', 'done',
            'meal', 'combo', 'with', 'without', 'extra', 'no', 'yes', 'some', 'any', 'all'
        }
        
        # Split into words and filter out stopwords (case insensitive)
        words = text.split()
        keywords = [word.lower() for word in words if word.lower() not in STOPWORDS and len(word) > 1]
        
        return keywords
    
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
    
    async def _search_database(self, restaurant_id: int, query: str) -> List[Any]:
        """
        Search database directly when cache is not available.
        
        Args:
            restaurant_id: Restaurant ID
            query: Search query
            
        Returns:
            List of matching MenuItem objects
        """
        try:
            print(f"   🔄 Searching database directly...")
            print(f"   Database session: {self.db}")
            
            # Get all menu items from database
            from app.repository.menu_item_repository import MenuItemRepository
            menu_item_repo = MenuItemRepository(self.db)
            print(f"   Repository created: {menu_item_repo}")
            
            # Get all menu items for the restaurant
            menu_items = await menu_item_repo.get_by_restaurant(restaurant_id)
            print(f"   Database has {len(menu_items)} items")
            
            if not menu_items:
                return []
            
            # Normalize query
            normalized_query = self._normalize_query(query)
            print(f"   Normalized query: '{normalized_query}'")
            
            # Try exact match first
            exact_matches = []
            for item in menu_items:
                if self._normalize_query(item.name) == normalized_query:
                    exact_matches.append(item)
                    print(f"   ✅ EXACT MATCH: '{item.name}'")
            
            if exact_matches:
                print(f"   Found {len(exact_matches)} exact matches")
                return exact_matches
            
            # Fall back to keyword matching
            query_words = self._extract_keywords(normalized_query)
            print(f"   Query keywords: {query_words}")
            matching_items = []
            
            for item in menu_items:
                item_normalized = self._normalize_query(item.name)
                item_keywords = self._extract_keywords(item_normalized)
                print(f"   Checking item: '{item.name}' (keywords: {item_keywords})")
                
                # Check if any query keyword matches any item keyword (partial matching)
                matches = []
                for query_word in query_words:
                    # Check if query word is contained in any item keyword
                    item_matches = [query_word in item_keyword for item_keyword in item_keywords]
                    matches.append(any(item_matches))
                print(f"   Keyword matches: {matches}")
                if any(matches):
                    matching_items.append(item)
                    print(f"   ✅ KEYWORD MATCH: '{item.name}'")
                else:
                    print(f"   ❌ NO MATCH: '{item.name}'")
            
            print(f"   Final matching items: {[item.name for item in matching_items]}")
            return matching_items
            
        except Exception as e:
            print(f"   Database search error: {str(e)}")
            logger.error(f"Database search failed: {e}")
            return []
    
    async def get_menu_item_by_name(self, restaurant_id: int, item_name: str):
        """
        Get a menu item by name for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID
            item_name: Menu item name
            
        Returns:
            MenuItem object or None if not found
        """
        try:
            from app.repository.menu_item_repository import MenuItemRepository
            menu_item_repo = MenuItemRepository(self.db)
            
            # Get all menu items for the restaurant
            menu_items = await menu_item_repo.get_by_restaurant(restaurant_id)
            
            # Find the item by name (case-insensitive)
            for item in menu_items:
                if self._normalize_query(item.name) == self._normalize_query(item_name):
                    return item
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get menu item by name: {e}")
            return None
