"""
Restaurant import service for saving parsed Excel data to database
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..dto.order_result import OrderResult
from ..repository import (
    RestaurantRepository, CategoryRepository, MenuItemRepository, 
    IngredientRepository, MenuItemIngredientRepository, InventoryRepository,
    TagRepository, MenuItemTagRepository
)


class RestaurantImportService:
    """
    Service for importing restaurant data to database
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize restaurant import service"""
        self.db = db
        self.restaurant_repo = RestaurantRepository(db)
        self.category_repo = CategoryRepository(db)
        self.menu_item_repo = MenuItemRepository(db)
        self.ingredient_repo = IngredientRepository(db)
        self.menu_item_ingredient_repo = MenuItemIngredientRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.tag_repo = TagRepository(db)
        self.menu_item_tag_repo = MenuItemTagRepository(db)
    
    async def import_restaurant_data(self, validated_data: Dict[str, Any], overwrite_existing: bool = False) -> OrderResult:
        """
        Import validated restaurant data to database
        
        Args:
            validated_data: Validated data from Excel parsing
            overwrite_existing: Whether to update existing records
            
        Returns:
            OrderResult: Import result with detailed success/error information
        """
        try:
            print(f"🔄 Starting database import...")
            print(f"📊 Data keys: {list(validated_data.keys())}")
            
            # Don't use nested transactions - the session is already in a transaction
            print(f"🔍 Using existing database session")
            
            # 1. Create Restaurant
            restaurant_data = validated_data["restaurant"][0]
            restaurant = await self.restaurant_repo.create(
                name=restaurant_data["name"],
                primary_color=restaurant_data["primary_color"],
                secondary_color=restaurant_data["secondary_color"],
                logo_url=restaurant_data["logo_url"],
                description=restaurant_data.get("description", ""),  # Use empty string if not present
                is_active=restaurant_data.get("is_active", True)  # Default to True if not present
            )
            print(f"✅ Created restaurant: {restaurant.name} (ID: {restaurant.id})")
            
            # 2. Create Categories
            categories = {}
            from ..models.category import Category
            for cat_data in validated_data["categories"]:
                category = Category(
                    restaurant_id=restaurant.id,
                    name=cat_data["name"],
                    display_order=cat_data["sort_order"],  # Map sort_order to display_order
                    is_active=cat_data["is_active"]
                )
                self.db.add(category)
                categories[cat_data["name"]] = category
            await self.db.flush()  # Get category IDs
            print(f"✅ Created {len(categories)} categories")
            
            # 3. Create Ingredients
            ingredients = {}
            from ..models.ingredient import Ingredient
            for ing_data in validated_data["ingredients"]:
                ingredient = Ingredient(
                    restaurant_id=restaurant.id,
                    name=ing_data["name"],
                    allergen_type=ing_data["allergens"] if ing_data["allergens"] and ing_data["allergens"] != "None" else None,
                    is_allergen=bool(ing_data["allergens"] and ing_data["allergens"] != "None"),
                    description=ing_data["description"]
                )
                self.db.add(ingredient)
                ingredients[ing_data["name"]] = ingredient
            await self.db.flush()  # Get ingredient IDs
            print(f"✅ Created {len(ingredients)} ingredients")
            
            # 4. Create Menu Items
            menu_items = {}
            from ..models.menu_item import MenuItem
            for item_data in validated_data["menu_items"]:
                category = categories[item_data["category_name"]]
                menu_item = MenuItem(
                    restaurant_id=restaurant.id,
                    category_id=category.id,
                    name=item_data["name"],
                    price=item_data["price"],
                    description=item_data["description"],
                    image_url=item_data["image_url"],
                    is_upsell=item_data["is_upsell"],
                    is_available=item_data.get("is_available", True),  # Map is_available to is_available
                    display_order=item_data["sort_order"]  # Map sort_order to display_order
                )
                self.db.add(menu_item)
                menu_items[item_data["name"]] = menu_item
            await self.db.flush()  # Get menu item IDs
            print(f"✅ Created {len(menu_items)} menu items")
            
            # 5. Create Menu Item Ingredients
            from ..models.menu_item_ingredient import MenuItemIngredient
            for mit_data in validated_data["menu_item_ingredients"]:
                menu_item = menu_items[mit_data["menu_item_name"]]
                ingredient = ingredients[mit_data["ingredient_name"]]
                
                menu_item_ingredient = MenuItemIngredient(
                    menu_item_id=menu_item.id,
                    ingredient_id=ingredient.id,
                    quantity=mit_data["quantity"],
                    unit="piece",  # Default unit
                    is_optional=not mit_data.get("is_required", True)  # Map is_required to is_optional
                )
                self.db.add(menu_item_ingredient)
            print(f"✅ Created menu item ingredients")
            
            # 6. Create Inventory
            from ..models.inventory import Inventory
            for inv_data in validated_data["inventory"]:
                ingredient = ingredients[inv_data["ingredient_name"]]
                
                inventory = Inventory(
                    ingredient_id=ingredient.id,
                    current_stock=inv_data["current_stock"],
                    min_stock_level=inv_data["min_stock"],  # Map min_stock to min_stock_level
                    unit="piece"  # Default unit
                )
                self.db.add(inventory)
            print(f"✅ Created inventory records")
            
            # 7. Create Tags
            tags = {}
            from ..models.tag import Tag
            for tag_data in validated_data["tags"]:
                tag = Tag(
                    restaurant_id=restaurant.id,
                    name=tag_data["name"],
                    color=tag_data["color"]
                )
                self.db.add(tag)
                tags[tag_data["name"]] = tag
            await self.db.flush()  # Get tag IDs
            print(f"✅ Created {len(tags)} tags")
            
            # 8. Create Menu Item Tags
            from ..models.menu_item_tag import MenuItemTag
            for mit_data in validated_data["menu_item_tags"]:
                menu_item = menu_items[mit_data["menu_item_name"]]
                tag = tags[mit_data["tag_name"]]
                
                menu_item_tag = MenuItemTag(
                    menu_item_id=menu_item.id,
                    tag_id=tag.id
                )
                self.db.add(menu_item_tag)
            print(f"✅ Created menu item tags")
            
            print(f"🎉 All data saved successfully")
            
            # Commit the transaction
            await self.db.commit()
            print(f"✅ Transaction committed successfully")
            
            return OrderResult.success(
                "Restaurant data imported successfully",
                data={
                    "restaurant_id": restaurant.id,
                    "restaurant_name": restaurant.name,
                    "categories_created": len(categories),
                    "menu_items_created": len(menu_items),
                    "ingredients_created": len(ingredients),
                    "tags_created": len(tags)
                }
            )
            
        except Exception as e:
            print(f"❌ Database import error: {str(e)}")
            import traceback
            traceback.print_exc()
            return OrderResult.error(f"Database import failed: {str(e)}")
