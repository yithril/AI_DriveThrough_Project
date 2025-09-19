"""
Configuration for speech integration tests
Easily add new test files here
"""

from app.models.language import Language


# Test file configurations
# Add new test files by adding entries to this list
TEST_FILES = [
    {
        "filename": "test_recording_1.m4a",
        "language": Language.ENGLISH,
        "description": "Basic English test recording"
    },
    # Add more test files here:
    # {
    #     "filename": "test_recording_2.m4a", 
    #     "language": Language.SPANISH,
    #     "description": "Spanish test recording"
    # },
    # {
    #     "filename": "test_recording_3.webm",
    #     "language": Language.ENGLISH,
    #     "description": "WebM format test"
    # },
    # {
    #     "filename": "noisy_environment.m4a",
    #     "language": Language.ENGLISH,
    #     "description": "Test with background noise"
    # },
    # {
    #     "filename": "long_order.m4a",
    #     "language": Language.ENGLISH,
    #     "description": "Complex order with multiple items"
    # }
]


def get_test_files():
    """
    Get the list of configured test files
    """
    return TEST_FILES


def add_test_file(filename: str, language: Language, description: str):
    """
    Add a new test file to the configuration
    """
    TEST_FILES.append({
        "filename": filename,
        "language": language,
        "description": description
    })


def get_supported_formats():
    """
    Get list of supported audio formats for reference
    """
    return [
        "m4a",  # Apple audio format (Sound Recorder default)
        "mp3",  # Standard audio format
        "wav",  # Uncompressed audio
        "webm", # Web audio format
        "mp4",  # MP4 audio container
        "mpeg"  # MPEG audio
    ]
