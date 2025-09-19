"""
Confirmation phrases for order confirmation and completion
"""

import random
from typing import List


def get_confirmation_phrases() -> List[str]:
    """Get phrases for asking if order is complete"""
    return [
        "Will that complete your order?",
        "Is that everything?",
        "Anything else?",
        "What else can I get you?",
        "Is there anything else?",
        "Would you like anything else?",
        "Can I get you anything else?",
        "What else would you like?",
        "Is that all?",
        "Anything more?",
        "What else can I help you with?",
        "Is that your complete order?",
        "Are you all set?",
        "Is that everything for you?",
        "What else can I get for you?"
    ]


def get_order_summary_phrases() -> List[str]:
    """Get phrases for summarizing the order"""
    return [
        "Let me confirm your order:",
        "So you have:",
        "Your order is:",
        "I have:",
        "You ordered:",
        "Here's what I have:",
        "Your order includes:",
        "I've got:",
        "You're getting:",
        "Here's your order:"
    ]


def get_final_confirmation_phrases() -> List[str]:
    """Get phrases for final order confirmation"""
    return [
        "Is that correct?",
        "Does that sound right?",
        "Is that what you wanted?",
        "Does that look good?",
        "Is that everything you wanted?",
        "Does that sound correct?",
        "Is that right?",
        "Does that match what you wanted?",
        "Is that your complete order?",
        "Does that sound good to you?"
    ]


def get_order_complete_phrases() -> List[str]:
    """Get phrases for when order is complete"""
    return [
        "Perfect! Your order is complete.",
        "Great! That's everything.",
        "Excellent! Your order is ready.",
        "Perfect! I have everything you need.",
        "Great! Your order is all set.",
        "Excellent! That's your complete order.",
        "Perfect! You're all set.",
        "Great! Your order is complete.",
        "Excellent! That's everything you wanted.",
        "Perfect! Your order is ready to go."
    ]


def get_thank_you_phrases() -> List[str]:
    """Get thank you phrases"""
    return [
        "Thank you!",
        "Thanks!",
        "Thank you very much!",
        "Thanks so much!",
        "Appreciate it!",
        "Thank you for your order!",
        "Thanks for choosing us!",
        "Thank you for coming!",
        "We appreciate your business!",
        "Thank you for your patience!"
    ]


def get_pull_forward_phrases() -> List[str]:
    """Get phrases for directing customer to pull forward"""
    return [
        "Please pull forward to the first window.",
        "Go ahead and pull forward.",
        "Please drive up to the first window.",
        "Pull forward to the first window, please.",
        "Go ahead and pull up to the first window.",
        "Please pull up to the first window.",
        "Drive forward to the first window.",
        "Pull forward to the first window when you're ready.",
        "Go ahead and pull forward to the first window.",
        "Please pull up to the first window."
    ]


def get_random_confirmation_phrase() -> str:
    """Get a random confirmation phrase"""
    phrases = get_confirmation_phrases()
    return random.choice(phrases)


def get_random_order_summary_phrase() -> str:
    """Get a random order summary phrase"""
    phrases = get_order_summary_phrases()
    return random.choice(phrases)


def get_random_final_confirmation_phrase() -> str:
    """Get a random final confirmation phrase"""
    phrases = get_final_confirmation_phrases()
    return random.choice(phrases)


def get_random_order_complete_phrase() -> str:
    """Get a random order complete phrase"""
    phrases = get_order_complete_phrases()
    return random.choice(phrases)


def get_random_thank_you_phrase() -> str:
    """Get a random thank you phrase"""
    phrases = get_thank_you_phrases()
    return random.choice(phrases)


def get_random_pull_forward_phrase() -> str:
    """Get a random pull forward phrase"""
    phrases = get_pull_forward_phrases()
    return random.choice(phrases)
