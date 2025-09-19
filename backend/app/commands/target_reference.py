"""
Target reference system for handling item references in commands
"""

from typing import List, Optional, Dict, Any
from ..models.order_item import OrderItem


class TargetReference:
    """
    Utility class for resolving target references to order items
    Handles references like "last_item", "first_item", "line_1", etc.
    """
    
    @staticmethod
    def resolve_target(
        target_ref: str, 
        order_items: List[OrderItem],
        last_mentioned_item: Optional[OrderItem] = None
    ) -> Optional[OrderItem]:
        """
        Resolve a target reference to an actual order item
        
        Args:
            target_ref: Reference string (e.g., "last_item", "line_1", "burger_123")
            order_items: List of current order items
            last_mentioned_item: Last mentioned item for context
            
        Returns:
            OrderItem or None if reference cannot be resolved
        """
        if not order_items:
            return None
        
        target_ref = target_ref.lower().strip()
        
        # Handle "last_item" or "the last one"
        if target_ref in ["last_item", "last", "the_last_one", "last_one"]:
            return order_items[-1] if order_items else None
        
        # Handle "first_item" or "the first one"
        if target_ref in ["first_item", "first", "the_first_one", "first_one"]:
            return order_items[0] if order_items else None
        
        # Handle "line_X" references (1-indexed)
        if target_ref.startswith("line_"):
            try:
                line_num = int(target_ref.split("_")[1])
                # Convert to 0-indexed
                index = line_num - 1
                if 0 <= index < len(order_items):
                    return order_items[index]
            except (ValueError, IndexError):
                pass
        
        # Handle "item_X" references (1-indexed)
        if target_ref.startswith("item_"):
            try:
                item_num = int(target_ref.split("_")[1])
                # Convert to 0-indexed
                index = item_num - 1
                if 0 <= index < len(order_items):
                    return order_items[index]
            except (ValueError, IndexError):
                pass
        
        # Handle menu item ID references
        if target_ref.startswith("menu_"):
            try:
                menu_id = int(target_ref.split("_")[1])
                for item in order_items:
                    if item.menu_item_id == menu_id:
                        return item
            except (ValueError, IndexError):
                pass
        
        # Handle "that one" or "it" - use last mentioned item
        if target_ref in ["that_one", "that", "it", "the_one"]:
            return last_mentioned_item
        
        # Handle generic item names (partial matching)
        for item in order_items:
            menu_item_name = item.menu_item.name.lower() if item.menu_item else ""
            if target_ref in menu_item_name or menu_item_name in target_ref:
                return item
        
        return None
    
    @staticmethod
    def get_target_candidates(order_items: List[OrderItem]) -> List[Dict[str, Any]]:
        """
        Get list of target candidates for reference resolution
        
        Args:
            order_items: List of current order items
            
        Returns:
            List of candidate dictionaries with reference info
        """
        candidates = []
        
        for i, item in enumerate(order_items):
            candidates.append({
                "line_number": i + 1,
                "item_number": i + 1,
                "menu_item_id": item.menu_item_id,
                "menu_item_name": item.menu_item.name if item.menu_item else "Unknown",
                "quantity": item.quantity,
                "references": [
                    f"line_{i + 1}",
                    f"item_{i + 1}",
                    f"menu_{item.menu_item_id}",
                    "last_item" if i == len(order_items) - 1 else None,
                    "first_item" if i == 0 else None
                ]
            })
        
        # Filter out None references
        for candidate in candidates:
            candidate["references"] = [ref for ref in candidate["references"] if ref is not None]
        
        return candidates
    
    @staticmethod
    def validate_target_ref(target_ref: str, order_items: List[OrderItem]) -> bool:
        """
        Validate if a target reference can be resolved
        
        Args:
            target_ref: Reference string to validate
            order_items: List of current order items
            
        Returns:
            True if reference can be resolved, False otherwise
        """
        return TargetReference.resolve_target(target_ref, order_items) is not None
