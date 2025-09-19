"""
Greeting phrases for drive-thru interactions
"""

import random
from typing import List


def get_greeting_phrases() -> List[str]:
    """Get greeting phrases - short and focused"""
    return [
        "Welcome to {restaurant}, may I take your order?",
        "Hi! What can I get for you today?",
        "Hello! What would you like to order?",
        "Welcome! What sounds good?",
        "Hi there! What can I get started for you?"
    ]


def get_thinking_phrases() -> List[str]:
    """Get phrases for when customer is thinking - short and encouraging"""
    return [
        "Take your time!",
        "No rush!",
        "I'm here when you're ready.",
        "Let me know when you're ready.",
        "Take your time deciding."
    ]


def get_still_there_phrases() -> List[str]:
    """Get phrases for when customer hasn't responded - clear and direct"""
    return [
        "Are you still there?",
        "Hello? Are you ready to order?",
        "Are you still with me?",
        "Hello? I'm here when you're ready.",
        "Are you ready to order?"
    ]


def get_menu_question_phrases() -> List[str]:
    """Get phrases for answering menu questions - helpful and concise"""
    return [
        "I can help you with that!",
        "I'd be happy to help!",
        "Let me help you with that.",
        "I can answer that for you.",
        "I'd be glad to help!"
    ]


def get_random_greeting_phrase() -> str:
    """Get a random greeting phrase"""
    phrases = get_greeting_phrases()
    return random.choice(phrases)


def get_random_thinking_phrase() -> str:
    """Get a random thinking phrase"""
    phrases = get_thinking_phrases()
    return random.choice(phrases)


def get_random_still_there_phrase() -> str:
    """Get a random still there phrase"""
    phrases = get_still_there_phrases()
    return random.choice(phrases)


def get_random_menu_question_phrase() -> str:
    """Get a random menu question phrase"""
    phrases = get_menu_question_phrases()
    return random.choice(phrases)


def get_canned_phrases() -> dict:
    """Get standard canned phrases for audio generation"""
    return {
        "greeting": "Welcome to {restaurant}, may I take your order?",
        "come_again": "I'm sorry, I didn't catch that. Could you please repeat your order?",
        "thank_you": "Thank you! Please pull forward to the window.",
        "upsell_1": "Would you like to try our special today?",
        "upsell_2": "Can I interest you in our combo meal?",
        "upsell_3": "Would you like to add a drink to your order?",
        "order_confirm": "Is that correct?",
        "order_complete": "Perfect! Your order is ready."
    }


def get_upsell_phrases() -> List[str]:
    """Get upsell phrases for random selection"""
    return [
        "Would you like to try our special today?",
        "Can I interest you in our combo meal?",
        "Would you like to add a drink to your order?"
    ]


def get_random_upsell_phrase() -> str:
    """Get a random upsell phrase"""
    phrases = get_upsell_phrases()
    return random.choice(phrases)
