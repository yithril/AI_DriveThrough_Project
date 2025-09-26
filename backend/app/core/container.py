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
    speech_to_text_service = providers.Singleton("app.services.speech_to_text_service.SpeechToTextService")
    validation_service = providers.Singleton("app.services.lightweight_validation_service.LightweightValidationService")
    
    # Redis service with lifecycle management
    redis_service = providers.Singleton("app.services.redis_service.RedisService")
    
    # TTS services
    tts_provider = providers.Singleton(
        "app.services.tts_provider.OpenAITTSProvider",
        api_key=config.OPENAI_API_KEY
    )
    text_to_speech_service = providers.Singleton(
        "app.services.text_to_speech_service.TextToSpeechService",
        provider=tts_provider
    )
    
    # File storage service (depends on settings)
    file_storage_service = providers.Singleton(
        "app.services.file_storage_service.S3FileStorageService",
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.S3_REGION,
        endpoint_url=settings.AWS_ENDPOINT_URL
    )
    
    # Order session service (Redis primary with PostgreSQL fallback)
    order_session_service = providers.Singleton(
        "app.services.order_session_service.OrderSessionService",
        redis_service=redis_service
    )
    
    # Customization validation service
    customization_validator = providers.Singleton(
        "app.services.customization_validation_service.CustomizationValidationService"
    )
    
    # Order validation service
    order_validator = providers.Singleton(
        "app.services.order_validator.OrderValidator"
    )
    
    # Voice service (unified service for all voice operations)
    voice_service = providers.Singleton(
        "app.services.voice_service.VoiceService",
        text_to_speech_service=text_to_speech_service,
        speech_to_text_service=speech_to_text_service,
        file_storage_service=file_storage_service,
        redis_service=redis_service
    )
    
    # Order service (depends on OrderSessionService, CustomizationValidator, and VoiceService)
    order_service = providers.Factory(
        "app.services.order_service.OrderService",
        order_session_service=order_session_service,
        customization_validator=customization_validator,
        voice_service=voice_service,
        order_validator=order_validator
    )
    
    # Service factory (for creating services with database sessions)
    service_factory = providers.Singleton(
        "app.core.service_factory.ServiceFactory",
        container=providers.Self()
    )
    
    # Menu service (needs database session, created per request)
    menu_service = providers.Factory("app.services.menu_service.MenuService")
    
    # Conversation services
    intent_classification_service = providers.Singleton(
        "app.core.services.conversation.intent_classification_service.IntentClassificationService"
    )
    
    state_transition_service = providers.Singleton(
        "app.core.services.conversation.state_transition_service.StateTransitionService",
        order_session_service=order_session_service
    )
    
    intent_parser_router_service = providers.Singleton(
        "app.core.services.conversation.intent_parser_router_service.IntentParserRouterService"
    )
    
    command_executor_service = providers.Singleton(
        "app.core.services.conversation.command_executor_service.CommandExecutorService",
        order_service=order_service
    )
    
    response_aggregator_service = providers.Singleton(
        "app.core.services.conversation.response_aggregator_service.ResponseAggregatorService"
    )
    
    voice_generation_service = providers.Singleton(
        "app.core.services.conversation.voice_generation_service.VoiceGenerationService",
        voice_service=voice_service
    )
    
    # Conversation orchestrator (replaces LangGraph workflow)
    conversation_orchestrator = providers.Singleton(
        "app.core.conversation_orchestrator.ConversationOrchestrator",
        intent_classification_service=intent_classification_service,
        state_transition_service=state_transition_service,
        intent_parser_router_service=intent_parser_router_service,
        command_executor_service=command_executor_service,
        response_aggregator_service=response_aggregator_service,
        voice_generation_service=voice_generation_service
    )
    
    # Audio pipeline service (orchestrates other services)
    audio_pipeline_service = providers.Singleton(
        "app.services.audio_pipeline_service.AudioPipelineService",
        voice_service=voice_service,
        validation_service=validation_service,
        order_session_service=order_session_service,
        conversation_orchestrator=conversation_orchestrator
    )
    
    # Import services (these need database sessions, so they're created per request)
    excel_import_service = providers.Factory("app.services.excel_import_service.ExcelImportService")
    restaurant_import_service = providers.Factory("app.services.restaurant_import_service.RestaurantImportService")
    
    # Restaurant service (needs database session, created per request)
    restaurant_service = providers.Factory("app.services.restaurant_service.RestaurantService")

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
