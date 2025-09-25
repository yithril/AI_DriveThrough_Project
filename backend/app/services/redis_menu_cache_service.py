"""
Redis Menu Cache Service

Redis implementation of menu caching for fast menu lookups
"""

import json
import logging
from typing import List, Dict, Any, Optional
import redis.asyncio as redis
from app.models.menu_item import MenuItem
from app.services.menu_cache_interface import MenuCacheInterface
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisMenuCacheService(MenuCacheInterface):
    """Redis implementation of menu caching"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_prefix = "menu:"
        self.available_items_prefix = "available:"
        self.search_index_prefix = "search:"
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client, create if not exists"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def _get_cache_key(self, restaurant_id: int, suffix: str = "") -> str:
        """Generate cache key for restaurant"""
        return f"{self.cache_prefix}{restaurant_id}{suffix}"
    
    async def _get_available_items_key(self, restaurant_id: int) -> str:
        """Generate cache key for available items"""
        return f"{self.available_items_prefix}{restaurant_id}"
    
    async def _get_search_index_key(self, restaurant_id: int) -> str:
        """Generate cache key for search index"""
        return f"{self.search_index_prefix}{restaurant_id}"
    
    async def get_menu_items(self, restaurant_id: int) -> List[MenuItem]:
        """Get all menu items for a restaurant from cache"""
        try:
            redis_client = await self._get_redis_client()
            cache_key = await self._get_cache_key(restaurant_id)
            
            cached_data = await redis_client.get(cache_key)
            if cached_data is None:
                logger.info(f"No cached menu items found for restaurant {restaurant_id}")
                return []
            
            menu_data = json.loads(cached_data)
            menu_items = [MenuItem(**item) for item in menu_data]
            
            logger.debug(f"Retrieved {len(menu_items)} menu items from cache for restaurant {restaurant_id}")
            return menu_items
            
        except Exception as e:
            logger.error(f"Error retrieving menu items from cache: {e}")
            return []
    
    async def get_menu_item_by_id(self, restaurant_id: int, menu_item_id: int) -> Optional[MenuItem]:
        """Get a specific menu item by ID from cache"""
        try:
            menu_items = await self.get_menu_items(restaurant_id)
            for item in menu_items:
                if item.id == menu_item_id:
                    return item
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving menu item {menu_item_id} from cache: {e}")
            return None
    
    async def search_menu_items(self, restaurant_id: int, query: str) -> List[MenuItem]:
        """Search menu items by name/description from cache"""
        try:
            menu_items = await self.get_menu_items(restaurant_id)
            if not menu_items:
                return []
            
            query_lower = query.lower()
            matching_items = []
            
            for item in menu_items:
                # Search in name and description
                if (query_lower in item.name.lower() or 
                    (item.description and query_lower in item.description.lower())):
                    matching_items.append(item)
            
            logger.debug(f"Found {len(matching_items)} matching items for query '{query}' in restaurant {restaurant_id}")
            return matching_items
            
        except Exception as e:
            logger.error(f"Error searching menu items in cache: {e}")
            return []
    
    async def get_available_items(self, restaurant_id: int) -> List[str]:
        """Get available menu item names from cache"""
        try:
            redis_client = await self._get_redis_client()
            available_key = await self._get_available_items_key(restaurant_id)
            
            cached_data = await redis_client.get(available_key)
            if cached_data is None:
                logger.info(f"No cached available items found for restaurant {restaurant_id}")
                return []
            
            available_items = json.loads(cached_data)
            logger.debug(f"Retrieved {len(available_items)} available items from cache for restaurant {restaurant_id}")
            return available_items
            
        except Exception as e:
            logger.error(f"Error retrieving available items from cache: {e}")
            return []
    
    async def cache_menu_items(self, restaurant_id: int, menu_items: List[MenuItem]) -> None:
        """Cache menu items for a restaurant"""
        try:
            redis_client = await self._get_redis_client()
            
            # Cache full menu items
            cache_key = await self._get_cache_key(restaurant_id)
            menu_data = [item.to_dict() for item in menu_items]
            await redis_client.setex(cache_key, 3600, json.dumps(menu_data))  # 1 hour TTL
            
            # Cache available items list
            available_items = [item.name for item in menu_items if item.is_available]
            available_key = await self._get_available_items_key(restaurant_id)
            await redis_client.setex(available_key, 3600, json.dumps(available_items))  # 1 hour TTL
            
            # Build search index for faster searching
            search_index = {}
            for item in menu_items:
                # Index by name words
                name_words = item.name.lower().split()
                for word in name_words:
                    if word not in search_index:
                        search_index[word] = []
                    search_index[word].append(item.id)
                
                # Index by description words if available
                if item.description:
                    desc_words = item.description.lower().split()
                    for word in desc_words:
                        if word not in search_index:
                            search_index[word] = []
                        search_index[word].append(item.id)
            
            search_key = await self._get_search_index_key(restaurant_id)
            await redis_client.setex(search_key, 3600, json.dumps(search_index))  # 1 hour TTL
            
            logger.info(f"Cached {len(menu_items)} menu items for restaurant {restaurant_id}")
            
        except Exception as e:
            logger.error(f"Error caching menu items: {e}")
            raise
    
    async def invalidate_restaurant_cache(self, restaurant_id: int) -> None:
        """Invalidate cache for a specific restaurant"""
        try:
            redis_client = await self._get_redis_client()
            
            # Delete all cache keys for this restaurant
            cache_key = await self._get_cache_key(restaurant_id)
            available_key = await self._get_available_items_key(restaurant_id)
            search_key = await self._get_search_index_key(restaurant_id)
            
            await redis_client.delete(cache_key, available_key, search_key)
            logger.info(f"Invalidated cache for restaurant {restaurant_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for restaurant {restaurant_id}: {e}")
    
    async def invalidate_all_cache(self) -> None:
        """Invalidate all menu cache"""
        try:
            redis_client = await self._get_redis_client()
            
            # Delete all menu-related keys
            pattern = f"{self.cache_prefix}*"
            available_pattern = f"{self.available_items_prefix}*"
            search_pattern = f"{self.search_index_prefix}*"
            
            # Get all matching keys and delete them
            for pattern in [pattern, available_pattern, search_pattern]:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            
            logger.info("Invalidated all menu cache")
            
        except Exception as e:
            logger.error(f"Error invalidating all cache: {e}")
    
    async def is_cache_available(self) -> bool:
        """Check if cache is available and working"""
        try:
            redis_client = await self._get_redis_client()
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache not available: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
