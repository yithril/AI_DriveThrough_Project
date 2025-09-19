"""
Error phrases for handling various error situations
"""

import random
from typing import List


def get_error_phrases() -> List[str]:
    """Get general error phrases"""
    return [
        "I'm sorry, I didn't understand that.",
        "I'm having trouble understanding. Could you try again?",
        "I'm sorry, I didn't catch that.",
        "I'm having trouble hearing you. Could you repeat that?",
        "I'm sorry, I missed that. Could you say it again?",
        "I'm having trouble understanding. What did you say?",
        "I'm sorry, I didn't get that.",
        "I'm having trouble hearing you. Could you try again?",
        "I'm sorry, I missed that.",
        "I'm having trouble understanding. Could you repeat that?"
    ]


def get_out_of_stock_phrases() -> List[str]:
    """Get phrases for out of stock items"""
    return [
        "I'm sorry, we're out of that item.",
        "Unfortunately, we don't have that available right now.",
        "I'm sorry, we're sold out of that.",
        "We don't have that item available at the moment.",
        "I'm sorry, that's not available right now.",
        "Unfortunately, we're out of that item.",
        "We don't have that in stock right now.",
        "I'm sorry, that item is not available.",
        "Unfortunately, we're sold out of that item.",
        "We don't have that available right now."
    ]


def get_alternative_phrases() -> List[str]:
    """Get phrases for suggesting alternatives"""
    return [
        "Would you like something else instead?",
        "Can I suggest something else?",
        "What else would you like?",
        "Is there something else you'd like?",
        "Would you like to try something else?",
        "Can I get you something else?",
        "What else sounds good?",
        "Is there something else I can get you?",
        "Would you like to try something different?",
        "What else would you like to order?"
    ]


def get_system_error_phrases() -> List[str]:
    """Get phrases for system errors"""
    return [
        "I'm having some technical difficulties. Please hold on.",
        "I'm experiencing some issues. Please bear with me.",
        "I'm having trouble with my system. Please wait a moment.",
        "I'm having some technical problems. Please hold on.",
        "I'm experiencing some difficulties. Please bear with me.",
        "I'm having trouble with my system. Please wait.",
        "I'm having some technical issues. Please hold on.",
        "I'm experiencing some problems. Please bear with me.",
        "I'm having trouble with my system. Please wait a moment.",
        "I'm having some technical difficulties. Please hold on."
    ]


def get_payment_error_phrases() -> List[str]:
    """Get phrases for payment errors"""
    return [
        "I'm having trouble with the payment system. Please try again.",
        "There's an issue with the payment. Please try again.",
        "I'm having trouble processing the payment. Please try again.",
        "There's a problem with the payment system. Please try again.",
        "I'm having trouble with the payment. Please try again.",
        "There's an issue with the payment system. Please try again.",
        "I'm having trouble processing the payment. Please try again.",
        "There's a problem with the payment. Please try again.",
        "I'm having trouble with the payment system. Please try again.",
        "There's an issue with the payment. Please try again."
    ]


def get_human_handoff_phrases() -> List[str]:
    """Get phrases for human handoff"""
    return [
        "I'm having trouble. Please pull forward to the first window for assistance.",
        "I'm having some difficulties. Please pull forward for help.",
        "I'm having trouble. Please pull forward to the first window.",
        "I'm having some issues. Please pull forward for assistance.",
        "I'm having trouble. Please pull forward to the first window for help.",
        "I'm having some difficulties. Please pull forward to the first window.",
        "I'm having trouble. Please pull forward for assistance.",
        "I'm having some issues. Please pull forward to the first window.",
        "I'm having trouble. Please pull forward to the first window for help.",
        "I'm having some difficulties. Please pull forward for assistance."
    ]


def get_random_error_phrase() -> str:
    """Get a random error phrase"""
    phrases = get_error_phrases()
    return random.choice(phrases)


def get_random_out_of_stock_phrase() -> str:
    """Get a random out of stock phrase"""
    phrases = get_out_of_stock_phrases()
    return random.choice(phrases)


def get_random_alternative_phrase() -> str:
    """Get a random alternative phrase"""
    phrases = get_alternative_phrases()
    return random.choice(phrases)


def get_random_system_error_phrase() -> str:
    """Get a random system error phrase"""
    phrases = get_system_error_phrases()
    return random.choice(phrases)


def get_random_payment_error_phrase() -> str:
    """Get a random payment error phrase"""
    phrases = get_payment_error_phrases()
    return random.choice(phrases)


def get_random_human_handoff_phrase() -> str:
    """Get a random human handoff phrase"""
    phrases = get_human_handoff_phrases()
    return random.choice(phrases)
