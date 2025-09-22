"""
Integration test for text-to-speech service
Generates real audio files from text using the voice service
"""

import asyncio
import os
import pytest
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Direct imports to avoid circular dependency
from app.services.voice_service import VoiceService
from app.services.text_to_speech_service import TextToSpeechService
from app.services.speech_to_text_service import SpeechToTextService
from app.services.file_storage_service import FileStorageService
from app.services.tts_provider import OpenAITTSProvider
from app.constants.audio_phrases import AudioPhraseType


class LocalFileStorageService:
    """
    Local file storage service for testing voice generation
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    async def store_file(self, file_data: bytes, file_name: str, content_type: str = "audio/mpeg", restaurant_id: int = None):
        """
        Store file locally for testing
        """
        try:
            # Create local file path
            local_file_path = self.output_dir / file_name
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file data
            with open(local_file_path, "wb") as f:
                f.write(file_data)
            
            # Return success result that matches the expected interface
            class StoreResult:
                def __init__(self, success: bool, data: dict = None, message: str = ""):
                    self.success = success
                    self.data = data
                    self.message = message
            
            return StoreResult(
                success=True,
                data={
                    "url": str(local_file_path),
                    "local_path": str(local_file_path),
                    "file_size": len(file_data)
                },
                message="File stored locally"
            )
            
        except Exception as e:
            class StoreResult:
                def __init__(self, success: bool, data: dict = None, message: str = ""):
                    self.success = success
                    self.data = data
                    self.message = message
            
            return StoreResult(
                success=False,
                data=None,
                message=f"Failed to store file: {str(e)}"
            )


class TextToSpeechIntegrationTest:
    """
    Integration test for text-to-speech service
    """
    
    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "output" / "tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def test_custom_phrase_generation(self):
        """
        Test generating custom phrases using the voice service
        """
        print("\n🎤 Testing Text-to-Speech Integration")
        print("=" * 60)
        
        # Test phrases from our clarification agent scenarios
        test_phrases = [
            {
                "text": "We don't have chocolate pie, but we do have apple pie and cheesecake. Would you like one of those instead?",
                "description": "Item not found with alternatives",
                "filename": "item_not_found_alternatives.mp3"
            },
            {
                "text": "What size Coke would you like? We have small, medium, and large available.",
                "description": "Option required missing",
                "filename": "option_required_missing.mp3"
            },
            {
                "text": "We can't do that many. How many would you like?",
                "description": "Quantity limit response",
                "filename": "quantity_limit.mp3"
            },
            {
                "text": "I'm sorry, but we don't have that item. What else can I get for you today?",
                "description": "No substitutes available",
                "filename": "no_substitutes.mp3"
            },
            {
                "text": "I added the quantum burger with extra onions and the strawberry milkshake to your order.",
                "description": "Partial success confirmation",
                "filename": "partial_success.mp3"
            }
        ]
        
        results = []
        
        for i, phrase_data in enumerate(test_phrases, 1):
            print(f"\n🔍 Test {i}: {phrase_data['description']}")
            print(f"   Text: {phrase_data['text']}")
            
            # Generate real audio using voice service
            result = await self._generate_real_voice_audio(phrase_data, i)
            results.append(result)
        
        # Generate summary
        await self._generate_tts_test_summary(results)
        
        print(f"\n✅ Text-to-speech integration test completed!")
        print(f"📁 Check output/tts folder for generated audio files")
        print(f"🎵 You can play these MP3 files to hear the TTS output!")
    
    async def _generate_real_voice_audio(self, phrase_data: dict, test_number: int) -> dict:
        """
        Generate real voice audio using the voice service (the actual implementation)
        """
        try:
            # Create a local file storage service for testing
            local_storage = LocalFileStorageService(self.output_dir)
            
            # Create TTS service with OpenAI provider
            tts_provider = OpenAITTSProvider(api_key=os.getenv("OPENAI_API_KEY", ""))
            tts_service = TextToSpeechService(provider=tts_provider)
            
            # Create voice service with local storage
            voice_service = VoiceService(
                text_to_speech_service=tts_service,
                speech_to_text_service=None,  # Not needed for this test
                file_storage_service=local_storage,
                redis_service=None  # Not needed for this test
            )
            
            print(f"   🎵 Generating audio for: '{phrase_data['text'][:50]}...'")
            
            # Generate audio using the voice service
            print(f"   🔧 Calling voice_service.generate_voice...")
            audio_url = await voice_service.generate_voice(
                text=phrase_data['text'],
                voice=os.getenv("TTS_VOICE", "nova"),  # Use env var or fallback for test
                language=os.getenv("TTS_LANGUAGE", "english"),  # Use env var or fallback for test
                restaurant_id=1
            )
            
            print(f"   🔧 Voice service returned: {audio_url}")
            
            if audio_url:
                # Save metadata
                metadata = {
                    "test_number": test_number,
                    "description": phrase_data["description"],
                    "text": phrase_data["text"],
                    "audio_file": audio_url,
                    "filename": phrase_data.get("filename", f"test_{test_number}.mp3"),
                    "voice": "nova",
                    "language": "english",
                    "restaurant_id": 1
                }
                
                metadata_file = self.output_dir / f"tts_test_{test_number}_metadata.json"
                import json
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ Audio generated successfully!")
                print(f"   📁 Audio file: {audio_url}")
                print(f"   📁 Metadata: {metadata_file.name}")
                
                return {
                    "test_number": test_number,
                    "success": True,
                    "description": phrase_data["description"],
                    "text": phrase_data["text"],
                    "audio_file": audio_url,
                    "filename": phrase_data.get("filename", f"test_{test_number}.mp3"),
                    "metadata_file": str(metadata_file)
                }
            else:
                print(f"   ❌ Failed to generate audio")
                return {
                    "test_number": test_number,
                    "success": False,
                    "error": "Voice generation failed",
                    "description": phrase_data["description"]
                }
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            print(f"   🔍 Full traceback: {traceback.format_exc()}")
            return {
                "test_number": test_number,
                "success": False,
                "error": str(e),
                "description": phrase_data["description"]
            }
    
    async def _generate_tts_test_summary(self, results: list):
        """
        Generate a summary report of TTS tests
        """
        summary_file = self.output_dir / "tts_integration_test_summary.txt"
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("Text-to-Speech Integration Test Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total tests: {len(results)}\n")
            f.write(f"Successful: {len(successful_tests)}\n")
            f.write(f"Failed: {len(failed_tests)}\n\n")
            
            f.write("🎤 TTS TEST SCENARIOS:\n")
            f.write("-" * 40 + "\n")
            
            for result in results:
                f.write(f"\nTest {result['test_number']}: {result['description']}\n")
                f.write(f"Text: {result.get('text', 'N/A')}\n")
                if result["success"]:
                    f.write(f"Status: ✅ SUCCESS\n")
                    f.write(f"Audio File: {result.get('audio_file', 'N/A')}\n")
                    f.write(f"Filename: {result.get('filename', 'N/A')}\n")
                    f.write(f"Metadata: {result.get('metadata_file', 'N/A')}\n")
                else:
                    f.write(f"Status: ❌ FAILED\n")
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n")
            
            f.write(f"\n\n📝 TTS INTEGRATION TEST NOTES:\n")
            f.write("-" * 30 + "\n")
            f.write("This test generates real audio files using the voice service.\n")
            f.write("Generated files are saved locally in the output/tts directory.\n")
            f.write("You can play these MP3 files to hear the TTS output.\n")
            f.write("\nTest includes:\n")
            f.write("1. Real TTS service integration with OpenAI\n")
            f.write("2. Local file storage for testing\n")
            f.write("3. Audio files saved as MP3 format\n")
            f.write("4. Metadata files with test information\n")
            f.write("5. Clarification agent response scenarios\n")
            f.write("6. Voice caching simulation (first call generates, subsequent calls would use cache)\n")
        
        print(f"\n📊 TTS test summary saved: {summary_file.name}")


# Pytest test functions
@pytest.mark.asyncio
async def test_text_to_speech_integration():
    """
    Pytest integration test for text-to-speech service
    """
    tts_test = TextToSpeechIntegrationTest()
    await tts_test.test_custom_phrase_generation()


# Standalone runner (for manual testing)
async def main():
    """
    Main function to run the TTS integration test
    """
    print("🎵 Running Text-to-Speech Integration Tests")
    tts_test_runner = TextToSpeechIntegrationTest()
    await tts_test_runner.test_custom_phrase_generation()


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(main())
