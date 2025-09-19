"""
Configuration settings for AI DriveThru
"""

import os
from typing import Optional

class Settings:
    """Application settings with feature flags"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ai_drivethru")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # JWT (removed for demo - no authentication needed)
    # JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    # JWT_ALGORITHM: str = "HS256"
    # JWT_EXPIRE_MINUTES: int = 30
    
    # NextAuth (removed for demo - no authentication needed)
    # NEXTAUTH_SECRET: str = os.getenv("NEXTAUTH_SECRET", "")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # App
    APP_NAME: str = "AI DriveThru API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Feature Flags
    ENABLE_INVENTORY_CHECKING: bool = os.getenv("ENABLE_INVENTORY_CHECKING", "True").lower() == "true"
    ENABLE_CUSTOMIZATION_VALIDATION: bool = os.getenv("ENABLE_CUSTOMIZATION_VALIDATION", "True").lower() == "true"
    ENABLE_ORDER_LIMITS: bool = os.getenv("ENABLE_ORDER_LIMITS", "True").lower() == "true"
    
    # Order Limits
    MAX_QUANTITY_PER_ITEM: int = int(os.getenv("MAX_QUANTITY_PER_ITEM", "10"))
    MAX_ORDER_TOTAL: float = float(os.getenv("MAX_ORDER_TOTAL", "200.00"))
    MAX_ITEMS_PER_ORDER: int = int(os.getenv("MAX_ITEMS_PER_ORDER", "50"))
    
    # Inventory
    ALLOW_NEGATIVE_INVENTORY: bool = os.getenv("ALLOW_NEGATIVE_INVENTORY", "False").lower() == "true"
    
    # AI Processing
    AI_CONFIDENCE_THRESHOLD: float = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.8"))
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "ai-drivethru-storage")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_ENDPOINT_URL: str = os.getenv("AWS_ENDPOINT_URL", "")

settings = Settings()
