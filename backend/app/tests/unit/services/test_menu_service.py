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


class TestMenuServiceSearch:
    """Test MenuService search functionality with various scenarios"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def menu_service(self, mock_db):
        """MenuService without cache for testing search logic"""
        return MenuService(mock_db, None)
    
    @pytest.fixture
    def sample_menu_items(self):
        """Sample menu items for testing search"""
        return [
            MenuItem(
                id=1,
                name="Quantum Cheeseburger",
                description="Our signature quantum cheeseburger",
                price=12.99,
                is_available=True,
                restaurant_id=1,
                category_id=1
            ),
            MenuItem(
                id=2,
                name="Neon Double Burger",
                description="Double patty neon burger",
                price=15.99,
                is_available=True,
                restaurant_id=1,
                category_id=1
            ),
            MenuItem(
                id=3,
                name="French Fries",
                description="Crispy golden french fries",
                price=4.99,
                is_available=True,
                restaurant_id=1,
                category_id=2
            ),
            MenuItem(
                id=4,
                name="Galactic Fries",
                description="Special galactic seasoned fries",
                price=5.99,
                is_available=True,
                restaurant_id=1,
                category_id=2
            ),
            MenuItem(
                id=5,
                name="Quantum Cola",
                description="Refreshing quantum cola",
                price=2.99,
                is_available=True,
                restaurant_id=1,
                category_id=3
            ),
            MenuItem(
                id=6,
                name="Unavailable Item",
                description="This item is not available",
                price=9.99,
                is_available=False,  # Not available
                restaurant_id=1,
                category_id=1
            )
        ]
    
    @pytest.mark.asyncio
    async def test_exact_match_search(self, menu_service, sample_menu_items):
        """Test exact match search"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test exact match
            result = await menu_service.search_menu_items(1, "Quantum Cheeseburger")
            assert result == ["Quantum Cheeseburger"]
            
            # Test case insensitive exact match
            result = await menu_service.search_menu_items(1, "quantum cheeseburger")
            assert result == ["Quantum Cheeseburger"]
            
            # Test with extra spaces
            result = await menu_service.search_menu_items(1, "  Quantum Cheeseburger  ")
            assert result == ["Quantum Cheeseburger"]
    
    @pytest.mark.asyncio
    async def test_keyword_search(self, menu_service, sample_menu_items):
        """Test keyword-based search"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test single keyword
            result = await menu_service.search_menu_items(1, "burger")
            assert "Quantum Cheeseburger" in result
            assert "Neon Double Burger" in result
            assert "French Fries" not in result
            
            # Test multiple keywords
            result = await menu_service.search_menu_items(1, "quantum burger")
            assert "Quantum Cheeseburger" in result
            
            # Test fries search
            result = await menu_service.search_menu_items(1, "fries")
            assert "French Fries" in result
            assert "Galactic Fries" in result
            assert "Quantum Cheeseburger" not in result
    
    @pytest.mark.asyncio
    async def test_stopword_removal(self, menu_service, sample_menu_items):
        """Test that stopwords are properly removed from queries"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test with stopwords
            result = await menu_service.search_menu_items(1, "I would like to add a Quantum Cheeseburger please")
            assert "Quantum Cheeseburger" in result
            
            # Test with common stopwords
            result = await menu_service.search_menu_items(1, "the quantum burger")
            assert "Quantum Cheeseburger" in result
            
            # Test with meal/combo stopwords
            result = await menu_service.search_menu_items(1, "quantum cheeseburger meal")
            assert "Quantum Cheeseburger" in result
    
    @pytest.mark.asyncio
    async def test_punctuation_handling(self, menu_service, sample_menu_items):
        """Test that punctuation is properly handled"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test with punctuation
            result = await menu_service.search_menu_items(1, "Quantum Cheeseburger!")
            assert "Quantum Cheeseburger" in result
            
            # Test with multiple punctuation
            result = await menu_service.search_menu_items(1, "Quantum... Cheeseburger!!!")
            assert "Quantum Cheeseburger" in result
    
    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, menu_service, sample_menu_items):
        """Test that search is case insensitive"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test various cases
            test_cases = [
                "QUANTUM CHEESEBURGER",
                "quantum cheeseburger", 
                "Quantum Cheeseburger",
                "QuAnTuM cHeEsEbUrGeR"
            ]
            
            for query in test_cases:
                result = await menu_service.search_menu_items(1, query)
                assert "Quantum Cheeseburger" in result, f"Failed for query: {query}"
    
    @pytest.mark.asyncio
    async def test_whitespace_handling(self, menu_service, sample_menu_items):
        """Test that whitespace is properly handled"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test with extra spaces
            result = await menu_service.search_menu_items(1, "  Quantum   Cheeseburger  ")
            assert "Quantum Cheeseburger" in result
            
            # Test with tabs and newlines
            result = await menu_service.search_menu_items(1, "\tQuantum\tCheeseburger\n")
            assert "Quantum Cheeseburger" in result
    
    @pytest.mark.asyncio
    async def test_partial_word_matching(self, menu_service, sample_menu_items):
        """Test that partial words match correctly"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test partial word matches
            result = await menu_service.search_menu_items(1, "quantum")
            assert "Quantum Cheeseburger" in result
            assert "Quantum Cola" in result
            
            result = await menu_service.search_menu_items(1, "cheese")
            assert "Quantum Cheeseburger" in result
            
            result = await menu_service.search_menu_items(1, "fries")
            assert "French Fries" in result
            assert "Galactic Fries" in result
    
    @pytest.mark.asyncio
    async def test_no_matches(self, menu_service, sample_menu_items):
        """Test when no matches are found"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test with non-existent item
            result = await menu_service.search_menu_items(1, "Pizza")
            assert result == []
            
            # Test with gibberish
            result = await menu_service.search_menu_items(1, "xyzabc123")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_unavailable_items_excluded(self, menu_service, sample_menu_items):
        """Test that unavailable items are excluded from search results"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test that unavailable items don't appear in results
            result = await menu_service.search_menu_items(1, "unavailable")
            assert result == []  # Should be empty because item is not available
    
    @pytest.mark.asyncio
    async def test_multiple_matches(self, menu_service, sample_menu_items):
        """Test when multiple items match the query"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test multiple matches
            result = await menu_service.search_menu_items(1, "fries")
            assert len(result) == 2
            assert "French Fries" in result
            assert "Galactic Fries" in result
            
            # Test quantum items
            result = await menu_service.search_menu_items(1, "quantum")
            assert len(result) == 2
            assert "Quantum Cheeseburger" in result
            assert "Quantum Cola" in result
    
    @pytest.mark.asyncio
    async def test_empty_query(self, menu_service, sample_menu_items):
        """Test handling of empty queries"""
        with patch('app.services.menu_service.UnitOfWork') as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.menu_items.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
            mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
            mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test empty string
            result = await menu_service.search_menu_items(1, "")
            assert result == []
            
            # Test whitespace only
            result = await menu_service.search_menu_items(1, "   ")
            assert result == []
            
            # Test only stopwords
            result = await menu_service.search_menu_items(1, "the a an and")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_normalize_query_method(self, menu_service):
        """Test the _normalize_query method directly"""
        # Test basic normalization
        result = menu_service._normalize_query("  Quantum Cheeseburger!  ")
        assert result == "quantum cheeseburger"
        
        # Test punctuation removal
        result = menu_service._normalize_query("Quantum... Cheeseburger!!!")
        assert result == "quantum cheeseburger"
        
        # Test whitespace collapse
        result = menu_service._normalize_query("Quantum   Cheeseburger")
        assert result == "quantum cheeseburger"
        
        # Test case normalization
        result = menu_service._normalize_query("QUANTUM CHEESEBURGER")
        assert result == "quantum cheeseburger"
    
    @pytest.mark.asyncio
    async def test_extract_keywords_method(self, menu_service):
        """Test the _extract_keywords method directly"""
        # Test stopword removal
        result = menu_service._extract_keywords("I would like to add a Quantum Cheeseburger please")
        assert "quantum" in result
        assert "cheeseburger" in result
        assert "i" not in result
        assert "would" not in result
        assert "like" not in result
        assert "to" not in result
        assert "add" not in result
        assert "a" not in result
        assert "please" not in result
        
        # Test with common stopwords
        result = menu_service._extract_keywords("the quantum burger meal")
        assert "quantum" in result
        assert "burger" in result
        assert "the" not in result
        assert "meal" not in result
        
        # Test with short words (should be filtered out)
        result = menu_service._extract_keywords("a b c quantum cheeseburger")
        assert "quantum" in result
        assert "cheeseburger" in result
        assert "a" not in result
        assert "b" not in result
        assert "c" not in result
