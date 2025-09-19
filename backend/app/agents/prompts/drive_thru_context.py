"""
Drive-thru context prompts for speech processing
"""

def get_drive_thru_context() -> str:
    """
    Create context prompt optimized for drive-thru environment
    Helps Whisper understand common phrases and filter background noise
    """
    return """This is audio from a drive-thru restaurant. Common phrases include:
    - "I want", "Can I get", "I'll have", "I'd like"
    - "No cheese", "Extra lettuce", "Well done", "Medium rare"
    - "Combo", "Meal", "Large", "Small", "Medium"
    - "How much", "What's the total", "That's all"
    - "Drive through", "Pick up", "To go"
    Background noise may include: cars, wind, children, music, other customers.
    Focus on the customer's order, ignore background noise."""


def get_restaurant_context(restaurant_name: str = None, menu_items: list = None) -> str:
    """
    Create context prompt with restaurant-specific menu items
    """
    base_context = get_drive_thru_context()
    
    if restaurant_name:
        base_context += f"\nRestaurant: {restaurant_name}"
    
    if menu_items:
        base_context += f"\nMenu items: {', '.join(menu_items[:15])}"
    
    return base_context
