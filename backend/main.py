"""
AI DriveThru Backend API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.container import Container
from app.core.logging import setup_logging, get_logger
from app.core.startup import startup_tasks
from app.api import restaurants, ai, sessions, admin

# Set up logging
logger = setup_logging()

# Create container instance and configure it
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

# Wire the dependency injection container with the API modules
container.wire(modules=["app.api.sessions", "app.api.ai", "app.api.admin"])

# Initialize resources (connects to Redis)
container.init_resources()

# Startup tasks will be handled by FastAPI lifespan events

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown tasks
    """
    # Startup
    logger.info("Starting application...")
    try:
        await startup_tasks()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        # Don't raise - let the app start even if startup tasks fail
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        container.shutdown_resources()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Application shutdown failed: {e}")

# Create FastAPI app
app = FastAPI(
    title="AI DriveThru API",
    description="AI-powered drive-thru ordering system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(restaurants.router)
app.include_router(ai.router)
app.include_router(sessions.router)
app.include_router(admin.router)

# Container is now managed by the lifespan context manager

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {"message": "AI DriveThru API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "service": "ai-drivethru-backend"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
