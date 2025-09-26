"""
Real End-to-End Workflow Test

This test uses:
- Real PostgreSQL database (localhost)
- Real Redis (localhost) 
- Real OpenAI API calls
- Real Text-to-Speech generation
- Local file storage (instead of S3)

The test starts with text input and runs through the full workflow.
"""

import pytest
import pytest_asyncio
import asyncio
import os
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from main import app
from app.core.container import Container
from app.core.database import get_db
from app.services.file_storage_service import LocalFileStorageService
from app.services.order_session_service import OrderSessionService
from app.services.redis_service import RedisService
from app.core.conversation_orchestrator import ConversationOrchestrator
from app.core.service_factory import ServiceFactory
from app.commands.intent_classification_schema import IntentType

# Define the path for local audio output
E2E_AUDIO_OUTPUT_DIR = "app/tests/end2end/audio_output"

@pytest.fixture(scope="session")
def setup_audio_output_dir():
    """Ensure the audio output directory exists"""
    os.makedirs(E2E_AUDIO_OUTPUT_DIR, exist_ok=True)
    return E2E_AUDIO_OUTPUT_DIR

@pytest.fixture(scope="session")
def local_file_storage_service(setup_audio_output_dir):
    """Use local file storage instead of S3"""
    return LocalFileStorageService(base_path=setup_audio_output_dir)

@pytest_asyncio.fixture(scope="function")
async def override_services(local_file_storage_service):
    """Override S3 with local file storage - function-scoped for per-test isolation"""
    container = Container()
    container.file_storage_service.override(local_file_storage_service)
    
    # Configure the container with settings
    from app.core.config import settings
    container.config.from_dict({
        "S3_BUCKET_NAME": settings.S3_BUCKET_NAME,
        "S3_REGION": settings.S3_REGION,
        "AWS_ENDPOINT_URL": settings.AWS_ENDPOINT_URL,
        "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
    })
    
    # Initialize resources (connects to Redis) - now in the function event loop
    # This is the critical fix: init_resources() now runs in the function loop
    container.init_resources()
    
    yield container
    container.file_storage_service.reset_override()

@pytest_asyncio.fixture(scope="function")
async def load_menu_cache(override_services):
    """Load menu cache on test startup - function-scoped for per-test isolation"""
    from app.core.startup import load_menu_cache_on_startup
    
    print("🔄 Loading menu cache for E2E test...")
    try:
        await load_menu_cache_on_startup()
        print("✅ Menu cache loaded successfully")
    except Exception as e:
        print(f"⚠️ Menu cache loading failed (continuing anyway): {e}")
        # Don't fail the test if cache loading fails

@pytest_asyncio.fixture(scope="function")
async def redis_client():
    """Create Redis client in the function event loop"""
    redis_service = RedisService()
    await redis_service.connect()
    yield redis_service
    await redis_service.disconnect()

@pytest_asyncio.fixture(scope="function")
async def order_session_service(redis_client):
    """Create order session service with Redis client from function loop"""
    return OrderSessionService(redis_service=redis_client)

@pytest_asyncio.fixture(scope="function")
async def fresh_session(order_session_service, override_services):
    """Create a fresh session and order for each test using OrderService.handle_new_car"""
    from app.core.database import get_db
    from app.services.order_service import OrderService
    from app.core.service_factory import ServiceFactory
    
    # Use the real container from the test (has all services configured)
    container = override_services
    service_factory = ServiceFactory(container)
    
    # Get database session and create both session and order
    async for db in get_db():
        order_service = service_factory.create_order_service(db)
        order_result = await order_service.handle_new_car(db, restaurant_id=1, customer_name=None)
        if not order_result.is_success:
            raise Exception(f"Failed to create session and order: {order_result.message}")
        
        # Extract session ID from the result
        session_data = order_result.data.get("session", {})
        session_id = session_data.get("id")
        if not session_id:
            raise Exception("No session ID returned from handle_new_car")
        
        return session_id

@pytest.mark.asyncio
async def test_real_workflow_add_item(
    fresh_session,
    override_services,
    setup_audio_output_dir,
    load_menu_cache
):
    """
    Test the real workflow end-to-end with:
    - Real database queries
    - Real Redis session management
    - Real OpenAI API calls
    - Real TTS generation
    - Local file storage
    """
    
    # Test input
    user_text = "I would like to add a Quantum Cheeseburger"
    session_id = fresh_session
    restaurant_id = 1

    print(f"\n🚀 Starting real E2E test...")
    print(f"📝 User input: '{user_text}'")
    print(f"🆔 Session ID: {session_id}")
    print(f"🏪 Restaurant ID: {restaurant_id}")
    
    print(f"📊 Creating orchestrator...")
    
    # Use the overridden services (local file storage instead of S3)
    if override_services:
        container = override_services
    else:
        # Fallback to creating container if no override
        container = Container()
        
        # Configure the container with settings
        from app.core.config import settings
        container.config.from_dict({
            "S3_BUCKET_NAME": settings.S3_BUCKET_NAME,
            "S3_REGION": settings.S3_REGION,
            "AWS_ENDPOINT_URL": settings.AWS_ENDPOINT_URL,
            "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
        })
        
        # Initialize resources (connects to Redis)
        container.init_resources()
    
    # Create service factory and orchestrator
    service_factory = ServiceFactory(container)
    orchestrator = ConversationOrchestrator(service_factory)
    
    print(f"🔄 Running orchestrator...")
    
    # Run the orchestrator with real services and real LLM calls
    try:
        final_state = await orchestrator.process_conversation_turn(
            user_input=user_text,
            session_id=session_id,
            restaurant_id=restaurant_id
        )
        
        print(f"✅ Orchestrator completed!")
        print(f"📝 Final response text: {final_state['response_text']}")
        print(f"🔊 Audio URL: {final_state['audio_url']}")
        print(f"🎯 Intent type: {final_state['intent_type']}")
        
        # Verify the workflow completed successfully
        assert final_state['response_text'] is not None, "No response text generated"
        assert final_state['audio_url'] is not None, "No audio URL generated"
        assert final_state['intent_type'] is not None, "No intent classified"
        
        # Verify the audio file was saved locally
        if final_state['audio_url']:
            # Use the full path from the audio URL
            audio_path = final_state['audio_url']
            assert os.path.exists(audio_path), f"Audio file not found at {audio_path}"
            print(f"🎵 Audio saved to: {audio_path}")
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            print(f"📏 Audio file size: {file_size} bytes")
            assert file_size > 0, "Audio file is empty"
        
            # Verify the intent was classified correctly
            assert final_state['intent_type'] == IntentType.ADD_ITEM, f"Expected ADD_ITEM intent, got {final_state['intent_type']}"
        
        # Verify the response mentions the item
        assert "Quantum Cheeseburger" in final_state['response_text'] or "added" in final_state['response_text'].lower(), \
            f"Response doesn't mention Quantum Cheeseburger or addition: {final_state['response_text']}"
        
        print(f"🎉 All assertions passed!")
        
    except Exception as e:
        print(f"❌ Orchestrator failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the test directly
    pytest.main([__file__, "-v", "-s"])
