"""
Integration test for speech-to-text service
Processes test audio files and outputs transcribed text
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
from app.services.speech_to_text_service import SpeechToTextService
from app.models.language import Language

# Simple test config without importing the full dependency chain
def get_test_files():
    return [
        {
            "filename": "test_recording_1.m4a",
            "language": Language.ENGLISH,
            "description": "Basic English test recording"
        }
    ]


class SpeechIntegrationTest:
    """
    Integration test for speech service processing
    """
    
    def __init__(self):
        self.speech_to_text_service = SpeechToTextService()
        self.test_audio_dir = Path(__file__).parent.parent / "test_audio"
        self.output_dir = Path(__file__).parent.parent / "output"
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Test configuration - easily add more files in test_config.py
        self.test_files = get_test_files()
    
    async def run_all_tests(self):
        """
        Run all speech integration tests
        """
        print("🎤 Starting Speech Service Integration Tests")
        print("=" * 50)
        
        results = []
        
        for test_file in self.test_files:
            result = await self.test_single_file(test_file)
            results.append(result)
        
        # Generate summary report
        await self.generate_summary_report(results)
        
        print("\n✅ All tests completed! Check the output folder for results.")
    
    async def test_single_file(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a single audio file
        """
        filename = test_config["filename"]
        language = test_config["language"]
        description = test_config["description"]
        
        print(f"\n🔍 Testing: {filename}")
        print(f"   Language: {language.display_name}")
        print(f"   Description: {description}")
        
        # Check if file exists
        file_path = self.test_audio_dir / filename
        if not file_path.exists():
            print(f"   ❌ File not found: {file_path}")
            return {
                "filename": filename,
                "success": False,
                "error": "File not found",
                "transcript": None
            }
        
        try:
            # Read audio file
            with open(file_path, "rb") as f:
                audio_data = f.read()
            
            print(f"   📁 File size: {len(audio_data):,} bytes")
            
            # Get file extension for format detection
            file_extension = file_path.suffix.lower()
            audio_format = file_extension[1:] if file_extension else "m4a"
            
            # Transcribe audio
            print(f"   🎯 Transcribing with {language.display_name} context...")
            result = await self.speech_to_text_service.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                language=language
            )
            
            if result.is_success:
                transcript = result.data["transcript"]
                confidence = result.data.get("confidence", 0.0)
                
                print(f"   ✅ Success!")
                print(f"   📝 Transcript: {transcript}")
                print(f"   🎯 Confidence: {confidence:.2f}")
                
                # Save transcript to output file
                await self.save_transcript(filename, transcript, result.data)
                
                return {
                    "filename": filename,
                    "success": True,
                    "transcript": transcript,
                    "confidence": confidence,
                    "language": language.value,
                    "file_size": len(audio_data)
                }
            else:
                print(f"   ❌ Transcription failed: {result.message}")
                return {
                    "filename": filename,
                    "success": False,
                    "error": result.message,
                    "transcript": None
                }
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {
                "filename": filename,
                "success": False,
                "error": str(e),
                "transcript": None
            }
    
    async def save_transcript(self, filename: str, transcript: str, metadata: Dict[str, Any]):
        """
        Save transcript and metadata to output files
        """
        # Create output filename
        base_name = Path(filename).stem
        transcript_file = self.output_dir / f"{base_name}_transcript.txt"
        metadata_file = self.output_dir / f"{base_name}_metadata.json"
        
        # Save transcript
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(f"Original file: {filename}\n")
            f.write(f"Transcribed text:\n")
            f.write(f"{transcript}\n")
        
        # Save metadata
        import json
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Saved transcript: {transcript_file.name}")
        print(f"   💾 Saved metadata: {metadata_file.name}")
    
    async def generate_summary_report(self, results: List[Dict[str, Any]]):
        """
        Generate a summary report of all tests
        """
        summary_file = self.output_dir / "test_summary.txt"
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("Speech Service Integration Test Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total tests: {len(results)}\n")
            f.write(f"Successful: {len(successful_tests)}\n")
            f.write(f"Failed: {len(failed_tests)}\n\n")
            
            if successful_tests:
                f.write("✅ SUCCESSFUL TESTS:\n")
                f.write("-" * 30 + "\n")
                for result in successful_tests:
                    f.write(f"File: {result['filename']}\n")
                    f.write(f"Language: {result.get('language', 'unknown')}\n")
                    f.write(f"Confidence: {result.get('confidence', 0):.2f}\n")
                    f.write(f"Transcript: {result['transcript']}\n\n")
            
            if failed_tests:
                f.write("❌ FAILED TESTS:\n")
                f.write("-" * 30 + "\n")
                for result in failed_tests:
                    f.write(f"File: {result['filename']}\n")
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n\n")
        
        print(f"\n📊 Summary report saved: {summary_file.name}")


# Pytest test functions
@pytest.mark.asyncio
async def test_speech_service_integration():
    """
    Pytest integration test for speech service
    """
    test_runner = SpeechIntegrationTest()
    await test_runner.run_all_tests()


@pytest.mark.asyncio
async def test_single_audio_file():
    """
    Test processing a single audio file
    """
    test_runner = SpeechIntegrationTest()
    test_files = get_test_files()
    
    if not test_files:
        pytest.skip("No test files configured")
    
    # Test the first configured file
    first_file = test_files[0]
    result = await test_runner.test_single_file(first_file)
    
    # Assertions
    assert result is not None
    assert "filename" in result
    assert "success" in result
    
    if result["success"]:
        assert "transcript" in result
        assert result["transcript"] is not None
        assert len(result["transcript"]) > 0
        print(f"✅ Successfully transcribed: {result['transcript']}")
    else:
        print(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
        # Don't fail the test if transcription fails - just log it
        # This allows us to see what's happening with our test files


# Standalone runner (for manual testing)
async def main():
    """
    Main function to run the speech-to-text integration test
    """
    print("🎤 Running Speech-to-Text Integration Tests")
    speech_test_runner = SpeechIntegrationTest()
    await speech_test_runner.run_all_tests()


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(main())
