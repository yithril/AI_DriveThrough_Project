"""
Audio Pipeline Service for orchestrating the complete audio processing flow
"""

from typing import Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..dto.order_result import OrderResult
from ..models.language import Language
from .speech_service import SpeechService
from .validation_interface import ValidationServiceInterface
from .order_intent_processor import OrderIntentProcessor
from .file_storage_service import FileStorageService
from .order_service import OrderService


class AudioPipelineService:
    """
    Service that orchestrates the complete audio processing pipeline
    """
    
    def __init__(
        self,
        speech_service: SpeechService,
        validation_service: ValidationServiceInterface,
        order_intent_processor: OrderIntentProcessor,
        file_storage_service: FileStorageService,
        order_service: OrderService
    ):
        self.speech_service = speech_service
        self.validation_service = validation_service
        self.order_intent_processor = order_intent_processor
        self.file_storage_service = file_storage_service
        self.order_service = order_service
    
    async def process_audio_pipeline(
        self,
        audio_file: UploadFile,
        restaurant_id: int,
        order_id: Optional[int],
        language: str,
        db: AsyncSession
    ) -> OrderResult:
        """
        Process audio through the complete AI pipeline
        
        Args:
            audio_file: Uploaded audio file
            restaurant_id: Restaurant ID for context
            order_id: Optional order ID (will create new if None)
            language: Language code (en, es, etc.)
            db: Database session
            
        Returns:
            OrderResult: Complete pipeline result
        """
        try:
            # Step 1: Validate audio file
            validation_result = await self._validate_audio_file(audio_file)
            if not validation_result.success:
                return validation_result
            
            # Read audio data
            audio_data = await audio_file.read()
            
            # Step 2: Handle order creation or retrieval
            order_result = await self._ensure_order_exists(restaurant_id, order_id, db)
            if not order_result.success:
                return order_result
            
            order_id = order_result.data
            
            # Step 3: Store audio file
            store_result = await self._store_audio_file(audio_file, audio_data, restaurant_id, order_id)
            if not store_result.success:
                return store_result
            
            file_id = store_result.data["file_id"]
            
            # Step 4: Speech-to-text
            speech_result = await self._transcribe_audio(audio_file, audio_data, language)
            if not speech_result.success:
                return speech_result
            
            transcript = speech_result.data["transcript"]
            
            # Step 5: LLM Guard validation
            guard_result = await self._validate_transcript(transcript)
            if not guard_result.success:
                return guard_result
            
            # Step 6: Intent processing
            intent_result = await self._process_intent(transcript, restaurant_id, order_id, db)
            if not intent_result.success:
                return intent_result
            
            # Step 7: Store transcript
            await self._store_transcript(file_id, transcript, speech_result.data, restaurant_id, order_id)
            
            # Return complete result
            return OrderResult.success(
                intent_result.message,
                data={
                    "transcript": transcript,
                    "language": speech_result.data.get("language", "en"),
                    "language_name": speech_result.data.get("language_name", "English"),
                    "intent": intent_result.data,
                    "file_id": file_id,
                    "order_id": order_id
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Audio pipeline processing failed: {str(e)}")
    
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
    
    async def _ensure_order_exists(self, restaurant_id: int, order_id: Optional[int], db: AsyncSession) -> OrderResult:
        """Ensure order exists, create if needed"""
        if order_id is None:
            # Create new order
            order_result = await self.order_service.create_order(
                restaurant_id=restaurant_id,
                customer_name=None,
                customer_phone=None,
                user_id=None
            )
            if not order_result.success:
                return OrderResult.error(f"Failed to create order: {order_result.message}")
            return OrderResult.success("Order created", data=order_result.data.id)
        else:
            # Verify existing order
            order_result = await self.order_service.get_order(order_id)
            if not order_result.success:
                return OrderResult.error(f"Order not found: {order_result.message}")
            
            # Verify order belongs to restaurant
            if order_result.data.restaurant_id != restaurant_id:
                return OrderResult.error("Order does not belong to this restaurant")
            
            return OrderResult.success("Order verified", data=order_id)
    
    async def _store_audio_file(self, audio_file: UploadFile, audio_data: bytes, restaurant_id: int, order_id: int) -> OrderResult:
        """Store audio file in S3"""
        store_result = await self.file_storage_service.store_file(
            file_data=audio_data,
            file_name=audio_file.filename,
            content_type=audio_file.content_type,
            restaurant_id=restaurant_id,
            order_id=order_id
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
    
    async def _process_intent(self, transcript: str, restaurant_id: int, order_id: int, db: AsyncSession) -> OrderResult:
        """Process intent using OrderIntentProcessor"""
        ai_result = await self.order_intent_processor.process_intent(
            text=transcript,
            restaurant_id=restaurant_id,
            order_id=order_id,
            db=db
        )
        
        if not ai_result.success:
            return OrderResult.error(f"AI processing failed: {ai_result.message}")
        
        return ai_result
    
    async def _store_transcript(self, file_id: str, transcript: str, speech_data: Dict[str, Any], restaurant_id: int, order_id: int) -> None:
        """Store transcript with metadata"""
        await self.file_storage_service.store_transcript(
            file_id=file_id,
            transcript=transcript,
            metadata={
                "duration": speech_data.get("duration", 0),
                "confidence": speech_data.get("confidence", 0),
                "restaurant_id": restaurant_id,
                "order_id": order_id
            },
            restaurant_id=restaurant_id,
            order_id=order_id
        )
