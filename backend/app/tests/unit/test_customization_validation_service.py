"""
Unit tests for CustomizationValidationService
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.services.customization_validation_service import CustomizationValidationService, ValidationResult, ValidationType
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient
from app.models.menu_item import MenuItem


class TestCustomizationValidationService:
    """Test cases for CustomizationValidationService"""
    
    @pytest.fixture
    def validation_service(self):
        """Create validation service instance"""
        return CustomizationValidationService()
    
    @pytest.fixture
    def mock_uow(self):
        """Create mock UnitOfWork"""
        uow = Mock()
        uow.menu_item_ingredients = AsyncMock()
        uow.ingredients = AsyncMock()
        uow.menu_items = AsyncMock()
        return uow
    
    @pytest.fixture
    def mock_menu_item(self):
        """Create mock menu item"""
        menu_item = Mock(spec=MenuItem)
        menu_item.id = 1
        menu_item.name = "Quantum Cheeseburger"
        menu_item.restaurant_id = 1
        return menu_item
    
    @pytest.fixture
    def mock_ingredient(self):
        """Create mock ingredient"""
        ingredient = Mock(spec=Ingredient)
        ingredient.id = 1
        ingredient.name = "Mustard"
        ingredient.unit_cost = 0.0
        ingredient.restaurant_id = 1
        return ingredient
    
    @pytest.fixture
    def mock_menu_item_ingredient(self):
        """Create mock menu item ingredient"""
        menu_ingredient = Mock(spec=MenuItemIngredient)
        menu_ingredient.menu_item_id = 1
        menu_ingredient.ingredient_id = 1
        menu_ingredient.ingredient = mock_ingredient
        menu_ingredient.additional_cost = 0.0
        return menu_ingredient
    
    @pytest.mark.asyncio
    async def test_validate_remove_ingredient_success(self, validation_service, mock_uow):
        """Test successfully validating removal of existing ingredient"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "lettuce"
        restaurant_id = 1
        
        # Mock ingredient exists in menu item
        mock_ingredient = Mock()
        mock_ingredient.name = "Lettuce"
        mock_menu_ingredient = Mock()
        mock_menu_ingredient.ingredient = mock_ingredient
        
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_ingredient]
        
        # Act
        result = await validation_service.validate_remove_ingredient(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert result.is_valid
        assert result.validation_type == ValidationType.REMOVE_INGREDIENT
        assert "Can remove" in result.message
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_remove_ingredient_not_found(self, validation_service, mock_uow, mock_menu_item):
        """Test validating removal of non-existent ingredient (foie gras scenario)"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "foie gras"
        restaurant_id = 1
        
        # Mock ingredient does NOT exist in menu item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validation_service.validate_remove_ingredient(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert not result.is_valid
        assert result.validation_type == ValidationType.REMOVE_INGREDIENT
        assert "Cannot remove 'foie gras'" in result.message
        assert "it's not an ingredient" in result.message
        assert len(result.errors) == 1
        assert "'foie gras' not found" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_ingredient_success_free(self, validation_service, mock_uow, mock_ingredient):
        """Test successfully validating addition of free ingredient (mustard scenario)"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "mustard"
        restaurant_id = 1
        
        # Mock ingredient exists in restaurant and is free
        mock_ingredient.name = "Mustard"
        mock_ingredient.unit_cost = 0.0
        mock_uow.ingredients.get_by_name_and_restaurant.return_value = mock_ingredient
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []
        
        # Act
        result = await validation_service.validate_add_ingredient(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert result.is_valid
        assert result.validation_type == ValidationType.ADD_INGREDIENT
        assert "Can add 'mustard'" in result.message
        assert result.extra_cost == 0.0
        assert "(no extra cost)" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_add_ingredient_success_with_cost(self, validation_service, mock_uow):
        """Test successfully validating addition of ingredient with extra cost"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "bacon"
        restaurant_id = 1
        
        # Mock ingredient exists with cost
        mock_ingredient = Mock()
        mock_ingredient.name = "Bacon"
        mock_ingredient.unit_cost = 1.50
        mock_uow.ingredients.get_by_name_and_restaurant.return_value = mock_ingredient
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []
        
        # Act
        result = await validation_service.validate_add_ingredient(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert result.is_valid
        assert result.validation_type == ValidationType.ADD_INGREDIENT
        assert "Can add 'bacon'" in result.message
        assert result.extra_cost == 1.50
        assert "(extra cost: $1.50)" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_add_ingredient_not_available(self, validation_service, mock_uow):
        """Test validating addition of ingredient not available in restaurant"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "truffle"
        restaurant_id = 1
        
        # Mock ingredient does NOT exist in restaurant
        mock_uow.ingredients.get_by_name_and_restaurant.return_value = None
        
        # Act
        result = await validation_service.validate_add_ingredient(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert not result.is_valid
        assert result.validation_type == ValidationType.ADD_INGREDIENT
        assert "Cannot add 'truffle'" in result.message
        assert "ingredient not available" in result.message
        assert len(result.errors) == 1
        assert "'truffle' not found in restaurant inventory" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_calculate_extra_cost_existing_ingredient(self, validation_service, mock_uow):
        """Test calculating extra cost for ingredient already in menu item"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "cheese"
        restaurant_id = 1
        
        # Mock ingredient already exists in menu item with additional_cost
        mock_ingredient = Mock()
        mock_ingredient.name = "Cheese"
        mock_menu_ingredient = Mock()
        mock_menu_ingredient.ingredient = mock_ingredient
        mock_menu_ingredient.additional_cost = 0.75
        
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_ingredient]
        
        # Act
        cost = await validation_service.calculate_extra_cost(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert cost == 0.75
    
    @pytest.mark.asyncio
    async def test_calculate_extra_cost_new_ingredient(self, validation_service, mock_uow):
        """Test calculating extra cost for ingredient not in menu item"""
        # Arrange
        menu_item_id = 1
        ingredient_name = "avocado"
        restaurant_id = 1
        
        # Mock ingredient exists but not in menu item
        mock_ingredient = Mock()
        mock_ingredient.unit_cost = 2.00
        mock_uow.ingredients.get_by_name_and_restaurant.return_value = mock_ingredient
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []
        
        # Act
        cost = await validation_service.calculate_extra_cost(
            menu_item_id, ingredient_name, restaurant_id, mock_uow
        )
        
        # Assert
        assert cost == 2.00
    
    @pytest.mark.asyncio
    async def test_validate_customizations_mixed(self, validation_service, mock_uow, mock_ingredient):
        """Test validating multiple customizations with mixed results"""
        # Arrange
        menu_item_id = 1
        customizations = ["no onions", "extra mustard", "no foie gras"]
        restaurant_id = 1
        
        # Mock setup
        mock_menu_item = Mock()
        mock_menu_item.name = "Quantum Cheeseburger"
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Mock ingredients
        onion_ingredient = Mock()
        onion_ingredient.name = "Onions"
        mustard_ingredient = Mock()
        mustard_ingredient.name = "Mustard"
        mustard_ingredient.unit_cost = 0.0
        
        # Mock menu item ingredients (has onions, no foie gras)
        mock_menu_ingredient_onion = Mock()
        mock_menu_ingredient_onion.ingredient = onion_ingredient
        
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_ingredient_onion]
        mock_uow.ingredients.get_by_name_and_restaurant.side_effect = lambda name, rid: {
            "mustard": mustard_ingredient,
            "foie gras": None
        }.get(name.lower())
        
        # Act
        results = await validation_service.validate_customizations(
            menu_item_id, customizations, restaurant_id, mock_uow
        )
        
        # Assert
        assert len(results) == 3
        
        # "no onions" should be valid
        assert results["no onions"].is_valid
        
        # "extra mustard" should be valid with no cost
        assert results["extra mustard"].is_valid
        assert results["extra mustard"].extra_cost == 0.0
        
        # "no foie gras" should be invalid
        assert not results["no foie gras"].is_valid
        assert "not an ingredient" in results["no foie gras"].message
    
    @pytest.mark.asyncio
    async def test_validate_customizations_generic(self, validation_service, mock_uow):
        """Test validating generic customizations (not remove/add)"""
        # Arrange
        menu_item_id = 1
        customizations = ["well done", "extra crispy"]
        restaurant_id = 1
        
        # Act
        results = await validation_service.validate_customizations(
            menu_item_id, customizations, restaurant_id, mock_uow
        )
        
        # Assert
        assert len(results) == 2
        assert results["well done"].is_valid
        assert results["extra crispy"].is_valid
        assert "accepted" in results["well done"].message
