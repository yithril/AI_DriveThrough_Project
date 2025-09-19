"""
Canned phrases for drive-thru conversations
"""

from .clarification import get_clarification_phrases
from .confirmation import get_confirmation_phrases
from .greeting import get_greeting_phrases
from .error import get_error_phrases
from .thinking import get_thinking_phrases

__all__ = [
    "get_clarification_phrases",
    "get_confirmation_phrases", 
    "get_greeting_phrases",
    "get_error_phrases",
    "get_thinking_phrases"
]
