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
from .validation_interface import ValidationServiceInterface
from .order_session_service import OrderSessionService
from ..core.conversation_orchestrator import ConversationOrchestrator
from ..core.logging import get_logger
from ..constants.audio_phrases import AudioPhraseType
from ..repository.restaurant_repository import RestaurantRepository


class AudioPipelineService:
    """
    Service that orchestrates the complete audio processing pipeline
    """
    
    def __init__(
        self,
        voice_service,  # VoiceService - unified audio service
        validation_service: ValidationServiceInterface,
        order_session_service: OrderSessionService,
        conversation_orchestrator: ConversationOrchestrator
    ):
        self.voice_service = voice_service
        self.validation_service = validation_service
        self.order_session_service = order_session_service
        self.conversation_orchestrator = conversation_orchestrator
        self.logger = get_logger(__name__)
    
    async def process_audio_pipeline(
        self,
        audio_file: UploadFile,
        session_id: str,
        restaurant_id: int,
        language: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process audio through the complete AI pipeline
        
        Args:
            audio_file: Uploaded audio file
            session_id: Session ID for conversation state
            restaurant_id: Restaurant ID for context
            language: Language code (en, es, etc.)
            db: Database session
            
        Returns:
            Dict[str, Any]: Completed workflow state with response and audio URL
        """
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.logger.info(f"[{request_id}] Starting audio pipeline - Session: {session_id}, Restaurant: {restaurant_id}, Language: {language}")
        self.logger.info(f"[{request_id}] DEBUG: Audio file details - Filename: {audio_file.filename}, Content-Type: {audio_file.content_type}, Size: {audio_file.size}")
        
        try:
            # Step 0: Validate input parameters
            self.logger.debug(f"[{request_id}] Step 0: Validating input parameters")
            await self._validate_request_inputs(restaurant_id, session_id, language, db, request_id)
            self.logger.debug(f"[{request_id}] Input validation passed")
            
            # Step 1: Validate audio file
            self.logger.debug(f"[{request_id}] Step 1: Validating audio file - Type: {audio_file.content_type}, Size: {audio_file.size}")
            validation_start = time.time()
            validation_result = await self._validate_audio_file(audio_file)
            validation_duration = time.time() - validation_start
            
            if not validation_result.success:
                self.logger.warning(f"[{request_id}] Audio validation failed: {validation_result.message}")
                # Instead of raising an exception, generate a fallback response
                return await self._generate_fallback_response(request_id, session_id, restaurant_id, "Audio validation failed")
            
            self.logger.debug(f"[{request_id}] Audio validation passed in {validation_duration:.2f}s")
            
            # Read audio data
            self.logger.info(f"[{request_id}] DEBUG: About to read audio file data...")
            audio_data = await audio_file.read()
            self.logger.info(f"[{request_id}] DEBUG: Read audio data - Size: {len(audio_data) if audio_data else 'None'}, Type: {type(audio_data)}")
            if audio_data:
                self.logger.info(f"[{request_id}] DEBUG: First 20 bytes: {audio_data[:20].hex() if len(audio_data) >= 20 else audio_data.hex()}")
            else:
                self.logger.error(f"[{request_id}] DEBUG: audio_data is None! This is the problem!")
            
            # Step 2: Store audio file
            self.logger.debug(f"[{request_id}] Step 2: Storing audio file")
            store_start = time.time()
            store_result = await self._store_audio_file(audio_file, audio_data, restaurant_id, session_id)
            store_duration = time.time() - store_start
            
            if not store_result.success or not store_result.data:
                self.logger.error(f"[{request_id}] Audio storage failed: {store_result.message}")
                # Instead of raising an exception, generate a fallback response
                return await self._generate_fallback_response(request_id, session_id, restaurant_id, "Audio storage failed")
            
            file_id = store_result.data["file_id"]
            self.logger.info(f"[{request_id}] Audio stored successfully - File ID: {file_id}, Duration: {store_duration:.2f}s")
            
            # Step 3: Speech-to-text
            self.logger.info(f"[{request_id}] DEBUG: Step 3: Starting speech-to-text transcription...")
            speech_start = time.time()
            speech_result = await self._transcribe_audio(audio_file, audio_data, language)
            speech_duration = time.time() - speech_start
            
            if not speech_result.success or not speech_result.data:
                self.logger.error(f"[{request_id}] Speech transcription failed: {speech_result.message}")
                # Instead of raising an exception, generate a fallback response
                return await self._generate_fallback_response(request_id, session_id, restaurant_id, "Speech transcription failed")
            
            transcript = speech_result.data["transcript"]
            confidence = speech_result.data.get("confidence", 0)
            self.logger.info(f"[{request_id}] DEBUG: Transcription result - Text: '{transcript}', Confidence: {confidence:.2f}")
            
            # Step 3.5: Store transcript to S3 for audit (DISABLED - not necessary)
            # self.logger.info(f"[{request_id}] DEBUG: Storing transcript to S3...")
            # transcript_store_result = await self._store_transcript(transcript, restaurant_id, session_id, request_id)
            # if transcript_store_result.success:
            #     self.logger.info(f"[{request_id}] DEBUG: Transcript stored successfully - File ID: {transcript_store_result.data.get('file_id')}")
            # else:
            #     self.logger.warning(f"[{request_id}] DEBUG: Failed to store transcript: {transcript_store_result.message}")
            
            self.logger.info(f"[{request_id}] Speech transcribed successfully - Duration: {speech_duration:.2f}s")
            
            # Step 4: Safety validation
            self.logger.debug(f"[{request_id}] Step 4: Validating transcript for safety")
            validation_start = time.time()
            guard_result = await self._validate_transcript(transcript)
            validation_duration = time.time() - validation_start
            
            if not guard_result.success:
                self.logger.warning(f"[{request_id}] Transcript validation failed: {guard_result.message}")
                raise ValueError(f"Transcript validation failed: {guard_result.message}")
            
            self.logger.debug(f"[{request_id}] Transcript validation passed in {validation_duration:.2f}s")
            
            # Step 5: Store transcript (already done in Step 3.5)
            self.logger.debug(f"[{request_id}] Step 5: Transcript already stored in Step 3.5")
            
            # Step 6: Get session state from OrderSessionService
            self.logger.debug(f"[{request_id}] Step 6: Retrieving session state")
            session_start = time.time()
            workflow_state = await self.order_session_service.get_conversation_workflow_state(
                session_id=session_id,
                user_input=transcript
            )
            session_duration = time.time() - session_start
            self.logger.debug(f"[{request_id}] Session state retrieved in {session_duration:.2f}s - State: {workflow_state.get('current_state', 'UNKNOWN')}")
            
            # Step 7: Feed into orchestrator (black box)
            self.logger.debug(f"[{request_id}] Step 7: Processing through conversation orchestrator")
            workflow_start = time.time()
            completed_workflow_state = await self.conversation_orchestrator.process_conversation_turn(
                user_input=workflow_state.get('user_input', transcript),
                session_id=workflow_state.get('session_id', session_id),
                restaurant_id=int(workflow_state.get('restaurant_id', restaurant_id)),
                conversation_history=workflow_state.get('conversation_history', []),
                order_state=workflow_state.get('order_state', {})
            )
            workflow_duration = time.time() - workflow_start
            
            total_duration = time.time() - start_time
            self.logger.info(f"[{request_id}] Audio pipeline completed successfully - Total duration: {total_duration:.2f}s, Workflow duration: {workflow_duration:.2f}s")
            
            # Log response details
            if completed_workflow_state.get('response_text'):
                self.logger.info(f"[{request_id}] Response generated: '{completed_workflow_state['response_text'][:100]}{'...' if len(completed_workflow_state['response_text']) > 100 else ''}'")
            
            if completed_workflow_state.get('audio_url'):
                self.logger.info(f"[{request_id}] Audio URL generated: {completed_workflow_state['audio_url']}")
            
            if completed_workflow_state.get('error'):
                self.logger.warning(f"[{request_id}] Orchestrator completed with errors: {completed_workflow_state['error']}")
            
            return completed_workflow_state
            
        except Exception as e:
            total_duration = time.time() - start_time
            self.logger.error(f"[{request_id}] Audio pipeline failed after {total_duration:.2f}s - Error: {str(e)}", exc_info=True)
            
            # Try to get a canned error response
            try:
                # Get restaurant slug from restaurant_id (you might need to adjust this)
                restaurant_slug = f"restaurant_{restaurant_id}"
                
                # Try to get a "come again" canned response for errors
                canned_audio_url = await self.voice_service.get_canned_phrase(
                    AudioPhraseType.COME_AGAIN, 
                    restaurant_id
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
            error_state = {
                "session_id": session_id,
                "restaurant_id": restaurant_id,
                "user_input": "",
                "response_text": error_response_text,
                "audio_url": canned_audio_url,
                "success": False,
                "errors": [str(e)],
                "intent_type": None
            }
            return error_state
    
    async def _validate_request_inputs(
        self, 
        restaurant_id: int, 
        session_id: str, 
        language: str, 
        db: AsyncSession,
        request_id: str
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
        
        # Validate session exists (skip validation since we're using PostgreSQL fallback)
        # if not await self.order_session_service.session_exists(session_id):
        #     raise ValueError(f"Session {session_id} not found")
        self.logger.info(f"[{request_id}] Skipping session validation - using PostgreSQL fallback")
        
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
            
            # CRITICAL: Reset file pointer to beginning so it can be read again
            await audio_file.seek(0)
            
            # TODO: Add duration validation (60 seconds max)
            # This would require audio processing to check duration
            
            return OrderResult.success("Audio file validation passed")
            
        except Exception as e:
            self.logger.error(f"File validation failed: {str(e)}", exc_info=True)
            return OrderResult.error(f"File validation failed: {str(e)}")
    
    async def _store_audio_file(self, audio_file: UploadFile, audio_data: bytes, restaurant_id: int, session_id: str) -> OrderResult:
        """Store audio file via VoiceService"""
        self.logger.info(f"DEBUG: _store_audio_file called - audio_data size: {len(audio_data) if audio_data else 'None'}")
        self.logger.info(f"DEBUG: Storing user audio to S3 - Restaurant: {restaurant_id}, Session: {session_id}")
        
        # DEBUG: Log what we're passing to VoiceService
        print(f"DEBUG AudioPipelineService calling VoiceService with:")
        print(f"  audio_data: {type(audio_data)} - {len(audio_data) if audio_data else 'None'}")
        print(f"  filename: {audio_file.filename}")
        print(f"  content_type: {audio_file.content_type}")
        print(f"  restaurant_id: {restaurant_id}")
        print(f"  session_id: {session_id}")
        
        if audio_data is None:
            print("ERROR: audio_data is None in AudioPipelineService!")
            self.logger.error("audio_data is None in AudioPipelineService._store_audio_file")
            return OrderResult.error("Audio data is None")
        
        file_id = await self.voice_service.store_uploaded_audio(
            audio_data=audio_data,
            filename=audio_file.filename,
            content_type=audio_file.content_type,
            restaurant_id=restaurant_id,
            session_id=session_id
        )
        
        self.logger.info(f"DEBUG: User audio stored with file_id: {file_id}")
        
        if file_id:
            return OrderResult.success("Audio file stored successfully", data={"file_id": file_id})
        else:
            return OrderResult.error("Failed to store audio file")
    
    async def _transcribe_audio(self, audio_file: UploadFile, audio_data: bytes, language: str) -> OrderResult:
        """Transcribe audio to text"""
        audio_format = audio_file.content_type.split('/')[-1] if audio_file.content_type else "webm"
        selected_language = Language.from_code(language)
        
        transcript = await self.voice_service.transcribe_audio(
            audio_data=audio_data,
            audio_format=audio_format,
            language=language
        )
        
        if transcript:
            return OrderResult.success(
                "Audio transcribed successfully", 
                data={
                    'transcript': transcript,
                    'confidence': 0,  # VoiceService doesn't return confidence yet
                    'duration': 0     # VoiceService doesn't return duration yet
                }
            )
        else:
            return OrderResult.error("Transcription failed")
    
    async def _store_transcript(self, transcript: str, restaurant_id: int, session_id: str, request_id: str) -> OrderResult:
        """Store transcript text to S3 for audit purposes"""
        try:
            # Convert transcript to bytes
            transcript_bytes = transcript.encode('utf-8')
            
            # Create filename with timestamp
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"transcripts/restaurant-{restaurant_id}/session-{session_id}/{timestamp}_transcript.txt"
            
            self.logger.info(f"DEBUG: Storing transcript to S3 - Path: {filename}, Size: {len(transcript_bytes)} bytes")
            
            # Store via file storage service
            store_result = await self.voice_service.file_storage_service.store_file(
                file_data=transcript_bytes,
                file_name=filename,
                content_type="text/plain",
                restaurant_id=restaurant_id
            )
            
            if store_result.success and store_result.data:
                file_id = store_result.data.get('file_id')
                self.logger.info(f"DEBUG: Transcript stored successfully - File ID: {file_id}")
                return OrderResult.success("Transcript stored successfully", data={"file_id": file_id})
            else:
                self.logger.error(f"DEBUG: Failed to store transcript: {store_result.message}")
                return OrderResult.error(f"Failed to store transcript: {store_result.message}")
                
        except Exception as e:
            self.logger.error(f"Transcript storage failed: {str(e)}", exc_info=True)
            return OrderResult.error(f"Transcript storage failed: {str(e)}")
    
    async def _generate_fallback_response(self, request_id: str, session_id: str, restaurant_id: int, error_reason: str) -> Dict[str, Any]:
        """Generate a fallback audio response when the pipeline fails"""
        try:
            self.logger.info(f"[{request_id}] Generating fallback response for error: {error_reason}")
            
            # Try to get a canned error response
            try:
                canned_audio_url = await self.voice_service.get_canned_phrase(
                    AudioPhraseType.COME_AGAIN, 
                    restaurant_id
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
            
            # Create fallback workflow state
            fallback_state = {
                "session_id": session_id,
                "restaurant_id": restaurant_id,
                "user_input": "",
                "response_text": error_response_text,
                "audio_url": canned_audio_url,
                "success": False,
                "error": error_reason,
                "workflow_state": {
                    "current_state": "error",
                    "error_message": error_reason
                }
            }
            
            self.logger.info(f"[{request_id}] Fallback response generated successfully")
            return fallback_state
            
        except Exception as e:
            self.logger.error(f"[{request_id}] Failed to generate fallback response: {str(e)}", exc_info=True)
            # Ultimate fallback - return minimal response
            return {
                "session_id": session_id,
                "restaurant_id": restaurant_id,
                "user_input": "",
                "response_text": "I'm sorry, I had trouble processing your request. Please try again.",
                "audio_url": None,
                "success": False,
                "error": f"Fallback generation failed: {str(e)}",
                "workflow_state": {
                    "current_state": "error",
                    "error_message": f"Fallback generation failed: {str(e)}"
                }
            }
    
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
    
