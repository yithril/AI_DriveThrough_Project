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
from ..agents.state import ConversationWorkflowState

router = APIRouter(prefix="/api/ai", tags=["AI"])

# JWT authentication removed for demo


@router.post("/process-audio")
@inject
async def process_audio(
    audio_file: UploadFile = File(...),
    session_id: str = Form(...),  # Frontend gets this from /current endpoint
    restaurant_id: int = Form(...),
    language: str = Form("en"),
    # jwt: Annotated[dict, Depends(JWT)] = None,  # Removed for demo
    audio_pipeline_service: AudioPipelineService = Depends(Provide[Container.audio_pipeline_service]),
    db: AsyncSession = Depends(get_db)
):
    """
    Process audio input through the complete AI pipeline
    
    Args:
        audio_file: Audio file upload (webm, mp3, wav, mpeg, mp4, m4a)
        session_id: Session ID (frontend gets this from /current endpoint)
        restaurant_id: Restaurant ID for context
        language: Language code (en, es) - defaults to English
        # jwt: NextAuth JWT token (removed for demo)
        audio_pipeline_service: Audio pipeline service
        db: Database session
        
    Returns:
        dict: Simplified response with audio URL and session info
    """
    try:
        # Process audio through the complete pipeline
        workflow_state = await audio_pipeline_service.process_audio_pipeline(
            audio_file=audio_file,
            session_id=session_id,
            restaurant_id=restaurant_id,
            language=language,
            db=db
        )
        
        # Check if workflow processing had errors
        if workflow_state.has_errors():
            # For now, return a generic error response
            # In the future, we could categorize errors and return appropriate HTTP status codes
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing failed: {'; '.join(workflow_state.errors)}"
            )
        
        # Return simplified response to frontend
        return {
            "success": True,
            "session_id": workflow_state.session_id,
            "audio_url": workflow_state.audio_url,
            "response_text": workflow_state.response_text,
            "metadata": {
                "processing_time": 0.0,  # TODO: Add actual timing
                "cached": False,  # TODO: Add caching logic
                "errors": workflow_state.errors if workflow_state.errors else None
            }
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
            "validation_service": "Lightweight validation service", 
            "conversation_workflow": "LangGraph conversation processing",
            "order_session_service": "Session state management",
            "file_storage": "S3 storage"
        },
        "message": "AI services are running"
    }
