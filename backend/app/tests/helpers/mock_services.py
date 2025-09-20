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
