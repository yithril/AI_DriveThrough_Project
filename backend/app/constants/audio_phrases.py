"""
Audio phrase constants for canned audio generation
"""
from enum import Enum
from typing import Dict, List


class AudioPhraseType(Enum):
    """Types of audio phrases"""
    GREETING = "greeting"
    COME_AGAIN = "come_again"
    THANK_YOU = "thank_you"
    UPSELL_1 = "upsell_1"
    UPSELL_2 = "upsell_2"
    UPSELL_3 = "upsell_3"
    SUGGESTION_1 = "suggestion_1"
    SUGGESTION_2 = "suggestion_2"
    SUGGESTION_3 = "suggestion_3"
    ORDER_CONFIRM = "order_confirm"
    ORDER_COMPLETE = "order_complete"
    SCREEN_CONFIRM = "screen_confirm"


class AudioPhraseConstants:
    """Constants for audio phrase generation and storage"""
    
    # Standard voice for all canned audio
    STANDARD_VOICE = "nova"
    
    # Audio file format
    AUDIO_FORMAT = "mp3"
    
    # Blob storage paths
    AUDIO_BASE_PATH = "audio/canned"
    
    # File naming pattern: {phrase_type}_{restaurant_slug}.mp3
    FILE_PATTERN = "{phrase_type}_{restaurant_slug}.{format}"
    
    # TTL for cached audio (24 hours)
    CACHE_TTL = 86400
    
    @staticmethod
    def get_phrase_text(phrase_type: AudioPhraseType, restaurant_name: str = None) -> str:
        """Get the text for a specific phrase type"""
        phrases = {
            AudioPhraseType.GREETING: f"Welcome to {restaurant_name or '{restaurant}'}, may I take your order?",
            AudioPhraseType.COME_AGAIN: "I'm sorry, I didn't catch that. Could you please repeat your order?",
            AudioPhraseType.THANK_YOU: "Thank you! Please pull forward to the window.",
            AudioPhraseType.UPSELL_1: "Would you like to try our special today?",
            AudioPhraseType.UPSELL_2: "Can I interest you in our combo meal?",
            AudioPhraseType.UPSELL_3: "Would you like to add a drink to your order?",
            AudioPhraseType.SUGGESTION_1: "Would you like to try our special today?",
            AudioPhraseType.SUGGESTION_2: "Can I interest you in our combo meal?",
            AudioPhraseType.SUGGESTION_3: "Would you like to add a drink to your order?",
            AudioPhraseType.ORDER_CONFIRM: "Is that correct?",
            AudioPhraseType.ORDER_COMPLETE: "Perfect! Your order is ready.",
            AudioPhraseType.SCREEN_CONFIRM: "Does everything on your screen look correct?"
        }
        return phrases.get(phrase_type, "")
    
    @staticmethod
    def get_all_phrase_types() -> List[AudioPhraseType]:
        """Get all available phrase types"""
        return list(AudioPhraseType)
    
    @staticmethod
    def get_filename(phrase_type: AudioPhraseType, restaurant_slug: str) -> str:
        """Generate filename for a phrase type and restaurant"""
        return AudioPhraseConstants.FILE_PATTERN.format(
            phrase_type=phrase_type.value,
            restaurant_slug=restaurant_slug,
            format=AudioPhraseConstants.AUDIO_FORMAT
        )
    
    @staticmethod
    def get_blob_path(phrase_type: AudioPhraseType, restaurant_slug: str) -> str:
        """Generate blob storage path for a phrase"""
        filename = AudioPhraseConstants.get_filename(phrase_type, restaurant_slug)
        return f"{AudioPhraseConstants.AUDIO_BASE_PATH}/{filename}"
