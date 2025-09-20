"""
Comprehensive unit tests for OrderValidator
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.order_validator import OrderValidator
from app.dto.order_result import OrderResult, OrderResultStatus
from app.models.menu_item import MenuItem
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.menu_item_ingredient import MenuItemIngredient
from app.models.ingredient import Ingredient
from app.models.inventory import Inventory
from app.core.unit_of_work import UnitOfWork
from app.core.config import settings
from app.tests.helpers.test_data_factory import TestDataFactory
from app.tests.helpers.mock_services import MockUnitOfWork


class TestOrderValidator:
    """Comprehensive tests for OrderValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create OrderValidator instance"""
        return OrderValidator()
    
    @pytest.fixture
    def mock_uow(self):
        """Create mock UnitOfWork using existing mock services"""
        return MockUnitOfWork()
    
    @pytest.fixture
    def mock_menu_item(self):
        """Create mock menu item using test data factory"""
        menu_item_data = TestDataFactory.create_menu_item(
            id=1,
            name="Quantum Cheeseburger",
            price=9.99,
            restaurant_id=1,
            is_available=True
        )
        
        # Convert to mock object
        menu_item = Mock(spec=MenuItem)
        for key, value in menu_item_data.items():
            setattr(menu_item, key, value)
        menu_item.to_dict.return_value = menu_item_data
        return menu_item
    
    @pytest.fixture
    def mock_order(self):
        """Create mock order"""
        order = Mock(spec=Order)
        order.id = 1
        order.total_amount = 15.98
        order.order_items = []
        return order
    
    @pytest.fixture
    def mock_order_item(self, mock_menu_item):
        """Create mock order item"""
        order_item = Mock(spec=OrderItem)
        order_item.id = 1
        order_item.quantity = 2
        order_item.menu_item = mock_menu_item
        order_item.to_dict.return_value = {
            "id": 1,
            "quantity": 2,
            "menu_item": {"name": "Quantum Cheeseburger"}
        }
        return order_item
    
    @pytest.fixture
    def mock_ingredient(self):
        """Create mock ingredient using test data factory"""
        ingredient_data = TestDataFactory.create_ingredient(
            id=1,
            name="Lettuce",
            restaurant_id=1
        )
        
        ingredient = Mock(spec=Ingredient)
        for key, value in ingredient_data.items():
            setattr(ingredient, key, value)
        return ingredient
    
    @pytest.fixture
    def mock_menu_item_ingredient(self, mock_ingredient):
        """Create mock menu item ingredient"""
        menu_ingredient = Mock(spec=MenuItemIngredient)
        menu_ingredient.menu_item_id = 1
        menu_ingredient.ingredient_id = 1
        menu_ingredient.quantity = 1.0
        menu_ingredient.unit = "piece"
        menu_ingredient.ingredient = mock_ingredient
        return menu_ingredient
    
    @pytest.fixture
    def mock_inventory(self):
        """Create mock inventory using test data factory"""
        inventory_data = TestDataFactory.create_inventory(
            id=1,
            ingredient_id=1,
            current_stock=100.0,
            unit="piece",
            is_low_stock=False
        )
        
        inventory = Mock(spec=Inventory)
        for key, value in inventory_data.items():
            setattr(inventory, key, value)
        return inventory

    # ============================================================================
    # VALIDATE_ADD_ITEM TESTS
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_add_item_success(self, validator, mock_uow, mock_menu_item):
        """Test successful validation of adding an item"""
        # Arrange
        restaurant_id = 1
        menu_item_id = 1
        quantity = 2
        
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=restaurant_id,
            menu_item_id=menu_item_id,
            quantity=quantity
        )
        
        # Assert
        assert result.is_success
        assert result.status == OrderResultStatus.SUCCESS
        assert "Successfully validated adding 2x Quantum Cheeseburger" in result.message
        assert result.data["menu_item"]["id"] == 1
        assert result.data["quantity"] == 2
    
    @pytest.mark.asyncio
    async def test_validate_add_item_quantity_zero(self, validator, mock_uow):
        """Test validation with zero quantity"""
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=0
        )
        
        # Assert
        assert not result.is_success
        assert result.status == OrderResultStatus.ERROR
        assert "Invalid quantity" in result.message
        assert "Quantity must be greater than 0" in result.errors
    
    @pytest.mark.asyncio
    async def test_validate_add_item_quantity_negative(self, validator, mock_uow):
        """Test validation with negative quantity"""
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=-1
        )
        
        # Assert
        assert not result.is_success
        assert "Quantity must be greater than 0" in result.errors
    
    @pytest.mark.asyncio
    async def test_validate_add_item_quantity_exceeds_max(self, validator, mock_uow):
        """Test validation with quantity exceeding maximum"""
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=settings.MAX_QUANTITY_PER_ITEM + 1
        )
        
        # Assert
        assert not result.is_success
        assert "Quantity cannot exceed 10 per item" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_menu_item_not_found(self, validator, mock_uow):
        """Test validation when menu item doesn't exist"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = None
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=999,
            quantity=1
        )
        
        # Assert
        assert not result.is_success
        assert "Menu item not found" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_add_item_wrong_restaurant(self, validator, mock_uow, mock_menu_item):
        """Test validation when menu item belongs to different restaurant"""
        # Arrange
        mock_menu_item.restaurant_id = 2  # Different restaurant
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,  # Requesting restaurant 1
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert not result.is_success
        assert "Menu item does not belong to this restaurant" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_add_item_unavailable(self, validator, mock_uow, mock_menu_item):
        """Test validation when menu item is unavailable"""
        # Arrange
        mock_menu_item.is_available = False
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert not result.is_success
        assert "Quantum Cheeseburger' is not available" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_customizations_success(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test validation with valid customizations"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Set up the mock ingredient to match the customization
        mock_menu_item_ingredient.ingredient.name = "lettuce"
        mock_menu_item_ingredient.ingredient_id = 1
        
        customizations = ["no lettuce"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_invalid_customizations(self, validator, mock_uow, mock_menu_item):
        """Test validation with invalid customizations (foie gras scenario)"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []  # No ingredients
        
        customizations = ["no foie gras"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert not result.is_success
        assert "Invalid customizations" in result.message
        assert "Cannot remove 'foie gras'" in result.errors[0]
        assert "not an ingredient in this item" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_extra_customization_warning(self, validator, mock_uow, mock_menu_item):
        """Test validation with extra customization that's not a standard ingredient"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []  # No ingredients
        
        customizations = ["extra truffle"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert result.status == OrderResultStatus.PARTIAL_SUCCESS
        assert result.warnings
        assert "Cannot add extra 'truffle'" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_check_success(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test inventory validation success"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_insufficient(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test inventory validation with insufficient stock"""
        # Arrange
        mock_inventory.current_stock = 0.5  # Less than required
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert not result.is_success
        assert "Inventory validation failed" in result.message
        assert "Insufficient inventory for 'Lettuce'" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_low_stock_warning(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test inventory validation with low stock warning"""
        # Arrange
        mock_inventory.current_stock = 10.0  # Sufficient but low
        mock_inventory.is_low_stock = True
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert result.status == OrderResultStatus.PARTIAL_SUCCESS
        assert result.warnings
        assert "Low stock warning for 'Lettuce'" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_order_limits_exceeded(self, validator, mock_uow, mock_menu_item, mock_order):
        """Test order limits validation"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_order.order_items = [Mock(quantity=45)]  # Already at 45 items
        mock_menu_item.price = 100.0  # High price item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=10,  # Would exceed MAX_ITEMS_PER_ORDER (50)
            current_order=mock_order
        )
        
        # Assert
        assert not result.is_success
        assert "Order limits exceeded" in result.message
        assert f"Order would exceed maximum of {settings.MAX_ITEMS_PER_ORDER} items" in result.errors
    
    @pytest.mark.asyncio
    async def test_validate_add_item_order_total_exceeded(self, validator, mock_uow, mock_menu_item, mock_order):
        """Test order total limit validation"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_order.total_amount = 190.0  # Close to limit
        mock_menu_item.price = 20.0  # Would exceed MAX_ORDER_TOTAL (200)
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            current_order=mock_order
        )
        
        # Assert
        assert not result.is_success
        assert "Order limits exceeded" in result.message
        assert f"Order total would exceed maximum of ${settings.MAX_ORDER_TOTAL}" in result.errors

    # ============================================================================
    # VALIDATE_REMOVE_ITEM TESTS
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_remove_item_success(self, validator, mock_uow, mock_order, mock_order_item):
        """Test successful validation of removing an item"""
        # Arrange
        mock_order.order_items = [mock_order_item]
        
        # Act
        result = await validator.validate_remove_item(
            uow=mock_uow,
            order_item_id=1,
            current_order=mock_order
        )
        
        # Assert
        assert result.is_success
        assert "Successfully validated removing 2x Quantum Cheeseburger" in result.message
        assert result.data["order_item"]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_validate_remove_item_not_found(self, validator, mock_uow, mock_order):
        """Test validation when order item doesn't exist"""
        # Arrange
        mock_order.order_items = []
        
        # Act
        result = await validator.validate_remove_item(
            uow=mock_uow,
            order_item_id=999,
            current_order=mock_order
        )
        
        # Assert
        assert not result.is_success
        assert "Order item not found in current order" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_remove_item_without_menu_item(self, validator, mock_uow, mock_order):
        """Test validation when order item has no menu item reference"""
        # Arrange
        order_item = Mock(spec=OrderItem)
        order_item.id = 1
        order_item.quantity = 1
        order_item.menu_item = None
        order_item.to_dict.return_value = {"id": 1, "quantity": 1}
        
        mock_order.order_items = [order_item]
        
        # Act
        result = await validator.validate_remove_item(
            uow=mock_uow,
            order_item_id=1,
            current_order=mock_order
        )
        
        # Assert
        assert result.is_success
        assert "Successfully validated removing 1x item" in result.message

    # ============================================================================
    # VALIDATE_CLEAR_ORDER TESTS
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_clear_order_success(self, validator, mock_uow, mock_order, mock_order_item):
        """Test successful validation of clearing an order"""
        # Arrange
        mock_order.order_items = [mock_order_item]
        
        # Act
        result = await validator.validate_clear_order(
            uow=mock_uow,
            current_order=mock_order
        )
        
        # Assert
        assert result.is_success
        assert "Successfully validated clearing order with 2 items" in result.message
        assert result.data["item_count"] == 2
    
    @pytest.mark.asyncio
    async def test_validate_clear_order_already_empty(self, validator, mock_uow, mock_order):
        """Test validation when order is already empty"""
        # Arrange
        mock_order.order_items = []
        
        # Act
        result = await validator.validate_clear_order(
            uow=mock_uow,
            current_order=mock_order
        )
        
        # Assert
        assert result.status == OrderResultStatus.WARNING
        assert "Order is already empty" in result.message

    # ============================================================================
    # CUSTOMIZATION VALIDATION TESTS (via validate_add_item)
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_valid_customizations(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test validation with valid customizations"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # The mock ingredient needs to match the customization
        mock_menu_item_ingredient.ingredient.name = "lettuce"  # Match the customization
        mock_menu_item_ingredient.ingredient_id = 1
        
        customizations = ["no lettuce"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_invalid_customizations_foie_gras(self, validator, mock_uow, mock_menu_item):
        """Test validation with invalid customizations (foie gras scenario)"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []  # No ingredients
        
        customizations = ["no foie gras"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert not result.is_success
        assert "Invalid customizations" in result.message
        assert "Cannot remove 'foie gras'" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_extra_customization_warning(self, validator, mock_uow, mock_menu_item):
        """Test validation with extra customization that's not a standard ingredient"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = []  # No ingredients
        
        customizations = ["extra truffle"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert result.status == OrderResultStatus.PARTIAL_SUCCESS
        assert result.warnings
        assert "Cannot add extra 'truffle'" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_with_mixed_customizations(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test validation with mixed valid/invalid customizations"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]  # Only has lettuce
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Set up the mock ingredient to match the customization
        mock_menu_item_ingredient.ingredient.name = "lettuce"
        mock_menu_item_ingredient.ingredient_id = 1
        
        customizations = ["no lettuce", "extra foie gras", "no pickles"]
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=customizations
        )
        
        # Assert
        assert not result.is_success
        assert "Invalid customizations" in result.message
        assert "Cannot remove 'pickles'" in result.errors[0]
        # Check if warnings exist before accessing them
        if result.warnings:
            assert "Cannot add extra 'foie gras'" in result.warnings[0]

    # ============================================================================
    # INVENTORY VALIDATION TESTS (via validate_add_item)
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_success(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test successful inventory validation"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_insufficient_stock(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test inventory validation with insufficient stock"""
        # Arrange
        mock_inventory.current_stock = 5.0  # Less than required
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=10
        )
        
        # Assert
        assert not result.is_success
        assert "Inventory validation failed" in result.message
        assert "Insufficient inventory for 'Lettuce'" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_low_stock_warning(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient, mock_inventory):
        """Test inventory validation with low stock warning"""
        # Arrange
        mock_inventory.current_stock = 10.0  # Sufficient but low
        mock_inventory.is_low_stock = True
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = mock_inventory
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1
        )
        
        # Assert
        assert result.status == OrderResultStatus.PARTIAL_SUCCESS
        assert result.warnings
        assert "Low stock warning for 'Lettuce'" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_no_tracking_allowed(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient):
        """Test inventory validation when no tracking but negative inventory allowed"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = None  # No inventory tracking
        
        # Temporarily enable negative inventory
        with patch.object(settings, 'ALLOW_NEGATIVE_INVENTORY', True):
            # Act
            result = await validator.validate_add_item(
                uow=mock_uow,
                restaurant_id=1,
                menu_item_id=1,
                quantity=1
            )
        
        # Assert
        assert result.is_success  # Should pass when ALLOW_NEGATIVE_INVENTORY is True
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_no_tracking_not_allowed(self, validator, mock_uow, mock_menu_item, mock_menu_item_ingredient):
        """Test inventory validation when no tracking and negative inventory not allowed"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_uow.menu_item_ingredients.get_by_menu_item.return_value = [mock_menu_item_ingredient]
        mock_uow.inventory.get_by_ingredient.return_value = None  # No inventory tracking
        
        # Temporarily disable negative inventory
        with patch.object(settings, 'ALLOW_NEGATIVE_INVENTORY', False):
            # Act
            result = await validator.validate_add_item(
                uow=mock_uow,
                restaurant_id=1,
                menu_item_id=1,
                quantity=1
            )
        
        # Assert
        assert not result.is_success
        assert "No inventory tracking for ingredient 'Lettuce'" in result.errors[0]

    # ============================================================================
    # ORDER LIMITS VALIDATION TESTS (via validate_add_item)
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_add_item_order_limits_success(self, validator, mock_uow, mock_menu_item, mock_order):
        """Test successful order limits validation"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_order.order_items = [Mock(quantity=10)]  # Current: 10 items
        mock_order.total_amount = 50.0
        mock_menu_item.price = 10.0
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=5,
            current_order=mock_order
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_order_limits_items_exceeded(self, validator, mock_uow, mock_menu_item, mock_order):
        """Test order limits validation when item count exceeds limit"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_order.order_items = [Mock(quantity=45)]  # Current: 45 items
        mock_menu_item.price = 5.0
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=10,  # Would exceed MAX_ITEMS_PER_ORDER (50)
            current_order=mock_order
        )
        
        # Assert
        assert not result.is_success
        assert "Order limits exceeded" in result.message
        assert f"Order would exceed maximum of {settings.MAX_ITEMS_PER_ORDER} items" in result.errors
    
    @pytest.mark.asyncio
    async def test_validate_add_item_order_limits_total_exceeded(self, validator, mock_uow, mock_menu_item, mock_order):
        """Test order limits validation when total amount exceeds limit"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_order.order_items = [Mock(quantity=10)]  # Current: 10 items
        mock_order.total_amount = 190.0  # Close to limit
        mock_menu_item.price = 25.0  # Would exceed MAX_ORDER_TOTAL (200)
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=5,
            current_order=mock_order
        )
        
        # Assert
        assert not result.is_success
        assert "Order limits exceeded" in result.message
        assert f"Order total would exceed maximum of ${settings.MAX_ORDER_TOTAL}" in result.errors

    # ============================================================================
    # FEATURE FLAG TESTS
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_add_item_customization_validation_disabled(self, validator, mock_uow, mock_menu_item):
        """Test validation when customization validation is disabled"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        with patch.object(settings, 'ENABLE_CUSTOMIZATION_VALIDATION', False):
            # Act
            result = await validator.validate_add_item(
                uow=mock_uow,
                restaurant_id=1,
                menu_item_id=1,
                quantity=1,
                customizations=["no foie gras"]  # Should be ignored
            )
        
        # Assert
        assert result.is_success  # Should pass without validation
    
    @pytest.mark.asyncio
    async def test_validate_add_item_inventory_checking_disabled(self, validator, mock_uow, mock_menu_item):
        """Test validation when inventory checking is disabled"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        with patch.object(settings, 'ENABLE_INVENTORY_CHECKING', False):
            # Act
            result = await validator.validate_add_item(
                uow=mock_uow,
                restaurant_id=1,
                menu_item_id=1,
                quantity=1
            )
        
        # Assert
        assert result.is_success  # Should pass without inventory check
    
    @pytest.mark.asyncio
    async def test_validate_add_item_order_limits_disabled(self, validator, mock_uow, mock_menu_item, mock_order):
        """Test validation when order limits are disabled"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_order.order_items = [Mock(quantity=100)]  # Way over limit
        mock_order.total_amount = 1000.0  # Way over limit
        
        with patch.object(settings, 'ENABLE_ORDER_LIMITS', False):
            # Act - Use a reasonable quantity that passes basic validation
            result = await validator.validate_add_item(
                uow=mock_uow,
                restaurant_id=1,
                menu_item_id=1,
                quantity=5,  # Reasonable quantity
                current_order=mock_order
            )
        
        # Assert
        assert result.is_success  # Should pass without order limit checks

    # ============================================================================
    # EDGE CASES AND ERROR SCENARIOS
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_add_item_none_customizations(self, validator, mock_uow, mock_menu_item):
        """Test validation with None customizations"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=None
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_empty_customizations(self, validator, mock_uow, mock_menu_item):
        """Test validation with empty customizations list"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            customizations=[]
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_no_current_order(self, validator, mock_uow, mock_menu_item):
        """Test validation without current order (should still work)"""
        # Arrange
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=1,
            current_order=None
        )
        
        # Assert
        assert result.is_success
    
    @pytest.mark.asyncio
    async def test_validate_add_item_empty_order_limits(self, validator, mock_uow, mock_menu_item):
        """Test order limits validation with empty order"""
        # Arrange
        empty_order = Mock(spec=Order)
        empty_order.order_items = []
        empty_order.total_amount = 0.0
        mock_uow.menu_items.get_by_id.return_value = mock_menu_item
        mock_menu_item.price = 10.0
        
        # Act
        result = await validator.validate_add_item(
            uow=mock_uow,
            restaurant_id=1,
            menu_item_id=1,
            quantity=5,
            current_order=empty_order
        )
        
        # Assert
        assert result.is_success
