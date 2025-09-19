"""
Logging configuration for AI DriveThru
"""

import logging
import sys
from typing import Optional
from .config import settings

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Use provided log level or default from settings
    level = log_level or settings.LOG_LEVEL
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    
    # Set up specific loggers for different components
    setup_component_loggers()
    
    return logger

def setup_component_loggers():
    """Set up loggers for different application components"""
    
    # AI Agent logging
    ai_logger = logging.getLogger("ai_agent")
    ai_logger.setLevel(logging.INFO)
    
    # Database logging
    db_logger = logging.getLogger("database")
    db_logger.setLevel(logging.WARNING)  # Only log warnings and errors
    
    # API logging
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.INFO)
    
    # Services logging
    services_logger = logging.getLogger("services")
    services_logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific component
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)

# Health check logging
def log_health_check(component: str, status: str, details: str = ""):
    """
    Log health check results
    
    Args:
        component: Component name (e.g., "database", "redis", "s3")
        status: Health status ("healthy", "unhealthy", "degraded")
        details: Additional details
    """
    logger = get_logger("health")
    
    if status == "healthy":
        logger.info(f"Health check passed: {component}")
    elif status == "unhealthy":
        logger.error(f"Health check failed: {component} - {details}")
    else:
        logger.warning(f"Health check degraded: {component} - {details}")

# Performance logging
def log_performance(operation: str, duration: float, details: str = ""):
    """
    Log performance metrics
    
    Args:
        operation: Operation name (e.g., "audio_processing", "database_query")
        duration: Duration in seconds
        details: Additional details
    """
    logger = get_logger("performance")
    logger.info(f"Performance: {operation} took {duration:.2f}s - {details}")

# Error logging with context
def log_error_with_context(error: Exception, context: dict):
    """
    Log errors with additional context
    
    Args:
        error: Exception that occurred
        context: Additional context (user_id, request_id, etc.)
    """
    logger = get_logger("errors")
    logger.error(f"Error occurred: {str(error)} - Context: {context}")
