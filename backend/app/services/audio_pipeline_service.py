"""
Audio Pipeline Service for orchestrating the complete audio processing flow
"""

from typing import Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import time
import uuid

from ..dto.order_result import OrderResult
from ..models.language import Language
from ..agents.state import ConversationWorkflowState
from .speech_service import SpeechService
from .validation_interface import ValidationServiceInterface
from .order_session_service import OrderSessionService
from .file_storage_service import FileStorageService
from .canned_audio_service import CannedAudioService
from ..agents.workflow import ConversationWorkflow
from ..core.logging import get_logger
from ..constants.audio_phrases import AudioPhraseType
from ..repository.restaurant_repository import RestaurantRepository


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
        canned_audio_service: CannedAudioService,
        conversation_workflow: ConversationWorkflow
    ):
        self.speech_service = speech_service
        self.validation_service = validation_service
        self.order_session_service = order_session_service
        self.file_storage_service = file_storage_service
        self.canned_audio_service = canned_audio_service
        self.conversation_workflow = conversation_workflow
        self.logger = get_logger(__name__)
    
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
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.logger.info(f"[{request_id}] Starting audio pipeline - Session: {session_id}, Restaurant: {restaurant_id}, Language: {language}")
        
        try:
            # Step 0: Validate input parameters
            self.logger.debug(f"[{request_id}] Step 0: Validating input parameters")
            await self._validate_request_inputs(restaurant_id, session_id, language, db)
            self.logger.debug(f"[{request_id}] Input validation passed")
            
            # Step 1: Validate audio file
            self.logger.debug(f"[{request_id}] Step 1: Validating audio file - Type: {audio_file.content_type}, Size: {audio_file.size}")
            validation_start = time.time()
            validation_result = await self._validate_audio_file(audio_file)
            validation_duration = time.time() - validation_start
            
            if not validation_result.success:
                self.logger.warning(f"[{request_id}] Audio validation failed: {validation_result.message}")
                raise ValueError(f"Audio validation failed: {validation_result.message}")
            
            self.logger.debug(f"[{request_id}] Audio validation passed in {validation_duration:.2f}s")
            
            # Read audio data
            audio_data = await audio_file.read()
            self.logger.debug(f"[{request_id}] Read audio data: {len(audio_data)} bytes")
            
            # Step 2: Store audio file
            self.logger.debug(f"[{request_id}] Step 2: Storing audio file")
            store_start = time.time()
            store_result = await self._store_audio_file(audio_file, audio_data, restaurant_id, session_id)
            store_duration = time.time() - store_start
            
            if not store_result.success:
                self.logger.error(f"[{request_id}] Audio storage failed: {store_result.message}")
                raise ValueError(f"Audio storage failed: {store_result.message}")
            
            file_id = store_result.data["file_id"]
            self.logger.info(f"[{request_id}] Audio stored successfully - File ID: {file_id}, Duration: {store_duration:.2f}s")
            
            # Step 3: Speech-to-text
            self.logger.debug(f"[{request_id}] Step 3: Starting speech-to-text transcription")
            speech_start = time.time()
            speech_result = await self._transcribe_audio(audio_file, audio_data, language)
            speech_duration = time.time() - speech_start
            
            if not speech_result.success:
                self.logger.error(f"[{request_id}] Speech transcription failed: {speech_result.message}")
                raise ValueError(f"Speech transcription failed: {speech_result.message}")
            
            transcript = speech_result.data["transcript"]
            confidence = speech_result.data.get("confidence", 0)
            self.logger.info(f"[{request_id}] Speech transcribed successfully - Transcript: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}', Confidence: {confidence:.2f}, Duration: {speech_duration:.2f}s")
            
            # Step 4: Safety validation
            self.logger.debug(f"[{request_id}] Step 4: Validating transcript for safety")
            validation_start = time.time()
            guard_result = await self._validate_transcript(transcript)
            validation_duration = time.time() - validation_start
            
            if not guard_result.success:
                self.logger.warning(f"[{request_id}] Transcript validation failed: {guard_result.message}")
                raise ValueError(f"Transcript validation failed: {guard_result.message}")
            
            self.logger.debug(f"[{request_id}] Transcript validation passed in {validation_duration:.2f}s")
            
            # Step 5: Store transcript
            self.logger.debug(f"[{request_id}] Step 5: Storing transcript with metadata")
            await self._store_transcript(file_id, transcript, speech_result.data, restaurant_id, session_id)
            
            # Step 6: Get session state from OrderSessionService
            self.logger.debug(f"[{request_id}] Step 6: Retrieving session state")
            session_start = time.time()
            workflow_state = await self.order_session_service.get_conversation_workflow_state(
                session_id=session_id,
                user_input=transcript
            )
            session_duration = time.time() - session_start
            self.logger.debug(f"[{request_id}] Session state retrieved in {session_duration:.2f}s - State: {workflow_state.current_state}")
            
            # Step 7: Feed into workflow (black box)
            self.logger.debug(f"[{request_id}] Step 7: Processing through conversation workflow")
            workflow_start = time.time()
            completed_workflow_state = await self.conversation_workflow.process_conversation_turn(workflow_state)
            workflow_duration = time.time() - workflow_start
            
            total_duration = time.time() - start_time
            self.logger.info(f"[{request_id}] Audio pipeline completed successfully - Total duration: {total_duration:.2f}s, Workflow duration: {workflow_duration:.2f}s")
            
            # Log response details
            if completed_workflow_state.response_text:
                self.logger.info(f"[{request_id}] Response generated: '{completed_workflow_state.response_text[:100]}{'...' if len(completed_workflow_state.response_text) > 100 else ''}'")
            
            if completed_workflow_state.audio_url:
                self.logger.info(f"[{request_id}] Audio URL generated: {completed_workflow_state.audio_url}")
            
            if completed_workflow_state.errors:
                self.logger.warning(f"[{request_id}] Workflow completed with errors: {completed_workflow_state.errors}")
            
            return completed_workflow_state
            
        except Exception as e:
            total_duration = time.time() - start_time
            self.logger.error(f"[{request_id}] Audio pipeline failed after {total_duration:.2f}s - Error: {str(e)}", exc_info=True)
            
            # Try to get a canned error response
            try:
                # Get restaurant slug from restaurant_id (you might need to adjust this)
                restaurant_slug = f"restaurant_{restaurant_id}"
                
                # Try to get a "come again" canned response for errors
                canned_audio_url = await self.canned_audio_service.get_canned_audio_url(
                    AudioPhraseType.COME_AGAIN, 
                    restaurant_slug
                )
                
                if canned_audio_url:
                    self.logger.info(f"[{request_id}] Using canned error response: {canned_audio_url}")
                    error_response_text = "I'm sorry, I had trouble processing your request. Could you please repeat your order?"
                else:
                    self.logger.warning(f"[{request_id}] No canned error response available, using fallback text")
                    error_response_text = "I'm sorry, I had trouble processing your request. Please try again."
                    canned_audio_url = None
                
            except Exception as canned_error:
                self.logger.error(f"[{request_id}] Failed to get canned error response: {str(canned_error)}")
                error_response_text = "I'm sorry, I had trouble processing your request. Please try again."
                canned_audio_url = None
            
            # Create error workflow state with canned response
            error_state = ConversationWorkflowState(
                session_id=session_id,
                restaurant_id=restaurant_id,
                user_input="",
                response_text=error_response_text,
                audio_url=canned_audio_url,
                errors=[str(e)]
            )
            return error_state
    
    async def _validate_request_inputs(
        self, 
        restaurant_id: int, 
        session_id: str, 
        language: str, 
        db: AsyncSession
    ) -> None:
        """
        Validate all input parameters before processing
        
        Args:
            restaurant_id: Restaurant ID to validate
            session_id: Session ID to validate
            language: Language code to validate
            db: Database session
            
        Raises:
            ValueError: If any validation fails
        """
        # Validate restaurant exists and is active
        restaurant_repo = RestaurantRepository(db)
        if not await restaurant_repo.restaurant_exists_and_active(restaurant_id):
            raise ValueError(f"Restaurant {restaurant_id} not found or inactive")
        
        # Validate session exists
        if not await self.order_session_service.session_exists(session_id):
            raise ValueError(f"Session {session_id} not found")
        
        # Language validation is now handled at the controller level
    
    async def _validate_audio_file(self, audio_file: UploadFile) -> OrderResult:
        """Validate audio file content (basic validation done at controller level)"""
        try:
            # Read file content to check if empty
            file_content = await audio_file.read()
            if len(file_content) == 0:
                self.logger.warning("Empty audio file received")
                return OrderResult.error("File is empty")
            
            self.logger.debug(f"Audio file validation passed - Type: {audio_file.content_type}, Size: {len(file_content)} bytes")
            
            # TODO: Add duration validation (60 seconds max)
            # This would require audio processing to check duration
            
            return OrderResult.success("Audio file validation passed")
            
        except Exception as e:
            self.logger.error(f"File validation failed: {str(e)}", exc_info=True)
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
        """Validate transcript with safety validation"""
        try:
            guard_result = await self.validation_service.validate_input(transcript)
            if not guard_result.success:
                self.logger.warning(f"Transcript blocked by safety filter: {guard_result.message}")
                return OrderResult.error("Input blocked by safety filter")
            
            self.logger.debug("Transcript passed safety validation")
            return OrderResult.success("Transcript validated")
        except Exception as e:
            self.logger.error(f"Transcript validation failed: {str(e)}", exc_info=True)
            return OrderResult.error(f"Transcript validation failed: {str(e)}")
    
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
