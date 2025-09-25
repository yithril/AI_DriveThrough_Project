"""
Command type schema for system commands.

This defines the types of commands the system can execute,
separate from customer intents.
"""

from enum import Enum


class CommandType(Enum):
    """Types of commands the system can execute."""
    
    # Core order commands
    ADD_ITEM = "ADD_ITEM"
    REMOVE_ITEM = "REMOVE_ITEM"
    MODIFY_ITEM = "MODIFY_ITEM"
    SET_QUANTITY = "SET_QUANTITY"
    CLEAR_ORDER = "CLEAR_ORDER"
    CONFIRM_ORDER = "CONFIRM_ORDER"
    
    # Response commands
    QUESTION = "QUESTION"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    ITEM_UNAVAILABLE = "ITEM_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
