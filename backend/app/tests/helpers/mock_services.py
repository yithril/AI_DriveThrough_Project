"""
Mock services for testing
"""

from typing import Dict, Any, Optional
from unittest.mock import AsyncMock


class MockOrderSessionService:
    """Mock OrderSessionService for testing"""
    
    def __init__(self):
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None
    
    async def get_order(self, db, order_id: str) -> Optional[Dict[str, Any]]:
        """Mock get order - returns stored order or None"""
        return self.orders.get(order_id)
    
    async def update_order(self, db, order_id: str, order_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """Mock update order - stores the order data"""
        self.orders[order_id] = order_data
        return True
    
    async def create_order(self, db, order_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """Mock create order - stores the order data"""
        self.orders[order_data["id"]] = order_data
        return True
    
    async def delete_order(self, db, order_id: str) -> bool:
        """Mock delete order - removes from storage"""
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False
    
    async def is_redis_available(self) -> bool:
        """Mock Redis availability - always returns True for testing"""
        return True
    
    async def get_current_session_id(self) -> Optional[str]:
        """Mock get current session ID"""
        return self.current_session_id
    
    async def set_current_session_id(self, session_id: str, ttl: int) -> bool:
        """Mock set current session ID"""
        self.current_session_id = session_id
        return True
    
    async def clear_current_session_id(self) -> bool:
        """Mock clear current session ID"""
        self.current_session_id = None
        return True


class MockUnitOfWork:
    """Mock UnitOfWork for testing"""
    
    def __init__(self, db=None):
        self.menu_items = MockMenuItemsRepository()
        self.menu_item_ingredients = MockMenuItemIngredientsRepository()
        self.inventory = MockInventoryRepository()
        self.ingredients = MockIngredientsRepository()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockMenuItemsRepository:
    """Mock MenuItemsRepository for testing"""
    
    def __init__(self):
        self.menu_items = {
            1: {
                "id": 1,
                "name": "Test Burger",
                "price": 9.99,
                "description": "A delicious test burger",
                "is_available": True,
                "restaurant_id": 1
            },
            2: {
                "id": 2,
                "name": "Test Fries",
                "price": 4.99,
                "description": "Crispy test fries",
                "is_available": True,
                "restaurant_id": 1
            },
            3: {
                "id": 3,
                "name": "Unavailable Item",
                "price": 5.99,
                "description": "This item is not available",
                "is_available": False,
                "restaurant_id": 1
            }
        }
    
    async def get_by_id(self, menu_item_id: int):
        """Mock get menu item by ID"""
        menu_item_data = self.menu_items.get(menu_item_id)
        if not menu_item_data:
            return None
        
        # Return a mock object with the data
        mock_item = AsyncMock()
        for key, value in menu_item_data.items():
            setattr(mock_item, key, value)
        return mock_item


class MockMenuItemIngredientsRepository:
    """Mock MenuItemIngredientsRepository for testing"""
    
    def __init__(self):
        from .test_data_factory import TestDataFactory
        self.menu_item_ingredients = {
            1: [TestDataFactory.create_menu_item_ingredient(1, 1, 1, 1.0, "piece", 0.0)],
            2: [TestDataFactory.create_menu_item_ingredient(2, 2, 2, 1.0, "piece", 0.0)]
        }
    
    async def get_by_menu_item(self, menu_item_id: int):
        """Mock get menu item ingredients by menu item ID"""
        ingredients_data = self.menu_item_ingredients.get(menu_item_id, [])
        
        # Return mock objects with the data
        mock_ingredients = []
        for ingredient_data in ingredients_data:
            mock_ingredient = AsyncMock()
            for key, value in ingredient_data.items():
                setattr(mock_ingredient, key, value)
            mock_ingredients.append(mock_ingredient)
        
        return mock_ingredients


class MockInventoryRepository:
    """Mock InventoryRepository for testing"""
    
    def __init__(self):
        from .test_data_factory import TestDataFactory
        self.inventories = {
            1: TestDataFactory.create_inventory(1, 1, 100.0, "piece", False, 10.0, 1),
            2: TestDataFactory.create_inventory(2, 2, 50.0, "piece", False, 10.0, 1),
            3: TestDataFactory.create_inventory(3, 3, 5.0, "piece", True, 10.0, 1)  # Low stock
        }
    
    async def get_by_ingredient(self, ingredient_id: int):
        """Mock get inventory by ingredient ID"""
        inventory_data = self.inventories.get(ingredient_id)
        if not inventory_data:
            return None
        
        # Return a mock object with the data
        mock_inventory = AsyncMock()
        for key, value in inventory_data.items():
            setattr(mock_inventory, key, value)
        return mock_inventory


class MockIngredientsRepository:
    """Mock IngredientsRepository for testing"""
    
    def __init__(self):
        from .test_data_factory import TestDataFactory
        self.ingredients = {
            1: TestDataFactory.create_ingredient(1, "Lettuce", "Fresh lettuce", None, False, 0.0, 1),
            2: TestDataFactory.create_ingredient(2, "Tomato", "Fresh tomato", None, False, 0.0, 1),
            3: TestDataFactory.create_ingredient(3, "Cheese", "Cheddar cheese", "dairy", True, 0.5, 1),
            4: TestDataFactory.create_ingredient(4, "Bacon", "Crispy bacon", None, False, 1.5, 1),
            5: TestDataFactory.create_ingredient(5, "Mustard", "Yellow mustard", None, False, 0.0, 1)
        }
    
    async def get_by_name_and_restaurant(self, name: str, restaurant_id: int):
        """Mock get ingredient by name and restaurant ID"""
        # Find ingredient by name (case insensitive)
        for ingredient_data in self.ingredients.values():
            if ingredient_data["name"].lower() == name.lower() and ingredient_data["restaurant_id"] == restaurant_id:
                # Return a mock object with the data
                mock_ingredient = AsyncMock()
                for key, value in ingredient_data.items():
                    setattr(mock_ingredient, key, value)
                return mock_ingredient
        
        return None
    
    async def get_by_id(self, ingredient_id: int):
        """Mock get ingredient by ID"""
        ingredient_data = self.ingredients.get(ingredient_id)
        if not ingredient_data:
            return None
        
        # Return a mock object with the data
        mock_ingredient = AsyncMock()
        for key, value in ingredient_data.items():
            setattr(mock_ingredient, key, value)
        return mock_ingredient


class MockCustomizationValidationService:
    """Mock CustomizationValidationService for testing"""
    
    def __init__(self):
        pass
    
    async def validate_customizations(self, menu_item_id: int, customizations: list, restaurant_id: int, uow):
        """Mock validate customizations - always returns valid for testing"""
        from app.services.customization_validation_service import ValidationResult
        
        results = {}
        for customization in customizations:
            results[customization] = ValidationResult(
                is_valid=True,
                message=f"Mock validation passed for {customization}",
                extra_cost=0.0,
                errors=[]
            )
        
        return results


class MockOrderService:
    """Mock OrderService for testing"""
    
    def __init__(self):
        pass
    
    async def add_item_to_order(self, db, order_id: str, menu_item_id: int, quantity: int, 
                               customizations=None, special_instructions=None, size=None):
        """Mock add item to order - behaves like real OrderService"""
        from app.dto.order_result import OrderResult
        
        # Simulate real service behavior: return error for non-existent items
        if menu_item_id == 999:  # Non-existent item
            return OrderResult.error(f"Menu item {menu_item_id} not found or not available")
        
        if menu_item_id == 3:  # Unavailable item
            return OrderResult.error(f"Menu item {menu_item_id} not found or not available")
        
        # Create realistic order item data
        order_item = {
            "id": f"item_{menu_item_id}_{quantity}",
            "menu_item_id": menu_item_id,
            "menu_item": {
                "id": menu_item_id,
                "name": "Test Burger",
                "price": 8.99,
                "restaurant_id": 1
            },
            "quantity": quantity,
            "unit_price": 8.99,
            "extra_cost": 0.0,  # Will be calculated by real service
            "total_price": 8.99 * quantity,
            "customizations": customizations or [],
            "special_instructions": special_instructions,
            "size": size,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        # Generate comprehensive message like real service
        item_name = "Test Burger"
        size_text = f" {size}" if size and size.lower() not in item_name.lower() else ""
        customizations_text = f" ({', '.join(customizations)})" if customizations else ""
        special_text = f" - {special_instructions}" if special_instructions else ""
        message = f"Added {quantity}x {item_name}{size_text}{customizations_text} to order{special_text}"
        
        return OrderResult.success(message, data={"order_item": order_item})


class MockContainer:
    """Mock container that provides services with mocked dependencies"""
    
    def __init__(self):
        """Initialize mock container with mocked services"""
        # Create mock services
        self.mock_order_session_service = MockOrderSessionService()
        self.mock_customization_validator = MockCustomizationValidationService()
        self.mock_order_service = MockOrderService()
        
        # Use mock OrderService instead of real one
        self._order_service = self.mock_order_service
    
    def order_service(self):
        """Get the mocked OrderService"""
        return self._order_service
    
    def order_session_service(self):
        """Get the mock OrderSessionService"""
        return self.mock_order_session_service
    
    def customization_validator(self):
        """Get the mock CustomizationValidationService"""
        return self.mock_customization_validator
    
    def get_db(self):
        """Mock database session generator"""
        async def mock_db_generator():
            # Return a mock database session
            mock_session = AsyncMock()
            yield mock_session
        
        return mock_db_generator()
    
    def get_db_mock(self):
        """Get the mock database session for testing"""
        return AsyncMock()
    
    def unit_of_work(self, db_session):
        """Mock UnitOfWork factory"""
        return MockUnitOfWork(db_session)
    
    # Legacy methods for backward compatibility
    def get_order_service(self):
        """Get the mocked OrderService"""
        return self._order_service
    
    def get_mock_order_session_service(self):
        """Get the mock OrderSessionService for test setup"""
        return self.mock_order_session_service
    
    def get_mock_customization_validator(self):
        """Get the mock CustomizationValidationService for test setup"""
        return self.mock_customization_validator
