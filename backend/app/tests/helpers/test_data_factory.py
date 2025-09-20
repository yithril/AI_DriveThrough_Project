"""
Test data factory for creating test objects and scenarios
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def create_menu_item(
        id: int = 1,
        name: str = "Test Burger",
        price: float = 9.99,
        description: str = "A delicious test burger",
        is_available: bool = True,
        restaurant_id: int = 1
    ) -> Dict[str, Any]:
        """Create a test menu item"""
        return {
            "id": id,
            "name": name,
            "price": price,
            "description": description,
            "is_available": is_available,
            "restaurant_id": restaurant_id
        }
    
    @staticmethod
    def create_order_item(
        id: str = "item_1234567890_1234",
        menu_item_id: int = 1,
        quantity: int = 1,
        unit_price: float = 9.99,
        customizations: Optional[List[str]] = None,
        special_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a test order item"""
        return {
            "id": id,
            "menu_item_id": menu_item_id,
            "menu_item": TestDataFactory.create_menu_item(menu_item_id),
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": unit_price * quantity,
            "customizations": customizations or [],
            "special_instructions": special_instructions,
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_empty_order(
        order_id: str = "order_123",
        restaurant_id: int = 1
    ) -> Dict[str, Any]:
        """Create an empty test order"""
        return {
            "id": order_id,
            "restaurant_id": restaurant_id,
            "items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_order_with_items(
        order_id: str = "order_123",
        restaurant_id: int = 1,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a test order with items"""
        if items is None:
            items = [
                TestDataFactory.create_order_item("item_1", 1, 2, 9.99),
                TestDataFactory.create_order_item("item_2", 2, 1, 4.99)
            ]
        
        # Calculate totals
        subtotal = sum(item["total_price"] for item in items)
        tax_amount = 0.0  # No taxes for now
        total_amount = subtotal + tax_amount
        
        return {
            "id": order_id,
            "restaurant_id": restaurant_id,
            "items": items,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_ingredient(
        id: int = 1,
        name: str = "Lettuce",
        description: str = "Fresh lettuce",
        allergen_type: Optional[str] = None,
        is_allergen: bool = False,
        unit_cost: float = 0.0,
        restaurant_id: int = 1
    ) -> Dict[str, Any]:
        """Create a test ingredient"""
        return {
            "id": id,
            "name": name,
            "description": description,
            "allergen_type": allergen_type,
            "is_allergen": is_allergen,
            "unit_cost": unit_cost,
            "restaurant_id": restaurant_id
        }
    
    @staticmethod
    def create_menu_item_ingredient(
        id: int = 1,
        menu_item_id: int = 1,
        ingredient_id: int = 1,
        quantity: float = 1.0,
        unit: str = "piece",
        additional_cost: float = 0.0
    ) -> Dict[str, Any]:
        """Create a test menu item ingredient relationship"""
        return {
            "id": id,
            "menu_item_id": menu_item_id,
            "ingredient_id": ingredient_id,
            "quantity": quantity,
            "unit": unit,
            "additional_cost": additional_cost
        }
    
    @staticmethod
    def create_inventory(
        id: int = 1,
        ingredient_id: int = 1,
        current_stock: float = 100.0,
        unit: str = "piece",
        is_low_stock: bool = False,
        low_stock_threshold: float = 10.0,
        restaurant_id: int = 1
    ) -> Dict[str, Any]:
        """Create a test inventory record"""
        return {
            "id": id,
            "ingredient_id": ingredient_id,
            "current_stock": current_stock,
            "unit": unit,
            "is_low_stock": is_low_stock,
            "low_stock_threshold": low_stock_threshold,
            "restaurant_id": restaurant_id
        }
    
    @staticmethod
    def create_order_scenarios() -> Dict[str, Dict[str, Any]]:
        """Create different order scenarios for testing"""
        return {
            "empty_order": TestDataFactory.create_empty_order(),
            "single_item_order": TestDataFactory.create_order_with_items(
                items=[TestDataFactory.create_order_item("item_1", 1, 1, 9.99)]
            ),
            "multiple_items_order": TestDataFactory.create_order_with_items(
                items=[
                    TestDataFactory.create_order_item("item_1", 1, 2, 9.99),  # $19.98
                    TestDataFactory.create_order_item("item_2", 2, 1, 4.99)   # $4.99
                ]
            ),
            "confirmed_order": {
                **TestDataFactory.create_order_with_items(),
                "status": "CONFIRMED",
                "confirmed_at": datetime.now().isoformat()
            },
            "large_order": TestDataFactory.create_order_with_items(
                items=[
                    TestDataFactory.create_order_item(f"item_{i}", i, 5, 10.0) 
                    for i in range(1, 11)  # 10 items, 5 quantity each = 50 total items
                ]
            ),
            "high_value_order": TestDataFactory.create_order_with_items(
                items=[
                    TestDataFactory.create_order_item("item_1", 1, 1, 150.0),  # $150
                    TestDataFactory.create_order_item("item_2", 2, 1, 40.0)    # $40
                ]
            )
        }
