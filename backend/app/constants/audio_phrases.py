"""
Audio phrase constants for canned audio generation
"""
from enum import Enum
from typing import Dict, List
from app.core.config import settings


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
    
    # State machine specific phrases
    ORDER_SUMMARY = "order_summary"
    ORDER_REPEAT = "order_repeat"
    CONTINUE_ORDERING = "continue_ordering"
    NO_ORDER_YET = "no_order_yet"
    TAKE_YOUR_TIME = "take_your_time"
    READY_TO_ORDER = "ready_to_order"
    ADD_ITEMS_FIRST = "add_items_first"
    HOW_CAN_I_HELP = "how_can_i_help"
    DIDNT_UNDERSTAND = "didnt_understand"
    ORDER_READY = "order_ready"
    ORDER_ALREADY_CONFIRMED = "order_already_confirmed"
    DRIVE_TO_WINDOW = "drive_to_window"
    ORDER_BEING_PREPARED = "order_being_prepared"
    CANT_HELP_RIGHT_NOW = "cant_help_right_now"
    WELCOME_MENU = "welcome_menu"
    ORDER_CORRECT = "order_correct"
    ORDER_NOT_UNDERSTOOD = "order_not_understood"
    ORDER_PREPARED_WINDOW = "order_prepared_window"
    
    # Command-specific success phrases
    ITEM_ADDED_SUCCESS = "item_added_success"
    ITEM_REMOVED_SUCCESS = "item_removed_success" 
    ITEM_UPDATED_SUCCESS = "item_updated_success"
    ORDER_CLEARED_SUCCESS = "order_cleared_success"
    NOTHING_TO_REPEAT = "nothing_to_repeat"
    SYSTEM_ERROR_RETRY = "system_error_retry"
    
    # Dynamic phrases (require custom text)
    CUSTOM_RESPONSE = "custom_response"
    CLARIFICATION_QUESTION = "clarification_question"
    ERROR_MESSAGE = "error_message"
    LLM_GENERATED = "llm_generated"


class AudioPhraseConstants:
    """Constants for audio phrase generation and storage"""
    
    # Standard voice for all canned audio (configurable via TTS_VOICE env var)
    STANDARD_VOICE = settings.TTS_VOICE
    
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
            AudioPhraseType.SCREEN_CONFIRM: "Does everything on your screen look correct?",
            
            # State machine specific phrases
            AudioPhraseType.ORDER_SUMMARY: "Let me confirm your order: [order summary]",
            AudioPhraseType.ORDER_REPEAT: "Here's your current order: [order summary]",
            AudioPhraseType.CONTINUE_ORDERING: "No problem! What else would you like to order?",
            AudioPhraseType.NO_ORDER_YET: "You don't have an order yet. What would you like to order?",
            AudioPhraseType.TAKE_YOUR_TIME: "Take your time! Let me know when you're ready to order.",
            AudioPhraseType.READY_TO_ORDER: "I'm here when you're ready to order!",
            AudioPhraseType.ADD_ITEMS_FIRST: "Please add some items to your order first.",
            AudioPhraseType.HOW_CAN_I_HELP: "What can I help you with today?",
            AudioPhraseType.DIDNT_UNDERSTAND: "I'm sorry, I didn't understand. Could you please try again?",
            AudioPhraseType.ORDER_READY: "Here's your order: [order summary]. Is this correct?",
            AudioPhraseType.ORDER_ALREADY_CONFIRMED: "Your order is already confirmed and being prepared!",
            AudioPhraseType.DRIVE_TO_WINDOW: "Drive up to the next window please!",
            AudioPhraseType.ORDER_BEING_PREPARED: "Your order is already being prepared. Is there anything else I can help you with?",
            AudioPhraseType.CANT_HELP_RIGHT_NOW: "I'm sorry, I can't help with that right now. Please let me know what you'd like to order.",
            AudioPhraseType.WELCOME_MENU: f"Welcome to {restaurant_name or '{restaurant}'}! Take your time looking at our menu.",
            AudioPhraseType.ORDER_CORRECT: "Is this order correct?",
            AudioPhraseType.ORDER_NOT_UNDERSTOOD: "I'm sorry, I didn't understand. Is this order correct?",
            AudioPhraseType.ORDER_PREPARED_WINDOW: "Your order: [order summary] is being prepared. Drive up to the next window!",
            
            # Command-specific success phrases
            AudioPhraseType.ITEM_ADDED_SUCCESS: "Added that to your order. Would you like anything else?",
            AudioPhraseType.ITEM_REMOVED_SUCCESS: "Removed that from your order. Would you like anything else?",
            AudioPhraseType.ITEM_UPDATED_SUCCESS: "Updated your item. Would you like anything else?",
            AudioPhraseType.ORDER_CLEARED_SUCCESS: "Your order has been cleared.",
            AudioPhraseType.NOTHING_TO_REPEAT: "There's nothing to repeat yet.",
            AudioPhraseType.SYSTEM_ERROR_RETRY: "I'm sorry, I'm having some technical difficulties. Please try again.",
            
            # Dynamic phrases (fallback text - usually overridden with custom_text)
            AudioPhraseType.CUSTOM_RESPONSE: "Custom response",
            AudioPhraseType.CLARIFICATION_QUESTION: "I need more information to help you.",
            AudioPhraseType.ERROR_MESSAGE: "I'm sorry, there was an error processing your request.",
            AudioPhraseType.LLM_GENERATED: "LLM generated response"
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
