"""
Clarification phrases for when the AI needs to ask for clarification
"""

import random
from typing import List


def get_clarification_phrases() -> List[str]:
    """Get random clarification phrases"""
    return [
        "I didn't quite catch that. Could you repeat that?",
        "Sorry, I didn't understand. What would you like?",
        "I'm not sure I heard that right. Could you say that again?",
        "Could you repeat that for me?",
        "I didn't get that. What did you say?",
        "Sorry, what was that?",
        "I didn't catch that. Could you try again?",
        "Could you speak a little clearer?",
        "I'm having trouble hearing you. What would you like?",
        "Sorry, I missed that. Could you repeat it?"
    ]


def get_specific_clarification_phrases() -> List[str]:
    """Get phrases for specific clarification needs"""
    return [
        "Which size would you like?",
        "What size did you want?",
        "Small, medium, or large?",
        "Did you want the small or large?",
        "What size drink?",
        "Which burger did you want?",
        "What kind of burger?",
        "Which combo number?",
        "What number combo?",
        "Did you want the #1 or #2?",
        "Which meal did you want?",
        "What meal number?",
        "Did you want fries with that?",
        "Would you like fries?",
        "Do you want a drink with that?",
        "What drink would you like?",
        "Which drink?",
        "Coke, Sprite, or something else?",
        "What kind of drink?",
        "Did you want anything else?"
    ]


def get_menu_help_phrases() -> List[str]:
    """Get phrases for menu help"""
    return [
        "I can help you with our menu. What are you looking for?",
        "What would you like to know about our menu?",
        "I can tell you about our burgers, combos, or drinks. What interests you?",
        "Our most popular items are the Big Mac, Quarter Pounder, and Chicken McNuggets. What sounds good?",
        "We have burgers, chicken, salads, and breakfast items. What are you in the mood for?",
        "I can help you find something on our menu. What are you craving?",
        "What kind of food are you looking for?",
        "Are you looking for something specific?",
        "What can I help you find?",
        "What sounds good to you?"
    ]


def get_start_order_phrases() -> List[str]:
    """Get phrases for when customer hasn't started ordering yet"""
    return [
        "I don't have anything in your order yet. What would you like to start with?",
        "What would you like to order?",
        "What can I get for you?",
        "What would you like?",
        "What sounds good?",
        "What are you in the mood for?",
        "What can I get started for you?",
        "What would you like to try?",
        "What looks good to you?",
        "What can I help you with?"
    ]


def get_random_clarification_phrase() -> str:
    """Get a random clarification phrase"""
    phrases = get_clarification_phrases()
    return random.choice(phrases)


def get_random_specific_clarification_phrase() -> str:
    """Get a random specific clarification phrase"""
    phrases = get_specific_clarification_phrases()
    return random.choice(phrases)


def get_random_menu_help_phrase() -> str:
    """Get a random menu help phrase"""
    phrases = get_menu_help_phrases()
    return random.choice(phrases)


def get_random_start_order_phrase() -> str:
    """Get a random start order phrase"""
    phrases = get_start_order_phrases()
    return random.choice(phrases)
