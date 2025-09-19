"""
Thinking phrases for when customer is browsing or thinking
"""

import random
from typing import List


def get_thinking_phrases() -> List[str]:
    """Get phrases for when customer is thinking"""
    return [
        "Take your time! I'll be here when you're ready.",
        "No rush! Let me know when you're ready to order.",
        "Take your time looking at the menu.",
        "I'm here when you're ready to order.",
        "No hurry! Take your time.",
        "Let me know when you're ready.",
        "I'll be here when you're ready to order.",
        "Take your time deciding.",
        "No rush! I'm here when you're ready.",
        "Let me know when you've decided."
    ]


def get_menu_browsing_phrases() -> List[str]:
    """Get phrases for when customer is browsing the menu"""
    return [
        "I'm here when you're ready to order.",
        "Let me know when you're ready.",
        "I'll be here when you're ready to order.",
        "Take your time looking at the menu.",
        "Let me know when you're ready to order.",
        "I'm here when you're ready.",
        "Take your time deciding.",
        "Let me know when you're ready to order.",
        "I'll be here when you're ready to order.",
        "Take your time looking at the menu."
    ]


def get_waiting_phrases() -> List[str]:
    """Get phrases for when customer is waiting"""
    return [
        "I'm here when you're ready.",
        "Let me know when you're ready to order.",
        "I'll be here when you're ready to order.",
        "Take your time.",
        "Let me know when you're ready.",
        "I'm here when you're ready to order.",
        "Take your time deciding.",
        "Let me know when you're ready to order.",
        "I'll be here when you're ready to order.",
        "Take your time."
    ]


def get_menu_help_phrases() -> List[str]:
    """Get phrases for offering menu help"""
    return [
        "I can help you with our menu if you have any questions.",
        "Let me know if you have any questions about our menu.",
        "I can help you with any menu questions you might have.",
        "Feel free to ask if you have any questions about our menu.",
        "I can help you with our menu if you need anything.",
        "Let me know if you need help with our menu.",
        "I can help you with any questions about our menu.",
        "Feel free to ask if you have any menu questions.",
        "I can help you with our menu if you have questions.",
        "Let me know if you need help with our menu."
    ]


def get_random_thinking_phrase() -> str:
    """Get a random thinking phrase"""
    phrases = get_thinking_phrases()
    return random.choice(phrases)


def get_random_menu_browsing_phrase() -> str:
    """Get a random menu browsing phrase"""
    phrases = get_menu_browsing_phrases()
    return random.choice(phrases)


def get_random_waiting_phrase() -> str:
    """Get a random waiting phrase"""
    phrases = get_waiting_phrases()
    return random.choice(phrases)


def get_random_menu_help_phrase() -> str:
    """Get a random menu help phrase"""
    phrases = get_menu_help_phrases()
    return random.choice(phrases)
