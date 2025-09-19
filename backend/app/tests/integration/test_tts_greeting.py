"""
Integration test for TTS greeting generation
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
from app.services.tts_service import TTSService
from app.services.tts_provider import OpenAITTSProvider
from app.agents.phrases.greeting import (
    get_random_greeting_phrase,
    get_random_thinking_phrase,
    get_random_still_there_phrase,
    get_random_menu_question_phrase
)


class TTSIntegrationTest:
    """
    Integration test for TTS service
    """
    
    def __init__(self):
        # Create TTS service directly (avoiding container for now)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        provider = OpenAITTSProvider(api_key)
        self.tts_service = TTSService(provider)
        
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    async def run_all_tests(self):
        """
        Run all TTS integration tests
        """
        # Starting TTS Service Integration Tests
        
        results = []
        
        # Test different voices
        voices = ["nova", "alloy", "echo", "fable", "onyx", "shimmer"]
        
        for voice in voices:
            result = await self.test_voice_greeting(voice)
            results.append(result)
        
        # Test agent phrases
        result = await self.test_agent_phrases()
        results.append(result)
        
        # Generate summary report
        await self.generate_summary_report(results)
        
        # All tests completed! Check the output folder for results.
    
    async def test_voice_greeting(self, voice: str) -> Dict[str, Any]:
        """
        Test greeting generation with a specific voice
        """
        # Testing voice: {voice}
        
        try:
            # Generate greeting audio
            audio_chunks = []
            async for chunk in self.tts_service.generate_greeting_audio(car_number=5, voice=voice):
                audio_chunks.append(chunk)
            
            # Combine all chunks
            audio_data = b''.join(audio_chunks)
            
            # Save to file
            output_file = self.output_dir / f"greeting_{voice}.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            # Success! File saved
            
            return {
                "voice": voice,
                "success": True,
                "file_size": len(audio_data),
                "output_file": str(output_file)
            }
            
        except Exception as e:
            return {
                "voice": voice,
                "success": False,
                "error": str(e)
            }


    async def test_agent_phrases(self) -> Dict[str, Any]:
        """
        Test agent phrase generation
        """
        # Testing agent phrases
        
        try:
            # Test different agent phrases
            phrases = [
                ("greeting", get_random_greeting_phrase()),
                ("thinking", get_random_thinking_phrase()),
                ("still_there", get_random_still_there_phrase()),
                ("menu_question", get_random_menu_question_phrase())
            ]
            
            results = []
            for phrase_type, text in phrases:
                # Generating {phrase_type}: '{text}'
                
                # Generate audio
                audio_chunks = []
                async for chunk in self.tts_service.generate_audio_stream(text, voice="nova"):
                    audio_chunks.append(chunk)
                
                # Save to file
                audio_data = b''.join(audio_chunks)
                output_file = self.output_dir / f"agent_{phrase_type}.mp3"
                
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                
                # Saved {phrase_type}
                
                results.append({
                    "phrase_type": phrase_type,
                    "text": text,
                    "success": True,
                    "file_size": len(audio_data),
                    "output_file": str(output_file)
                })
            
            return {
                "test_type": "agent_phrases",
                "success": True,
                "results": results
            }
            
        except Exception as e:
            return {
                "test_type": "agent_phrases",
                "success": False,
                "error": str(e)
            }
    
    async def generate_summary_report(self, results: List[Dict[str, Any]]):
        """
        Generate a summary report of all tests
        """
        summary_file = self.output_dir / "tts_test_summary.txt"
        
        successful_tests = [r for r in results if r.get("success", False)]
        failed_tests = [r for r in results if not r.get("success", False)]
        
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("TTS Service Integration Test Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total tests: {len(results)}\n")
            f.write(f"Successful: {len(successful_tests)}\n")
            f.write(f"Failed: {len(failed_tests)}\n\n")
            
            if successful_tests:
                f.write("✅ SUCCESSFUL TESTS:\n")
                f.write("-" * 30 + "\n")
                for result in successful_tests:
                    if "voice" in result:
                        f.write(f"Voice: {result['voice']}\n")
                        f.write(f"File size: {result.get('file_size', 0):,} bytes\n")
                        f.write(f"Output: {result.get('output_file', 'N/A')}\n\n")
                    elif "test_type" in result:
                        f.write(f"Test type: {result['test_type']}\n")
                        f.write(f"Results: {len(result.get('results', []))} phrases\n\n")
            
            if failed_tests:
                f.write("❌ FAILED TESTS:\n")
                f.write("-" * 30 + "\n")
                for result in failed_tests:
                    f.write(f"Test: {result.get('voice', result.get('test_type', 'unknown'))}\n")
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n\n")
        
        # Summary report saved


# Pytest test functions
@pytest.mark.asyncio
async def test_tts_service_integration():
    """
    Pytest integration test for TTS service
    """
    test_runner = TTSIntegrationTest()
    await test_runner.run_all_tests()


@pytest.mark.asyncio
async def test_single_voice():
    """
    Test a single voice generation
    """
    test_runner = TTSIntegrationTest()
    result = await test_runner.test_voice_greeting("nova")
    
    # Assertions
    assert result is not None
    assert "voice" in result
    assert "success" in result
    
    if result["success"]:
        assert "file_size" in result
        assert result["file_size"] > 0
        print(f"✅ Successfully generated audio for voice: {result['voice']}")
    else:
        print(f"❌ Voice generation failed: {result.get('error', 'Unknown error')}")


# Standalone runner (for manual testing)
async def main():
    """
    Main function to run the integration test
    """
    test_runner = TTSIntegrationTest()
    await test_runner.run_all_tests()


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(main())
