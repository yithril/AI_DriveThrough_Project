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
    
    @staticmethod
    def create_batch_result_scenarios() -> Dict[str, Any]:
        """Create different batch result scenarios for testing"""
        from app.dto.order_result import OrderResult, OrderResultStatus, ErrorCategory, ErrorCode, CommandBatchResult, ResponsePayload
        
        # Item not found scenario
        item_not_found_result = OrderResult.business_error(
            message="Chocolate pie not found",
            errors=["Item 'chocolate pie' is not available"],
            error_code=ErrorCode.ITEM_NOT_FOUND
        )
        
        item_not_found_batch = CommandBatchResult.from_results(
            results=[item_not_found_result],
            command_family="ADD_ITEM",
            batch_outcome="ALL_FAILED",
            first_error_code="ITEM_NOT_FOUND",
            response_payload=ResponsePayload(
                enum_key="ITEM_NOT_FOUND",
                args={"failed_item": "chocolate pie"},
                telemetry={"error_count": 1}
            )
        )
        
        # Partial success scenario - Quantum Burger succeeds, Churros fails
        success_result = OrderResult.success(
            message="Quantum Burger added to order",
            data={"item_name": "Quantum Burger", "quantity": 1}
        )
        
        failed_result = OrderResult.business_error(
            message="Churros not found",
            errors=["Item 'churros' is not available"],
            error_code=ErrorCode.ITEM_NOT_FOUND
        )
        
        partial_success_batch = CommandBatchResult.from_results(
            results=[success_result, failed_result],
            command_family="ADD_ITEM",
            batch_outcome="PARTIAL_SUCCESS_ASK",
            first_error_code="ITEM_NOT_FOUND",
            response_payload=ResponsePayload(
                enum_key="PARTIAL_SUCCESS_ASK",
                args={"successful_items": ["Quantum Burger"], "failed_items": ["churros"]},
                telemetry={"success_count": 1, "error_count": 1}
            )
        )
        
        # Size not available scenario
        size_error_result = OrderResult.business_error(
            message="Large size not available for chocolate pie",
            errors=["Size 'large' is not available for this item"],
            error_code=ErrorCode.SIZE_NOT_AVAILABLE
        )
        
        size_error_batch = CommandBatchResult.from_results(
            results=[size_error_result],
            command_family="ADD_ITEM",
            batch_outcome="ALL_FAILED",
            first_error_code="SIZE_NOT_AVAILABLE",
            response_payload=ResponsePayload(
                enum_key="SIZE_NOT_AVAILABLE",
                args={"item": "chocolate pie", "requested_size": "large"},
                telemetry={"error_count": 1}
            )
        )
        
        # Quantity exceeds limit scenario
        quantity_error_result = OrderResult.business_error(
            message="Quantity exceeds limit for water bottles",
            errors=["Maximum quantity of 10 allowed per item. You requested 10,000 water bottles."],
            error_code=ErrorCode.QUANTITY_EXCEEDS_LIMIT
        )
        
        quantity_error_batch = CommandBatchResult.from_results(
            results=[quantity_error_result],
            command_family="ADD_ITEM",
            batch_outcome="ALL_FAILED",
            first_error_code="QUANTITY_EXCEEDS_LIMIT",
            response_payload=ResponsePayload(
                enum_key="QUANTITY_EXCEEDS_LIMIT",
                args={"item": "water bottles", "requested_quantity": 10000, "max_quantity": 10},
                telemetry={"error_count": 1}
            )
        )
        
        # Modifier conflict scenario
        modifier_conflict_result = OrderResult.business_error(
            message="Conflicting modifiers for hamburger",
            errors=["Cannot have both 'extra meat' and 'no meat' on the same item"],
            error_code=ErrorCode.MODIFIER_CONFLICT
        )
        
        modifier_conflict_batch = CommandBatchResult.from_results(
            results=[modifier_conflict_result],
            command_family="ADD_ITEM",
            batch_outcome="ALL_FAILED",
            first_error_code="MODIFIER_CONFLICT",
            response_payload=ResponsePayload(
                enum_key="MODIFIER_CONFLICT",
                args={"item": "hamburger", "conflicting_modifiers": ["extra meat", "no meat"]},
                telemetry={"error_count": 1}
            )
        )
        
        # No substitutes scenario - completely inappropriate item
        no_substitutes_result = OrderResult.business_error(
            message="Shark fin soup not available",
            errors=["Item 'shark fin soup' is not available at this restaurant"],
            error_code=ErrorCode.ITEM_NOT_FOUND
        )
        
        no_substitutes_batch = CommandBatchResult.from_results(
            results=[no_substitutes_result],
            command_family="ADD_ITEM",
            batch_outcome="ALL_FAILED",
            first_error_code="ITEM_NOT_FOUND",
            response_payload=ResponsePayload(
                enum_key="ITEM_NOT_FOUND",
                args={"failed_item": "shark fin soup"},
                telemetry={"error_count": 1}
            )
        )
        
        # Multi-item mixed results scenario
        success_result_1 = OrderResult.success(
            message="Quantum Burger with extra onions added to order",
            data={"item_name": "Quantum Burger", "modifiers": ["extra onions"]}
        )
        
        success_result_2 = OrderResult.success(
            message="Strawberry Milkshake added to order",
            data={"item_name": "Strawberry Milkshake", "quantity": 1}
        )
        
        failed_result = OrderResult.business_error(
            message="Waffle fries not available",
            errors=["Item 'waffle fries' is not available"],
            error_code=ErrorCode.ITEM_NOT_FOUND
        )
        
        multi_item_mixed_batch = CommandBatchResult.from_results(
            results=[success_result_1, success_result_2, failed_result],
            command_family="ADD_ITEM",
            batch_outcome="PARTIAL_SUCCESS_ASK",
            first_error_code="ITEM_NOT_FOUND",
            response_payload=ResponsePayload(
                enum_key="PARTIAL_SUCCESS_ASK",
                args={"successful_items": ["Quantum Burger with extra onions", "Strawberry Milkshake"], "failed_items": ["waffle fries"]},
                telemetry={"success_count": 2, "error_count": 1}
            )
        )
        
        # Option required missing scenario
        option_missing_result = OrderResult.business_error(
            message="Size required for coke",
            errors=["Please specify size: small, medium, or large"],
            error_code=ErrorCode.OPTION_REQUIRED_MISSING
        )
        
        option_missing_batch = CommandBatchResult.from_results(
            results=[option_missing_result],
            command_family="ADD_ITEM",
            batch_outcome="ALL_FAILED",
            first_error_code="OPTION_REQUIRED_MISSING",
            response_payload=ResponsePayload(
                enum_key="OPTION_REQUIRED_MISSING",
                args={"item": "coke", "missing_option": "size", "available_options": ["small", "medium", "large"]},
                telemetry={"error_count": 1}
            )
        )
        
        return {
            "item_not_found": item_not_found_batch,
            "partial_success": partial_success_batch,
            "size_not_available": size_error_batch,
            "quantity_exceeds_limit": quantity_error_batch,
            "modifier_conflict": modifier_conflict_batch,
            "no_substitutes": no_substitutes_batch,
            "multi_item_mixed_results": multi_item_mixed_batch,
            "option_required_missing": option_missing_batch
        }