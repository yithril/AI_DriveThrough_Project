"""
File storage service with interface for local and cloud storage
"""

import os
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
from pathlib import Path

from ..dto.order_result import OrderResult


class FileStorageInterface(ABC):
    """
    Abstract interface for file storage operations
    """
    
    @abstractmethod
    async def store_file(self, file_data: bytes, file_name: str, content_type: str, restaurant_id: int = None, order_id: int = None) -> OrderResult:
        """
        Store a file and return its storage information
        
        Args:
            file_data: Raw file bytes
            file_name: Original file name
            content_type: MIME type of the file
            
        Returns:
            OrderResult: Storage result with file information
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_id: str) -> OrderResult:
        """
        Retrieve a file by its ID
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            OrderResult: File data or error
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> OrderResult:
        """
        Delete a file by its ID
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            OrderResult: Deletion result
        """
        pass
    
    @abstractmethod
    async def store_transcript(self, file_id: str, transcript: str, metadata: Dict[str, Any]) -> OrderResult:
        """
        Store transcript data associated with a file
        
        Args:
            file_id: Associated file ID
            transcript: Transcribed text
            metadata: Additional metadata (duration, confidence, etc.)
            
        Returns:
            OrderResult: Storage result
        """
        pass
    
    @abstractmethod
    async def get_transcript(self, file_id: str) -> OrderResult:
        """
        Retrieve transcript data for a file
        
        Args:
            file_id: Associated file ID
            
        Returns:
            OrderResult: Transcript data or error
        """
        pass


class LocalFileStorageService(FileStorageInterface):
    """
    Local file storage implementation for development
    """
    
    def __init__(self, base_path: str = "storage"):
        """
        Initialize local file storage
        
        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.files_path = self.base_path / "files"
        self.transcripts_path = self.base_path / "transcripts"
        
        # Create directories if they don't exist
        self.files_path.mkdir(parents=True, exist_ok=True)
        self.transcripts_path.mkdir(parents=True, exist_ok=True)
    
    async def store_file(self, file_data: bytes, file_name: str, content_type: str) -> OrderResult:
        """Store file locally"""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Determine file extension from content type
            extension = self._get_extension_from_content_type(content_type)
            if not extension:
                extension = Path(file_name).suffix or ".bin"
            
            # Create file path
            file_path = self.files_path / f"{file_id}{extension}"
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Store file metadata
            metadata = {
                "file_id": file_id,
                "original_name": file_name,
                "content_type": content_type,
                "size": len(file_data),
                "stored_at": datetime.now().isoformat(),
                "file_path": str(file_path)
            }
            
            return OrderResult.success(
                "File stored successfully",
                data=metadata
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to store file: {str(e)}")
    
    async def get_file(self, file_id: str) -> OrderResult:
        """Retrieve file from local storage"""
        try:
            # Find file by ID (scan for files with this ID)
            for file_path in self.files_path.glob(f"{file_id}.*"):
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                return OrderResult.success(
                    "File retrieved successfully",
                    data={
                        "file_id": file_id,
                        "file_data": file_data,
                        "file_path": str(file_path)
                    }
                )
            
            return OrderResult.error("File not found")
            
        except Exception as e:
            return OrderResult.error(f"Failed to retrieve file: {str(e)}")
    
    async def delete_file(self, file_id: str) -> OrderResult:
        """Delete file from local storage"""
        try:
            # Find and delete file
            for file_path in self.files_path.glob(f"{file_id}.*"):
                file_path.unlink()
                return OrderResult.success("File deleted successfully")
            
            return OrderResult.error("File not found")
            
        except Exception as e:
            return OrderResult.error(f"Failed to delete file: {str(e)}")
    
    async def store_transcript(self, file_id: str, transcript: str, metadata: Dict[str, Any]) -> OrderResult:
        """Store transcript data locally"""
        try:
            transcript_path = self.transcripts_path / f"{file_id}.json"
            
            import json
            transcript_data = {
                "file_id": file_id,
                "transcript": transcript,
                "metadata": metadata,
                "created_at": datetime.now().isoformat()
            }
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2)
            
            return OrderResult.success(
                "Transcript stored successfully",
                data=transcript_data
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to store transcript: {str(e)}")
    
    async def get_transcript(self, file_id: str) -> OrderResult:
        """Retrieve transcript data"""
        try:
            transcript_path = self.transcripts_path / f"{file_id}.json"
            
            if not transcript_path.exists():
                return OrderResult.error("Transcript not found")
            
            import json
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            return OrderResult.success(
                "Transcript retrieved successfully",
                data=transcript_data
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to retrieve transcript: {str(e)}")
    
    def _get_extension_from_content_type(self, content_type: str) -> Optional[str]:
        """Get file extension from MIME type"""
        mime_to_ext = {
            "audio/webm": ".webm",
            "audio/mp3": ".mp3",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mp4": ".mp4",
            "audio/m4a": ".m4a",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif"
        }
        return mime_to_ext.get(content_type.lower())


class S3FileStorageService(FileStorageInterface):
    """
    AWS S3 file storage implementation for production
    """
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", endpoint_url: str = None):
        """
        Initialize S3 file storage
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint URL (for LocalStack, MinIO, etc.)
        """
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize boto3 S3 client
        import boto3
        client_kwargs = {'region_name': region}
        if endpoint_url:
            client_kwargs['endpoint_url'] = endpoint_url
        self.s3_client = boto3.client('s3', **client_kwargs)
    
    async def _ensure_bucket_exists(self):
        """Ensure the S3 bucket exists, create if it doesn't"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except self.s3_client.exceptions.NoSuchBucket:
            # Create bucket if it doesn't exist
            self.s3_client.create_bucket(Bucket=self.bucket_name)
        except Exception as e:
            # Try to create anyway
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except Exception as create_error:
                raise
    
    async def store_file(self, file_data: bytes, file_name: str, content_type: str, restaurant_id: int = None, order_id: int = None) -> OrderResult:
        """Store file in S3 with restaurant/order organization"""
        try:
            # Ensure bucket exists
            await self._ensure_bucket_exists()
            
            # Determine file extension
            extension = self._get_extension_from_content_type(content_type)
            if not extension:
                extension = Path(file_name).suffix or ".bin"
            
            # Create organized S3 key structure
            if "/" in file_name and not file_name.startswith("files/"):
                # file_name is already an organized path (e.g., "audio/canned/greeting_restaurant_20.mp3")
                # Use it directly as the S3 key
                file_id = str(uuid.uuid4())  # Still need file_id for metadata
                s3_key = file_name
            elif restaurant_id and order_id:
                # For audio files, use UUID to avoid conflicts
                file_id = str(uuid.uuid4())
                s3_key = f"restaurants/{restaurant_id}/orders/{order_id}/audio/{file_id}{extension}"
            elif restaurant_id:
                # Check if this is an image file based on content type
                if content_type and content_type.startswith('image/'):
                    # For images, use the original filename to maintain readability
                    file_id = str(uuid.uuid4())  # Still need file_id for metadata
                    s3_key = f"restaurants/{restaurant_id}/images/{file_name}"
                else:
                    # For other files, use UUID
                    file_id = str(uuid.uuid4())
                    s3_key = f"restaurants/{restaurant_id}/audio/{file_id}{extension}"
            else:
                # Fallback to old structure with UUID
                file_id = str(uuid.uuid4())
                s3_key = f"files/{file_id}{extension}"
            
            # Upload to S3
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    "original_name": file_name,
                    "file_id": file_id
                }
            )
            
            # Store metadata
            metadata = {
                "file_id": file_id,
                "original_name": file_name,
                "content_type": content_type,
                "size": len(file_data),
                "stored_at": datetime.now().isoformat(),
                "s3_key": s3_key,
                "s3_url": f"s3://{self.bucket_name}/{s3_key}"
            }
            
            return OrderResult.success(
                "File stored successfully in S3",
                data=metadata
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to store file in S3: {str(e)}")
    
    async def get_file(self, file_id: str) -> OrderResult:
        """Retrieve file from S3"""
        try:
            # List objects to find the file
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"files/{file_id}"
            )
            
            if 'Contents' not in response or not response['Contents']:
                return OrderResult.error("File not found")
            
            # Get the first matching file
            s3_key = response['Contents'][0]['Key']
            
            # Retrieve file from S3
            file_response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            file_data = file_response['Body'].read()
            
            return OrderResult.success(
                "File retrieved successfully from S3",
                data={
                    "file_id": file_id,
                    "file_data": file_data,
                    "s3_key": s3_key
                }
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to retrieve file from S3: {str(e)}")
    
    async def delete_file(self, file_id: str) -> OrderResult:
        """Delete file from S3"""
        try:
            # List objects to find the file
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"files/{file_id}"
            )
            
            if 'Contents' not in response or not response['Contents']:
                return OrderResult.error("File not found")
            
            # Delete the file
            s3_key = response['Contents'][0]['Key']
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return OrderResult.success("File deleted successfully from S3")
            
        except Exception as e:
            return OrderResult.error(f"Failed to delete file from S3: {str(e)}")
    
    async def store_transcript(self, file_id: str, transcript: str, metadata: Dict[str, Any], restaurant_id: int = None, order_id: int = None) -> OrderResult:
        """Store transcript in S3 with restaurant/order organization"""
        try:
            # Create organized transcript key structure
            if restaurant_id and order_id:
                transcript_key = f"restaurants/{restaurant_id}/orders/{order_id}/transcripts/{file_id}.json"
            elif restaurant_id:
                transcript_key = f"restaurants/{restaurant_id}/transcripts/{file_id}.json"
            else:
                transcript_key = f"transcripts/{file_id}.json"  # Fallback to old structure
            
            import json
            transcript_data = {
                "file_id": file_id,
                "transcript": transcript,
                "metadata": metadata,
                "created_at": datetime.now().isoformat()
            }
            
            # Upload transcript to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=transcript_key,
                Body=json.dumps(transcript_data),
                ContentType="application/json"
            )
            
            return OrderResult.success(
                "Transcript stored successfully in S3",
                data=transcript_data
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to store transcript in S3: {str(e)}")
    
    async def get_transcript(self, file_id: str) -> OrderResult:
        """Retrieve transcript from S3"""
        try:
            transcript_key = f"transcripts/{file_id}.json"
            
            # Retrieve transcript from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=transcript_key
            )
            
            import json
            transcript_data = json.loads(response['Body'].read().decode('utf-8'))
            
            return OrderResult.success(
                "Transcript retrieved successfully from S3",
                data=transcript_data
            )
            
        except self.s3_client.exceptions.NoSuchKey:
            return OrderResult.error("Transcript not found")
        except Exception as e:
            return OrderResult.error(f"Failed to retrieve transcript from S3: {str(e)}")
    
    def _get_extension_from_content_type(self, content_type: str) -> Optional[str]:
        """Get file extension from MIME type"""
        mime_to_ext = {
            "audio/webm": ".webm",
            "audio/mp3": ".mp3",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mp4": ".mp4",
            "audio/m4a": ".m4a",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif"
        }
        return mime_to_ext.get(content_type.lower())


class FileStorageService:
    """
    Main file storage service using S3
    """
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", endpoint_url: str = None):
        """
        Initialize file storage service with S3
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint URL (for LocalStack, MinIO, etc.)
        """
        self.storage = S3FileStorageService(bucket_name, region, endpoint_url)
    
    async def store_file(self, file_data: bytes, file_name: str, content_type: str) -> OrderResult:
        """Store a file"""
        return await self.storage.store_file(file_data, file_name, content_type)
    
    async def get_file(self, file_id: str) -> OrderResult:
        """Retrieve a file"""
        return await self.storage.get_file(file_id)
    
    async def delete_file(self, file_id: str) -> OrderResult:
        """Delete a file"""
        return await self.storage.delete_file(file_id)
    
    async def store_transcript(self, file_id: str, transcript: str, metadata: Dict[str, Any]) -> OrderResult:
        """Store transcript data"""
        return await self.storage.store_transcript(file_id, transcript, metadata)
    
    async def get_transcript(self, file_id: str) -> OrderResult:
        """Retrieve transcript data"""
        return await self.storage.get_transcript(file_id)
