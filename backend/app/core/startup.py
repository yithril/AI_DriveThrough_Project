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
        
        # Create container and service factory
        container = Container()
        service_factory = ServiceFactory(container)
        
        # Create menu cache loader
        cache_loader = service_factory.create_menu_cache_loader()
        
        # Get database session
        async for db_session in get_db():
            try:
                # Load menu cache for all restaurants
                await cache_loader.load_all_restaurants(db_session)
                logger.info("Menu cache loading completed successfully")
                break
            except Exception as e:
                logger.error(f"Failed to load menu cache: {e}")
                raise
            finally:
                await db_session.close()
        
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
    
    # Load menu cache
    await load_menu_cache_on_startup()
    
    logger.info("Application startup tasks completed")
