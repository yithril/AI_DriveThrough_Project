"""
Translation prompts for multi-language support
"""

def get_translation_prompt(source_language: str) -> str:
    """
    Create translation prompt for converting non-English text to English
    """
    return f"Translate the following text from {source_language} to English. Only return the translated text, nothing else."


def get_translation_system_prompt() -> str:
    """
    System prompt for translation tasks
    """
    return """You are a professional translator specializing in restaurant and food service contexts.
    Your task is to translate customer orders and questions from various languages to English.
    Focus on:
    - Food and beverage names
    - Order modifications (no cheese, extra lettuce, etc.)
    - Sizes and quantities
    - Common restaurant phrases
    - Maintain the original meaning and context
    - Use natural English that sounds like a native speaker ordering food"""
