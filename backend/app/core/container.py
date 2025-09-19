"""
Dependency injection container for the application
"""

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for all services
    """
    
    wiring_config = containers.WiringConfiguration(modules=["app.api.sessions", "app.api.ai"])
    
    # Configuration
    config = providers.Configuration()
    
    # Database session will be provided by FastAPI DI directly to services
    
    # Core services (no dependencies) - using lazy imports
    speech_service = providers.Singleton("app.services.speech_service.SpeechService")
    llm_guard_service = providers.Singleton("app.services.llm_guard_service.LLMGuardService")
    order_intent_processor = providers.Singleton("app.services.ai_agent.OrderIntentProcessor")
    
    # Audio pipeline service (orchestrates other services)
    audio_pipeline_service = providers.Singleton(
        "app.services.audio_pipeline_service.AudioPipelineService",
        speech_service=speech_service,
        llm_guard_service=llm_guard_service,
        order_intent_processor=order_intent_processor,
        file_storage_service=file_storage_service,
        order_service=order_service
    )
    
    # Redis service with lifecycle management
    redis_service = providers.Singleton("app.services.redis_service.RedisService")
    
    # TTS services
    tts_provider = providers.Singleton(
        "app.services.tts_provider.OpenAITTSProvider",
        api_key=config.OPENAI_API_KEY
    )
    tts_service = providers.Singleton(
        "app.services.tts_service.TTSService",
        provider=tts_provider
    )
    
    # File storage service (depends on config)
    file_storage_service = providers.Singleton(
        "app.services.file_storage_service.FileStorageService",
        bucket_name=config.S3_BUCKET_NAME,
        region=config.S3_REGION,
        endpoint_url=config.AWS_ENDPOINT_URL
    )
    
    # Canned audio service (depends on file storage and TTS)
    canned_audio_service = providers.Singleton(
        "app.services.canned_audio_service.CannedAudioService",
        file_storage=file_storage_service,
        tts_service=tts_service
    )
    
    # Repositories will be created by services with the database session from FastAPI DI
    
    # Order service (only depends on Redis, gets session from API boundary)
    order_service = providers.Factory(
        "app.services.order_service.OrderService",
        redis_service=redis_service
    )

    def init_resources(self):
        """Initialize resources that need startup setup"""
        # Connect to Redis on startup
        redis = self.redis_service()
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(redis.connect())
    
    def shutdown_resources(self):
        """Clean up resources on shutdown"""
        # Disconnect from Redis on shutdown
        redis = self.redis_service()
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(redis.disconnect())


# Container instance will be created in main.py
# Configuration will be set there as well
