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
    # Validate audio file at controller level
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is required"
        )
    
    # Check file type
    allowed_types = ["audio/webm", "audio/mp3", "audio/wav", "audio/mpeg", "audio/mp4", "audio/m4a"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {audio_file.content_type}. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Check file size (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    if audio_file.size and audio_file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Validate language code
    valid_languages = ["en", "es"]
    if language not in valid_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language '{language}'. Must be one of: {valid_languages}"
        )
    
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
        if workflow_state.get('errors') or not workflow_state.get('success', True):
            # Check error type and return appropriate HTTP status code
            errors = workflow_state.get('errors', [])
            error_message = '; '.join(errors) if errors else 'Processing failed'
            error_lower = error_message.lower()
            
            if any(keyword in error_lower for keyword in ['restaurant', 'session']) and 'not found' in error_lower:
                # Resource not found (404)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_message
                )
            elif any(keyword in error_lower for keyword in ['invalid', 'inactive']):
                # Bad request format (400)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            else:
                # Internal server error (500)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Processing failed: {error_message}"
                )
        
        # Return simplified response to frontend
        return {
            "success": True,
            "session_id": workflow_state.get('session_id'),
            "audio_url": workflow_state.get('audio_url'),
            "response_text": workflow_state.get('response_text'),
            "order_state_changed": workflow_state.get('order_state_changed', False),  # Tell frontend if order was modified
            "metadata": {
                "processing_time": 0.0,  # TODO: Add actual timing
                "cached": False,  # TODO: Add caching logic
                "errors": workflow_state.get('errors') if workflow_state.get('errors') else None
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
