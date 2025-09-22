"""
Restaurant Service for accessing restaurant information
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.unit_of_work import UnitOfWork
import logging

logger = logging.getLogger(__name__)


class RestaurantService:
    """
    Service for accessing restaurant information across the application.
    Uses UnitOfWork pattern for repository access.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize RestaurantService with database session
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_restaurant_info(self, restaurant_id: int) -> Dict[str, Any]:
        """
        Get restaurant information that exists in the database.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            Dict containing restaurant information
        """
        try:
            async with UnitOfWork(self.db) as uow:
                restaurant = await uow.restaurants.get_by_id(restaurant_id)
                if not restaurant:
                    return self._get_default_restaurant_info()
                
                return {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "description": restaurant.description,
                    "logo_url": restaurant.logo_url,
                    "primary_color": restaurant.primary_color,
                    "secondary_color": restaurant.secondary_color,
                    "address": restaurant.address,
                    "phone": restaurant.phone,
                    "hours": restaurant.hours,
                    "is_active": restaurant.is_active
                }
        except Exception as e:
            logger.error(f"Failed to get restaurant info for ID {restaurant_id}: {e}")
            return self._get_default_restaurant_info()
    
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
            logger.error(f"Failed to get restaurant name for ID {restaurant_id}: {e}")
            return "Restaurant"
    
    async def get_restaurant_hours(self, restaurant_id: int) -> str:
        """
        Get restaurant hours.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            str: Restaurant hours or default message
        """
        try:
            async with UnitOfWork(self.db) as uow:
                restaurant = await uow.restaurants.get_by_id(restaurant_id)
                return restaurant.hours if restaurant and restaurant.hours else "Hours not available"
        except Exception as e:
            logger.error(f"Failed to get restaurant hours for ID {restaurant_id}: {e}")
            return "Hours not available"
    
    async def get_restaurant_address(self, restaurant_id: int) -> str:
        """
        Get restaurant address.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            str: Restaurant address or default message
        """
        try:
            async with UnitOfWork(self.db) as uow:
                restaurant = await uow.restaurants.get_by_id(restaurant_id)
                return restaurant.address if restaurant and restaurant.address else "Address not available"
        except Exception as e:
            logger.error(f"Failed to get restaurant address for ID {restaurant_id}: {e}")
            return "Address not available"
    
    async def get_restaurant_phone(self, restaurant_id: int) -> str:
        """
        Get restaurant phone number.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            str: Restaurant phone or default message
        """
        try:
            async with UnitOfWork(self.db) as uow:
                restaurant = await uow.restaurants.get_by_id(restaurant_id)
                return restaurant.phone if restaurant and restaurant.phone else "Phone not available"
        except Exception as e:
            logger.error(f"Failed to get restaurant phone for ID {restaurant_id}: {e}")
            return "Phone not available"
    
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
            logger.error(f"Failed to get menu categories for restaurant {restaurant_id}: {e}")
            return []
    
    async def get_restaurant_summary(self, restaurant_id: int) -> str:
        """
        Get a summary of restaurant information for AI agents.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            str: Summary of restaurant information
        """
        try:
            info = await self.get_restaurant_info(restaurant_id)
            categories = await self.get_menu_categories(restaurant_id)
            
            summary_parts = [
                f"Restaurant: {info['name']}",
                f"Hours: {info['hours']}",
                f"Location: {info['location']}"
            ]
            
            if categories:
                summary_parts.append(f"Categories: {', '.join(categories)}")
            
            return " | ".join(summary_parts)
        except Exception as e:
            logger.error(f"Failed to get restaurant summary for ID {restaurant_id}: {e}")
            return "Restaurant information unavailable"
    
    def _get_default_restaurant_info(self) -> Dict[str, Any]:
        """Get default restaurant info when database lookup fails"""
        return {
            "id": 0,
            "name": "Restaurant",
            "description": "Local restaurant",
            "logo_url": None,
            "primary_color": "#FF6B35",
            "secondary_color": "#F7931E",
            "address": "Drive-thru location",
            "phone": "Call for details",
            "hours": "Open 24/7",
            "is_active": True
        }
