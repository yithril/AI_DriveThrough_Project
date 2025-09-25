"""
Unit tests for MenuService with cache integration
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.menu_service import MenuService
from app.services.menu_cache_interface import MenuCacheInterface
from app.models.menu_item import MenuItem


class MockMenuCacheService(MenuCacheInterface):
    """Mock menu cache service for testing"""
    
    def __init__(self, cache_data=None, available_items=None, search_results=None):
        self.cache_data = cache_data or []
        self.available_items = available_items or []
        self.search_results = search_results or []
        self.cache_available = True
    
    async def get_menu_items(self, restaurant_id: int):
        return self.cache_data
    
    async def get_menu_item_by_id(self, restaurant_id: int, menu_item_id: int):
        for item in self.cache_data:
            if item.id == menu_item_id:
                return item
        return None
    
    async def search_menu_items(self, restaurant_id: int, query: str):
        return self.search_results
    
    async def get_available_items(self, restaurant_id: int):
        return self.available_items
    
    async def cache_menu_items(self, restaurant_id: int, menu_items):
        self.cache_data = menu_items
        self.available_items = [item.name for item in menu_items if item.is_available]
    
    async def invalidate_restaurant_cache(self, restaurant_id: int):
        self.cache_data = []
        self.available_items = []
    
    async def invalidate_all_cache(self):
        self.cache_data = []
        self.available_items = []
    
    async def is_cache_available(self):
        return self.cache_available


class TestMenuService:
    """Test MenuService with cache integration"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service"""
        return MockMenuCacheService()
    
    @pytest.fixture
    def menu_service_with_cache(self, mock_db, mock_cache_service):
        """MenuService with cache service"""
        return MenuService(mock_db, mock_cache_service)
    
    @pytest.fixture
    def menu_service_without_cache(self, mock_db):
        """MenuService without cache service"""
        return MenuService(mock_db, None)
    
    @pytest.fixture
    def sample_menu_items(self):
        """Sample menu items for testing"""
        return [
            MenuItem(
                id=1,
                name="Cheeseburger",
                description="Classic cheeseburger with lettuce and tomato",
                price=8.99,
                is_available=True,
                restaurant_id=1,
                category_id=1
            ),
            MenuItem(
                id=2,
                name="French Fries",
                description="Crispy golden french fries",
                price=3.99,
                is_available=True,
                restaurant_id=1,
                category_id=1
            ),
            MenuItem(
                id=3,
                name="Chicken Sandwich",
                description="Grilled chicken sandwich",
                price=9.99,
                is_available=False,  # Not available
                restaurant_id=1,
                category_id=1
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_available_items_with_cache_hit(self, menu_service_with_cache, sample_menu_items):
        """Test getting available items when cache has data"""
        # Setup cache with data
        menu_service_with_cache.cache_service.available_items = ["Cheeseburger", "French Fries"]
        
        result = await menu_service_with_cache.get_available_items_for_restaurant(1)
        
        assert result == ["Cheeseburger", "French Fries"]
        # Should not hit database
        menu_service_with_cache.db.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_available_items_with_cache_miss(self, menu_service_with_cache, sample_menu_items):
        """Test getting available items when cache is empty (fallback to DB)"""
        # Setup cache with no data
        menu_service_with_cache.cache_service.available_items = []
        
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await menu_service_with_cache.get_available_items_for_restaurant(1)
            
            # Should return available items from database
            expected_items = [item.name for item in sample_menu_items if item.is_available]
            assert result == expected_items
            assert "Cheeseburger" in result
            assert "French Fries" in result
            assert "Chicken Sandwich" not in result  # Not available
    
    @pytest.mark.asyncio
    async def test_get_available_items_without_cache(self, menu_service_without_cache, sample_menu_items):
        """Test getting available items when no cache service is provided"""
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await menu_service_without_cache.get_available_items_for_restaurant(1)
            
            # Should return available items from database
            expected_items = [item.name for item in sample_menu_items if item.is_available]
            assert result == expected_items
    
    @pytest.mark.asyncio
    async def test_get_available_items_cache_error_fallback(self, menu_service_with_cache, sample_menu_items):
        """Test getting available items when cache throws error (fallback to DB)"""
        # Setup cache to throw error
        menu_service_with_cache.cache_service.cache_available = False
        
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await menu_service_with_cache.get_available_items_for_restaurant(1)
            
            # Should fallback to database
            expected_items = [item.name for item in sample_menu_items if item.is_available]
            assert result == expected_items
    
    @pytest.mark.asyncio
    async def test_search_menu_items_with_cache_hit(self, menu_service_with_cache):
        """Test searching menu items when cache has data"""
        # Setup cache with search results
        search_results = [
            MenuItem(id=1, name="Cheeseburger", description="Classic burger", price=8.99, is_available=True, restaurant_id=1, category_id=1)
        ]
        menu_service_with_cache.cache_service.search_results = search_results
        
        result = await menu_service_with_cache.search_menu_items(1, "burger")
        
        assert result == ["Cheeseburger"]
        # Should not hit database
        menu_service_with_cache.db.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_menu_items_with_cache_miss(self, menu_service_with_cache, sample_menu_items):
        """Test searching menu items when cache is empty (fallback to DB)"""
        # Setup cache with no data
        menu_service_with_cache.cache_service.search_results = []
        
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await menu_service_with_cache.search_menu_items(1, "burger")
            
            # Should return matching items from database
            assert "Cheeseburger" in result
            assert "French Fries" not in result
    
    @pytest.mark.asyncio
    async def test_search_menu_items_without_cache(self, menu_service_without_cache, sample_menu_items):
        """Test searching menu items when no cache service is provided"""
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await menu_service_without_cache.search_menu_items(1, "burger")
            
            # Should return matching items from database
            assert "Cheeseburger" in result
    
    @pytest.mark.asyncio
    async def test_get_restaurant_name(self, menu_service_with_cache):
        """Test getting restaurant name"""
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_restaurant = Mock()
            mock_restaurant.name = "Test Restaurant"
            mock_uow_instance.restaurants.get_by_id = AsyncMock(return_value=mock_restaurant)
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            
            result = await menu_service_with_cache.get_restaurant_name(1)
            
            assert result == "Test Restaurant"
    
    @pytest.mark.asyncio
    async def test_get_restaurant_name_not_found(self, menu_service_with_cache):
        """Test getting restaurant name when restaurant not found"""
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.restaurants.get_by_id = AsyncMock(return_value=None)
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            
            result = await menu_service_with_cache.get_restaurant_name(999)
            
            assert result == "Restaurant"
    
    @pytest.mark.asyncio
    async def test_get_menu_categories(self, menu_service_with_cache):
        """Test getting menu categories"""
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            # Create proper mock categories
            burger_category = Mock()
            burger_category.name = "Burgers"
            burger_category.is_active = True
            
            fries_category = Mock()
            fries_category.name = "Fries"
            fries_category.is_active = True
            
            drinks_category = Mock()
            drinks_category.name = "Drinks"
            drinks_category.is_active = False
            
            mock_categories = [burger_category, fries_category, drinks_category]
            mock_uow_instance.categories.get_by_restaurant = AsyncMock(return_value=mock_categories)
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            
            result = await menu_service_with_cache.get_menu_categories(1)
            
            assert result == ["Burgers", "Fries"]
            assert "Drinks" not in result  # Inactive category
    
    @pytest.mark.asyncio
    async def test_get_menu_items_by_category(self, menu_service_with_cache, sample_menu_items):
        """Test getting menu items organized by category"""
        # Mock database response
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            # Create proper mock category
            burger_category = Mock()
            burger_category.id = 1
            burger_category.name = "Burgers"
            burger_category.is_active = True
            
            mock_categories = [burger_category]
            mock_uow_instance.categories.get_by_restaurant = AsyncMock(return_value=mock_categories)
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            
            result = await menu_service_with_cache.get_menu_items_by_category(1)
            
            # Should organize items by category
            assert "Burgers" in result
            assert "Cheeseburger" in result["Burgers"]
            assert "French Fries" in result["Burgers"]
            assert "Chicken Sandwich" not in result["Burgers"]  # Not available
    
    @pytest.mark.asyncio
    async def test_get_menu_summary(self, menu_service_with_cache):
        """Test getting menu summary"""
        # Mock get_menu_items_by_category response
        with patch.object(menu_service_with_cache, 'get_menu_items_by_category') as mock_get_items:
            mock_get_items.return_value = {
                "Burgers": ["Cheeseburger", "Chicken Burger", "Veggie Burger"],
                "Fries": ["French Fries", "Sweet Potato Fries"]
            }
            
            result = await menu_service_with_cache.get_menu_summary(1)
            
            assert "Burgers" in result
            assert "Fries" in result
            assert "Cheeseburger" in result
    
    @pytest.mark.asyncio
    async def test_get_menu_summary_empty(self, menu_service_with_cache):
        """Test getting menu summary when no items available"""
        # Mock get_menu_items_by_category response
        with patch.object(menu_service_with_cache, 'get_menu_items_by_category') as mock_get_items:
            mock_get_items.return_value = {}
            
            result = await menu_service_with_cache.get_menu_summary(1)
            
            assert result == "No menu items available"
    
    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, menu_service_with_cache):
        """Test error handling when database fails"""
        # Mock database to raise exception
        with patch('app.core.unit_of_work.UnitOfWork') as mock_uow:
            mock_uow.side_effect = Exception("Database connection failed")
            
            # Should return empty list instead of crashing
            result = await menu_service_with_cache.get_available_items_for_restaurant(1)
            assert result == []
            
            result = await menu_service_with_cache.search_menu_items(1, "burger")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_cache_service_integration(self, menu_service_with_cache):
        """Test that MenuService properly integrates with cache service"""
        # Verify cache service is set
        assert menu_service_with_cache.cache_service is not None
        
        # Test cache service methods are called
        await menu_service_with_cache.cache_service.get_available_items(1)
        await menu_service_with_cache.cache_service.search_menu_items(1, "test")
        
        # Should not raise any errors
        assert True
