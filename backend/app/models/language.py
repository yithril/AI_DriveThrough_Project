"""
Language support for speech processing
"""

from enum import Enum


class Language(str, Enum):
    """
    Supported languages for speech processing
    """
    ENGLISH = "en"
    SPANISH = "es"
    
    @classmethod
    def get_default(cls) -> "Language":
        """Get the default language (English)"""
        return cls.ENGLISH
    
    @classmethod
    def from_code(cls, code: str) -> "Language":
        """Get language from language code"""
        try:
            return cls(code.lower())
        except ValueError:
            return cls.get_default()
    
    @property
    def display_name(self) -> str:
        """Get human-readable language name"""
        names = {
            "en": "English",
            "es": "Spanish"
        }
        return names.get(self.value, "English")
    
    @property
    def whisper_language_code(self) -> str:
        """Get the language code for OpenAI Whisper API"""
        return self.value
    
    @property
    def translation_target(self) -> str:
        """Get the target language for translation (always English)"""
        return "en"
