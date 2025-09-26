"""
Parser message constants for consistent user-facing text
"""

class ParserMessages:
    """Constants for parser-generated messages"""
    
    # Item unavailable messages
    ITEM_UNAVAILABLE_TEMPLATE = "Sorry, we don't have {item_name} on our menu"
    
    # Clarification messages
    CLARIFICATION_TEMPLATE = "Did you mean: {options}?"
    
    # Error messages
    EXTRACTION_FAILED = "Failed to extract items from user input"
    RESOLUTION_FAILED = "Failed to resolve items against menu"
    NO_COMMANDS_GENERATED = "No valid commands generated from agent responses"
    PARSING_FAILED = "ADD_ITEM parsing failed: {error}"
    
    # Success messages
    ITEMS_EXTRACTED = "Items extracted successfully"
    ITEMS_RESOLVED = "Items resolved against menu"
    COMMANDS_CREATED = "Commands created successfully"
