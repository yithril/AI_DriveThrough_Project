"""
Audio Pipeline Service for orchestrating the complete audio processing flow
"""

from typing import Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..dto.order_result import OrderResult
from ..models.language import Language
from ..agents.state import ConversationWorkflowState
from .speech_service import SpeechService
from .validation_interface import ValidationServiceInterface
from .order_session_service import OrderSessionService
from .file_storage_service import FileStorageService
from ..agents.workflow import ConversationWorkflow


class AudioPipelineService:
    """
    Service that orchestrates the complete audio processing pipeline
    """
    
    def __init__(
        self,
        speech_service: SpeechService,
        validation_service: ValidationServiceInterface,
        order_session_service: OrderSessionService,
        file_storage_service: FileStorageService,
        conversation_workflow: ConversationWorkflow
    ):
        self.speech_service = speech_service
        self.validation_service = validation_service
        self.order_session_service = order_session_service
        self.file_storage_service = file_storage_service
        self.conversation_workflow = conversation_workflow
    
    async def process_audio_pipeline(
        self,
        audio_file: UploadFile,
        session_id: str,
        restaurant_id: int,
        language: str,
        db: AsyncSession
    ) -> ConversationWorkflowState:
        """
        Process audio through the complete AI pipeline
        
        Args:
            audio_file: Uploaded audio file
            session_id: Session ID for conversation state
            restaurant_id: Restaurant ID for context
            language: Language code (en, es, etc.)
            db: Database session
            
        Returns:
            ConversationWorkflowState: Completed workflow state with response and audio URL
        """
        try:
            # Step 1: Validate audio file
            validation_result = await self._validate_audio_file(audio_file)
            if not validation_result.success:
                raise ValueError(f"Audio validation failed: {validation_result.message}")
            
            # Read audio data
            audio_data = await audio_file.read()
            
            # Step 2: Store audio file
            store_result = await self._store_audio_file(audio_file, audio_data, restaurant_id, session_id)
            if not store_result.success:
                raise ValueError(f"Audio storage failed: {store_result.message}")
            
            file_id = store_result.data["file_id"]
            
            # Step 3: Speech-to-text
            speech_result = await self._transcribe_audio(audio_file, audio_data, language)
            if not speech_result.success:
                raise ValueError(f"Speech transcription failed: {speech_result.message}")
            
            transcript = speech_result.data["transcript"]
            
            # Step 4: LLM Guard validation
            guard_result = await self._validate_transcript(transcript)
            if not guard_result.success:
                raise ValueError(f"Transcript validation failed: {guard_result.message}")
            
            # Step 5: Store transcript
            await self._store_transcript(file_id, transcript, speech_result.data, restaurant_id, session_id)
            
            # Step 6: Get session state from OrderSessionService
            workflow_state = await self.order_session_service.get_conversation_workflow_state(
                session_id=session_id,
                user_input=transcript
            )
            
            # Step 7: Feed into workflow (black box)
            completed_workflow_state = await self.conversation_workflow.process_conversation_turn(workflow_state)
            
            # Return completed workflow state
            return completed_workflow_state
            
        except Exception as e:
            # Create error workflow state
            error_state = ConversationWorkflowState(
                session_id=session_id,
                restaurant_id=restaurant_id,
                user_input="",
                response_text=f"I'm sorry, I had trouble processing your request. Please try again.",
                errors=[str(e)]
            )
            return error_state
    
    async def _validate_audio_file(self, audio_file: UploadFile) -> OrderResult:
        """Validate audio file for size, type, and duration"""
        try:
            # Check file type
            allowed_types = ["audio/webm", "audio/mp3", "audio/wav", "audio/mpeg", "audio/mp4", "audio/m4a"]
            if audio_file.content_type not in allowed_types:
                return OrderResult.error(
                    f"Invalid file type: {audio_file.content_type}. Allowed types: {', '.join(allowed_types)}"
                )
            
            # Check file size (10MB max)
            max_size = 10 * 1024 * 1024  # 10MB
            file_content = await audio_file.read()
            if len(file_content) > max_size:
                return OrderResult.error("File size exceeds 10MB limit")
            
            if len(file_content) == 0:
                return OrderResult.error("File is empty")
            
            # TODO: Add duration validation (60 seconds max)
            # This would require audio processing to check duration
            
            return OrderResult.success("Audio file validation passed")
            
        except Exception as e:
            return OrderResult.error(f"File validation failed: {str(e)}")
    
    async def _store_audio_file(self, audio_file: UploadFile, audio_data: bytes, restaurant_id: int, session_id: str) -> OrderResult:
        """Store audio file in S3"""
        store_result = await self.file_storage_service.store_file(
            file_data=audio_data,
            file_name=audio_file.filename,
            content_type=audio_file.content_type,
            restaurant_id=restaurant_id,
            order_id=None,  # We don't have order_id anymore, use session_id for organization
            metadata={"session_id": session_id}  # Store session_id in metadata
        )
        
        if not store_result.success:
            return OrderResult.error(f"Failed to store audio file: {store_result.message}")
        
        return store_result
    
    async def _transcribe_audio(self, audio_file: UploadFile, audio_data: bytes, language: str) -> OrderResult:
        """Transcribe audio to text"""
        audio_format = audio_file.content_type.split('/')[-1] if audio_file.content_type else "webm"
        selected_language = Language.from_code(language)
        
        speech_result = await self.speech_service.transcribe_audio(
            audio_data, 
            audio_format, 
            selected_language
        )
        
        if not speech_result.success:
            return OrderResult.error(f"Speech transcription failed: {speech_result.message}")
        
        return speech_result
    
    async def _validate_transcript(self, transcript: str) -> OrderResult:
        """Validate transcript with LLM Guard"""
        guard_result = await self.validation_service.validate_input(transcript)
        if not guard_result.success:
            return OrderResult.error("Input blocked by safety filter")
        
        return OrderResult.success("Transcript validated")
    
    async def _store_transcript(self, file_id: str, transcript: str, speech_data: Dict[str, Any], restaurant_id: int, session_id: str) -> None:
        """Store transcript with metadata"""
        await self.file_storage_service.store_transcript(
            file_id=file_id,
            transcript=transcript,
            metadata={
                "duration": speech_data.get("duration", 0),
                "confidence": speech_data.get("confidence", 0),
                "restaurant_id": restaurant_id,
                "session_id": session_id
            },
            restaurant_id=restaurant_id,
            order_id=None,  # We don't have order_id anymore
            metadata_override={"session_id": session_id}  # Store session_id in metadata
        )
