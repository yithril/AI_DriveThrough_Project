"""
AI API endpoints for processing user interactions
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import Provide, inject

from ..core.database import get_db
from ..core.config import settings
from ..core.container import Container
from ..services.audio_pipeline_service import AudioPipelineService
from ..models.language import Language
from ..dto.order_result import OrderResult

router = APIRouter(prefix="/api/ai", tags=["AI"])

# JWT authentication removed for demo


@router.post("/process-audio")
@inject
async def process_audio(
    audio_file: UploadFile = File(...),
    restaurant_id: int = Form(...),
    order_id: int = Form(None),  # Optional - if None, create new order
    language: str = Form("en"),
    # jwt: Annotated[dict, Depends(JWT)] = None,  # Removed for demo
    audio_pipeline_service: AudioPipelineService = Depends(Provide[Container.audio_pipeline_service]),
    db: AsyncSession = Depends(get_db)
):
    """
    Process audio input through the complete AI pipeline
    
    Args:
        audio_file: Audio file upload (webm, mp3, wav, mpeg, mp4, m4a)
        restaurant_id: Restaurant ID for context
        order_id: Optional order ID for order-specific operations
        language: Language code (en, es) - defaults to English
        # jwt: NextAuth JWT token (removed for demo)
        audio_pipeline_service: Audio pipeline service
        db: Database session
        
    Returns:
        dict: AI response after processing
    """
    try:
        # Process audio through the complete pipeline
        result = await audio_pipeline_service.process_audio_pipeline(
            audio_file=audio_file,
            restaurant_id=restaurant_id,
            order_id=order_id,
            language=language,
            db=db
        )
        
        if not result.success:
            # Determine appropriate HTTP status based on error type
            if "validation" in result.message.lower():
                status_code = status.HTTP_400_BAD_REQUEST
            elif "not found" in result.message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "forbidden" in result.message.lower():
                status_code = status.HTTP_403_FORBIDDEN
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            raise HTTPException(
                status_code=status_code,
                detail=result.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio processing failed: {str(e)}"
        )




@router.get("/health")
async def ai_health_check():
    """
    Health check endpoint for AI services
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "services": {
            "audio_pipeline_service": "Complete audio processing pipeline",
            "speech_service": "OpenAI Whisper API",
            "llm_guard": "LLM Guard validation", 
            "order_intent_processor": "Intent processing",
            "file_storage": "S3 storage"
        },
        "message": "AI services are running"
    }
