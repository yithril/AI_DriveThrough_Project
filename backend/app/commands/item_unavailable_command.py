"""
Item Unavailable Command

Command for when a customer requests an item that doesn't exist on the menu.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..constants.audio_phrases import AudioPhraseType
from ..dto.order_result import OrderResult
import logging


class ItemUnavailableCommand(BaseCommand):
    """
    Command for handling unavailable items
    """
    
    def __init__(
        self, 
        restaurant_id: int, 
        order_id: int,
        requested_item: str,
        message: Optional[str] = None
    ):
        """
        Initialize item unavailable command
        
        Args:
            restaurant_id: Restaurant ID
            order_id: Order ID
            requested_item: The item that was requested but is unavailable
            message: Custom message (optional, will generate default if not provided)
        """
        super().__init__(restaurant_id, order_id)
        self.requested_item = requested_item
        self.message = message or f"Sorry, we don't have {requested_item} on our menu"
        self.confidence = 1.0  # Item unavailable commands are always confident
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, context: CommandContext, db: AsyncSession) -> OrderResult:
        """
        Execute the item unavailable command
        
        Args:
            context: Command execution context
            db: Database session
            
        Returns:
            OrderResult: Result indicating item is unavailable
        """
        try:
            # Log the unavailable item request
            self.logger.info(f"Item unavailable: {self.requested_item}")
            print(f"\n🔍 DEBUG - ITEM UNAVAILABLE COMMAND EXECUTE:")
            print(f"   Requested item: {self.requested_item}")
            print(f"   Message: {self.message}")
            
            # Return success result indicating item is not available (this is a successful response to user)
            result = OrderResult.success(
                message=self.message,
                data={
                    "response_type": "item_unavailable",
                    "requested_item": self.requested_item,
                    "phrase_type": AudioPhraseType.ITEM_UNAVAILABLE
                }
            )
            
            print(f"   Result: {result}")
            print(f"   Result is_success: {result.is_success}")
            print(f"   Result data: {result.data}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Item unavailable command execution failed: {e}")
            print(f"   Exception: {e}")
            return OrderResult.error(f"Failed to process unavailable item request: {str(e)}")
    
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
