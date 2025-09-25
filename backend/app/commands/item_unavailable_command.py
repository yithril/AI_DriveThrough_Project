"""
Item Unavailable Command

Command for when a customer requests an item that doesn't exist on the menu.
"""

from typing import Dict, Any, Optional
from .base_command import BaseCommand
from .command_context import CommandContext
from ..constants.audio_phrases import AudioPhraseType


class ItemUnavailableCommand(BaseCommand):
    """
    Command for handling unavailable items
    """
    
    def __init__(self, command_data: Dict[str, Any]):
        super().__init__(command_data)
        self.requested_item = command_data.get("slots", {}).get("requested_item", "item")
        self.message = command_data.get("slots", {}).get("message", f"Sorry, we don't have {self.requested_item} on our menu")
    
    async def execute(self, context: CommandContext) -> Dict[str, Any]:
        """
        Execute the item unavailable command
        
        Args:
            context: Command execution context
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Log the unavailable item request
            self.logger.info(f"Item unavailable: {self.requested_item}")
            
            # Return response indicating item is not available
            return {
                "success": True,
                "response_type": "item_unavailable",
                "phrase_type": AudioPhraseType.ITEM_UNAVAILABLE,
                "response_text": self.message,
                "confidence": self.confidence,
                "requested_item": self.requested_item
            }
            
        except Exception as e:
            self.logger.error(f"Item unavailable command execution failed: {e}")
            return {
                "success": False,
                "response_type": "error",
                "phrase_type": AudioPhraseType.DIDNT_UNDERSTAND,
                "response_text": "I'm sorry, I had trouble processing your request. Could you please try again?",
                "confidence": 0.0
            }
    
    def validate(self) -> bool:
        """
        Validate the command data
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not self.requested_item:
                self.logger.warning("Item unavailable command missing requested_item")
                return False
            
            # Check confidence
            if self.confidence < 0.0 or self.confidence > 1.0:
                self.logger.warning(f"Item unavailable command has invalid confidence: {self.confidence}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Item unavailable command validation failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert command to dictionary
        
        Returns:
            Dictionary representation of the command
        """
        return {
            "intent": "ITEM_UNAVAILABLE",
            "confidence": self.confidence,
            "slots": {
                "requested_item": self.requested_item,
                "message": self.message
            }
        }
