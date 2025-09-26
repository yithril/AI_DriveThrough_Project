"""
Service Locator for Dependency Injection

This module provides a service locator that creates services with their dependencies.
This allows us to create services on-demand with the correct database sessions,
similar to how .NET DI works with scoped services.
"""

from typing import Callable, Any, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

if TYPE_CHECKING:
    from app.core.container import Container


class ServiceFactory:
    """
    Service locator that creates services with their dependencies.
    
    This provides a clean way to create services on-demand with database sessions,
    similar to how .NET DI works with scoped services.
    """
    
    def __init__(self, container: "Container"):
        self.container = container
    
    # Database-dependent service factories
    def create_menu_service(self, db_session: AsyncSession):
        """Create MenuService with database session and cache service"""
        from app.services.menu_service import MenuService
        from app.services.redis_menu_cache_service import RedisMenuCacheService
        
        # Create cache service
        cache_service = RedisMenuCacheService()
        return MenuService(db_session, cache_service)
    
    def create_restaurant_service(self, db_session: AsyncSession):
        """Create RestaurantService with database session"""
        from app.services.restaurant_service import RestaurantService
        return RestaurantService(db_session)
    
    def create_order_service(self, db_session: AsyncSession):
        """Create OrderService with database session"""
        from app.services.order_service import OrderService
        from app.services.order_session_service import OrderSessionService
        from app.services.customization_validation_service import CustomizationValidationService
        
        # Create the required dependencies
        order_session_service = self.create_order_session_service()
        customization_validator = self.create_customization_validator(db_session)
        voice_service = self.create_voice_service()
        order_validator = self.create_order_validator()
        
        return OrderService(order_session_service, customization_validator, voice_service, order_validator)
    
    def create_customization_validator(self, db_session: AsyncSession):
        """Create CustomizationValidator with database session"""
        from app.services.customization_validation_service import CustomizationValidationService
        return CustomizationValidationService()
    
    def create_order_validator(self):
        """Create OrderValidator"""
        from app.services.order_validator import OrderValidator
        return OrderValidator()
    
    # Non-database services (can be created directly from container)
    def create_order_session_service(self):
        """Create OrderSessionService (uses Redis, no database)"""
        from app.services.order_session_service import OrderSessionService
        from app.services.redis_service import RedisService
        
        # Create Redis service directly
        redis_service = RedisService()
        return OrderSessionService(redis_service)
    
    def create_voice_service(self):
        """Create VoiceService (no database dependencies)"""
        from app.services.voice_service import VoiceService
        from app.services.text_to_speech_service import TextToSpeechService
        from app.services.speech_to_text_service import SpeechToTextService
        from app.services.file_storage_service import S3FileStorageService
        from app.services.redis_service import RedisService
        from app.core.config import settings
        
        # Create dependencies directly
        tts_provider = self.container.tts_provider()
        text_to_speech_service = TextToSpeechService(tts_provider)
        speech_to_text_service = self.container.speech_to_text_service()
        file_storage_service = S3FileStorageService(
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.S3_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL
        )
        redis_service = RedisService()
        
        return VoiceService(
            text_to_speech_service=text_to_speech_service,
            speech_to_text_service=speech_to_text_service,
            file_storage_service=file_storage_service,
            redis_service=redis_service
        )
    
    def create_redis_service(self):
        """Create RedisService (no database dependencies)"""
        return self.container.redis_service()
    
    def create_menu_cache_loader(self):
        """Create MenuCacheLoader with Redis cache service"""
        from app.services.menu_cache_loader import MenuCacheLoader
        from app.services.redis_menu_cache_service import RedisMenuCacheService
        
        cache_service = RedisMenuCacheService()
        return MenuCacheLoader(cache_service)


def create_service_factory(container: "Container") -> ServiceFactory:
    """
    Create a ServiceFactory instance with the given container.
    
    Args:
        container: Dependency injection container
        
    Returns:
        ServiceFactory instance
    """
    return ServiceFactory(container)
