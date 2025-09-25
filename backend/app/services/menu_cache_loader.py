"""
Menu Cache Loader Service

Loads menu data into cache on application startup
"""

import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.unit_of_work import UnitOfWork
from app.services.menu_cache_interface import MenuCacheInterface
from app.models.menu_item import MenuItem

logger = logging.getLogger(__name__)


class MenuCacheLoader:
    """Service to load menu data into cache on startup"""
    
    def __init__(self, cache_service: MenuCacheInterface):
        """
        Initialize menu cache loader
        
        Args:
            cache_service: Menu cache service implementation
        """
        self.cache_service = cache_service
    
    async def load_all_restaurants(self, db: AsyncSession) -> None:
        """
        Load menu data for all restaurants into cache
        
        Args:
            db: Database session
        """
        try:
            logger.info("Starting menu cache loading...")
            
            # Check if cache is available
            if not await self.cache_service.is_cache_available():
                logger.warning("Cache service not available, skipping menu cache loading")
                return
            
            # Get all restaurants
            async with UnitOfWork(db) as uow:
                restaurants = await uow.restaurants.get_all()
                logger.info(f"Found {len(restaurants)} restaurants to cache")
                
                for restaurant in restaurants:
                    await self._load_restaurant_menu(restaurant.id, db)
            
            logger.info("Menu cache loading completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to load menu cache: {e}")
            raise
    
    async def load_restaurant_menu(self, restaurant_id: int, db: AsyncSession) -> None:
        """
        Load menu data for a specific restaurant into cache
        
        Args:
            restaurant_id: Restaurant ID
            db: Database session
        """
        try:
            logger.info(f"Loading menu cache for restaurant {restaurant_id}")
            
            # Check if cache is available
            if not await self.cache_service.is_cache_available():
                logger.warning("Cache service not available, skipping menu cache loading")
                return
            
            await self._load_restaurant_menu(restaurant_id, db)
            logger.info(f"Menu cache loaded successfully for restaurant {restaurant_id}")
            
        except Exception as e:
            logger.error(f"Failed to load menu cache for restaurant {restaurant_id}: {e}")
            raise
    
    async def _load_restaurant_menu(self, restaurant_id: int, db: AsyncSession) -> None:
        """
        Internal method to load menu data for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            db: Database session
        """
        try:
            async with UnitOfWork(db) as uow:
                # Get all menu items for the restaurant
                menu_items = await uow.menu_items.get_by_restaurant(restaurant_id)
                
                if not menu_items:
                    logger.warning(f"No menu items found for restaurant {restaurant_id}")
                    return
                
                # Cache the menu items
                await self.cache_service.cache_menu_items(restaurant_id, menu_items)
                
                logger.info(f"Cached {len(menu_items)} menu items for restaurant {restaurant_id}")
                
        except Exception as e:
            logger.error(f"Failed to load menu items for restaurant {restaurant_id}: {e}")
            raise
    
    async def refresh_restaurant_cache(self, restaurant_id: int, db: AsyncSession) -> None:
        """
        Refresh menu cache for a specific restaurant
        
        Args:
            restaurant_id: Restaurant ID
            db: Database session
        """
        try:
            logger.info(f"Refreshing menu cache for restaurant {restaurant_id}")
            
            # Invalidate existing cache
            await self.cache_service.invalidate_restaurant_cache(restaurant_id)
            
            # Reload menu data
            await self.load_restaurant_menu(restaurant_id, db)
            
        except Exception as e:
            logger.error(f"Failed to refresh menu cache for restaurant {restaurant_id}: {e}")
            raise
    
    async def refresh_all_cache(self, db: AsyncSession) -> None:
        """
        Refresh menu cache for all restaurants
        
        Args:
            db: Database session
        """
        try:
            logger.info("Refreshing all menu cache")
            
            # Invalidate all cache
            await self.cache_service.invalidate_all_cache()
            
            # Reload all menu data
            await self.load_all_restaurants(db)
            
        except Exception as e:
            logger.error(f"Failed to refresh all menu cache: {e}")
            raise
