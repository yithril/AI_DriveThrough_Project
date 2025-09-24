"""
Multi-Item Order End-to-End Test

This test verifies that the system can handle multiple items in a single order:
- Checks order state before and after
- Processes: "I want a quantum burger a nebula wrap and a lunar lemonade please"
- Verifies all items are added to the order
"""

import pytest
import pytest_asyncio
import asyncio
import os
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.container import Container
from app.core.database import get_db
from app.services.file_storage_service import LocalFileStorageService
from app.services.order_session_service import OrderSessionService
from app.services.redis_service import RedisService
from app.agents.workflow import create_conversation_workflow
from app.agents.state import ConversationWorkflowState
from app.commands.intent_classification_schema import IntentType
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem
from sqlalchemy import select

# Define the path for local audio output
E2E_AUDIO_OUTPUT_DIR = "app/tests/end2end/audio_output"

@pytest.fixture(scope="module")
def setup_audio_output_dir():
    """Ensure the audio output directory exists"""
    os.makedirs(E2E_AUDIO_OUTPUT_DIR, exist_ok=True)
    return E2E_AUDIO_OUTPUT_DIR

@pytest.fixture(scope="module")
def local_file_storage_service(setup_audio_output_dir):
    """Use local file storage instead of S3"""
    return LocalFileStorageService(base_path=setup_audio_output_dir)

@pytest.fixture(scope="module")
def override_services(local_file_storage_service):
    """Override S3 with local file storage"""
    container = Container()
    container.file_storage_service.override(local_file_storage_service)
    return container

@pytest_asyncio.fixture(scope="function")
async def fresh_session(override_services):
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

async def get_order_items_from_redis(session_id: str, container):
    """Get all items in an order from Redis (the source of truth)"""
    from app.core.service_factory import ServiceFactory
    from app.core.database import get_db
    
    service_factory = ServiceFactory(container)
    
    # Get database session for OrderService
    async for db in get_db():
        order_service = service_factory.create_order_service(db)
        
        # Get order from Redis using the session_id as order_id
        order_result = await order_service.get_order(db, session_id)
        
        if not order_result.is_success or not order_result.data:
            return []
        
        # Extract items from the order data
        order_data = order_result.data
        items = order_data.get("items", [])
        
        # Get menu item names for the items
        item_names = []
        for item in items:
            menu_item_id = item.get("menu_item_id")
            if menu_item_id:
                # Get menu item name from database
                from app.models.menu_item import MenuItem
                from sqlalchemy import select
                result = await db.execute(
                    select(MenuItem.name).where(MenuItem.id == menu_item_id)
                )
                menu_item = result.scalar_one_or_none()
                if menu_item:
                    item_names.append(menu_item)
        
        return item_names

async def get_order_item_names_from_redis(session_id: str, container):
    """Get just the names of items in an order from Redis"""
    return await get_order_items_from_redis(session_id, container)

@pytest.mark.asyncio
async def test_multi_item_order_e2e(
    fresh_session,
    override_services,
    setup_audio_output_dir
):
    """
    Test the real workflow end-to-end with multiple items:
    - Real database queries
    - Real Redis session management
    - Real OpenAI API calls
    - Real TTS generation
    - Local file storage
    - Order state verification
    """

    # Test input
    user_text = "I want a quantum burger a nebula wrap and a lunar lemonade please"
    session_id = fresh_session
    restaurant_id = 1

    print(f"\n🚀 Starting multi-item E2E test...")
    print(f"📝 User input: '{user_text}'")
    print(f"🆔 Session ID: {session_id}")
    print(f"🏪 Restaurant ID: {restaurant_id}")

    # Check initial order state (from Redis)
    initial_items = await get_order_item_names_from_redis(session_id, override_services)
    print(f"📋 Initial order items: {initial_items}")
    assert len(initial_items) == 0, f"Expected empty order, got: {initial_items}"

    # Create the workflow state
    initial_state = ConversationWorkflowState(
        session_id=session_id,
        restaurant_id=str(restaurant_id),
        user_input=user_text,
        normalized_user_input=user_text
    )

    print(f"📊 Initial state created")

    # Get the real workflow
    workflow = create_conversation_workflow()

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

    context = {"container": container}

    print(f"🔄 Running workflow...")

    # Run the workflow with real nodes and real LLM calls
    try:
        final_state = await workflow.process_conversation_turn(initial_state, context)

        print(f"✅ Workflow completed!")
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
        
        # Check final order state (from Redis)
        final_items = await get_order_item_names_from_redis(session_id, override_services)
        print(f"📋 Final order items: {final_items}")
        
        # Verify all three items were added
        expected_items = ["Quantum Cheeseburger", "Veggie Nebula Wrap", "Lunar Lemonade"]
        for expected_item in expected_items:
            assert expected_item in final_items, f"Expected {expected_item} in order, got: {final_items}"
        
        assert len(final_items) == 3, f"Expected 3 items in order, got {len(final_items)}: {final_items}"
        
        # Verify the response mentions the items
        response_text = final_state['response_text'].lower()
        assert any(keyword in response_text for keyword in ["added", "order", "quantum", "nebula", "lunar"]), \
            f"Response doesn't mention items or addition: {final_state['response_text']}"
        
        print(f"🎉 All assertions passed! Multi-item order successful!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        raise
