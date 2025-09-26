import pytest
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def event_loop():
    """Create one event loop for the entire test session."""
    # Set environment variables to ensure consistent database connection
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_drivethru")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
