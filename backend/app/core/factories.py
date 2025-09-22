"""
Service Locator for Dependency Injection

This module provides a service locator that creates services with their dependencies.
This allows us to create services on-demand with the correct database sessions,
similar to how .NET DI works with scoped services.
"""

from typing import Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.container import Container


class ServiceFactory:
    """
    Service locator that creates services with their dependencies.
    
    This provides a clean way to create services on-demand with database sessions,
    similar to how .NET DI works with scoped services.
    """
    
    def __init__(self, container: Container):
        self.container = container
    
    # Database-dependent service factories
    def create_menu_service(self, db_session: AsyncSession):
        """Create MenuService with database session"""
        from app.services.menu_service import MenuService
        return MenuService(db_session)
    
    def create_restaurant_service(self, db_session: AsyncSession):
        """Create RestaurantService with database session"""
        from app.services.restaurant_service import RestaurantService
        return RestaurantService(db_session)
    
    def create_order_service(self, db_session: AsyncSession):
        """Create OrderService with database session"""
        from app.services.order_service import OrderService
        return OrderService(db_session)
    
    def create_customization_validator(self, db_session: AsyncSession):
        """Create CustomizationValidator with database session"""
        from app.services.customization_validator import CustomizationValidator
        return CustomizationValidator(db_session)
    
    # Non-database services (can be created directly from container)
    def create_order_session_service(self):
        """Create OrderSessionService (uses Redis, no database)"""
        return self.container.order_session_service()
    
    def create_voice_service(self):
        """Create VoiceService (no database dependencies)"""
        return self.container.voice_service()
    
    def create_redis_service(self):
        """Create RedisService (no database dependencies)"""
        return self.container.redis_service()


def create_service_factory(container: Container) -> ServiceFactory:
    """
    Create a ServiceFactory instance with the given container.
    
    Args:
        container: Dependency injection container
        
    Returns:
        ServiceFactory instance
    """
    return ServiceFactory(container)
