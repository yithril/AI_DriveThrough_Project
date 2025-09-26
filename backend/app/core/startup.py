"""
Application Startup Tasks

Handles initialization tasks that need to run when the application starts
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.service_factory import ServiceFactory
from app.core.container import Container

logger = logging.getLogger(__name__)


async def load_menu_cache_on_startup():
    """
    Load menu cache on application startup
    
    This function should be called when the application starts to pre-populate
    the menu cache with data from the database.
    """
    try:
        logger.info("Starting menu cache loading on startup...")
        
        # For now, skip cache loading during startup to avoid async context issues
        # The cache will be loaded lazily on first use
        logger.info("Skipping menu cache loading during startup (will load on first use)")
        
    except Exception as e:
        logger.error(f"Menu cache loading failed: {e}")
        # Don't raise the exception - we want the app to start even if cache loading fails
        logger.warning("Application will continue without menu cache")


async def startup_tasks():
    """
    Run all startup tasks
    
    This function should be called when the application starts
    """
    logger.info("Running application startup tasks...")
    
    # Skip menu cache loading during startup to avoid async context issues
    # Cache will be loaded lazily on first use
    logger.info("Skipping menu cache loading during startup (lazy loading enabled)")
    
    logger.info("Application startup tasks completed")
