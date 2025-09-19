"""
Excel import service for restaurant data
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import io

from ..dto.order_result import OrderResult
from ..models import Restaurant, Category, MenuItem, Ingredient, MenuItemIngredient, Inventory, Tag, MenuItemTag
from ..repository import (
    RestaurantRepository, CategoryRepository, MenuItemRepository, 
    IngredientRepository, MenuItemIngredientRepository, InventoryRepository,
    TagRepository, MenuItemTagRepository
)


class ExcelImportService:
    """
    Service for importing restaurant data from Excel files
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize Excel import service"""
        self.db = db
        self.restaurant_repo = RestaurantRepository(db)
        self.category_repo = CategoryRepository(db)
        self.menu_item_repo = MenuItemRepository(db)
        self.ingredient_repo = IngredientRepository(db)
        self.menu_item_ingredient_repo = MenuItemIngredientRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.tag_repo = TagRepository(db)
        self.menu_item_tag_repo = MenuItemTagRepository(db)
        
        # Required sheet names and headers (matching actual Excel file)
        self.required_sheets = {
            "restaurant_info": ["name", "primary_color", "secondary_color"],
            "categories": ["name", "sort_order", "is_active"],
            "menu_items": ["name", "category_name", "price", "description", "is_special", "is_upsell"],
            "ingredients": ["name", "allergens"],
            "menu_item_ingredients": ["menu_item_name", "ingredient_name", "quantity"],
            "inventory": ["ingredient_name", "current_stock", "min_stock"],
            "tags": ["name", "color"],
            "menu_item_tags": ["menu_item_name", "tag_name"]
        }
    
    async def parse_restaurant_excel(self, excel_data: bytes) -> OrderResult:
        """
        Parse restaurant data from Excel file and return structured data
        
        Args:
            excel_data: Raw Excel file bytes
            
        Returns:
            OrderResult: Parsed data ready for database import
        """
        try:
            # Stage 1: Parse and validate Excel structure
            parse_result = await self._parse_and_validate_excel(excel_data)
            if not parse_result.success:
                print(f"❌ Stage 1 failed: {parse_result.message}")
                return parse_result
            
            excel_data_dict = parse_result.data
            # Stage 2: Validate all data relationships
            validation_result = await self._validate_all_data(excel_data_dict)
            if not validation_result.is_success:
                print(f"❌ Stage 2 failed: {validation_result.message}")
                return validation_result
            
            validated_data = validation_result.data
            
            # Return the validated data for external processing
            return OrderResult.success(
                "Excel file parsed and validated successfully",
                data=validated_data
            )
            
        except Exception as e:
            print(f"❌ Exception in parse_restaurant_excel: {str(e)}")
            import traceback
            traceback.print_exc()
            return OrderResult.error(f"Excel parsing failed: {str(e)}")
    
    async def _parse_and_validate_excel(self, excel_data: bytes) -> OrderResult:
        """Parse Excel file and validate structure"""
        try:
            # Parse Excel file
            excel_file = pd.ExcelFile(io.BytesIO(excel_data))
            
            # Check if all required sheets exist
            missing_sheets = set(self.required_sheets.keys()) - set(excel_file.sheet_names)
            if missing_sheets:
                return OrderResult.error(
                    f"Missing required sheets: {', '.join(missing_sheets)}",
                    errors=[f"Sheet '{sheet}' is required but not found" for sheet in missing_sheets]
                )
            
            # Parse each sheet and validate headers
            parsed_data = {}
            validation_errors = []
            
            for sheet_name, required_headers in self.required_sheets.items():
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # Check if sheet is empty
                    if df.empty:
                        validation_errors.append(f"Sheet '{sheet_name}' is empty")
                        continue
                    
                    # Validate headers
                    missing_headers = set(required_headers) - set(df.columns)
                    if missing_headers:
                        validation_errors.append(
                            f"Sheet '{sheet_name}' missing headers: {', '.join(missing_headers)}"
                        )
                        continue
                    
                    # Clean data (remove empty rows, handle NaN values)
                    df = df.dropna(how='all')  # Remove completely empty rows
                    df = df.fillna('')  # Fill NaN with empty strings
                    
                    parsed_data[sheet_name] = df
                    
                except Exception as e:
                    validation_errors.append(f"Error parsing sheet '{sheet_name}': {str(e)}")
            
            if validation_errors:
                print(f"❌ Validation errors: {validation_errors}")
                return OrderResult.error(
                    "Excel structure validation failed",
                    errors=validation_errors
                )
            
            return OrderResult.success(
                "Excel file parsed successfully",
                data=parsed_data
            )
            
        except Exception as e:
            return OrderResult.error(f"Failed to parse Excel file: {str(e)}")
    
    async def _validate_all_data(self, excel_data: Dict[str, pd.DataFrame]) -> OrderResult:
        """Validate all data and relationships"""
        print(f"🔍 _validate_all_data called with keys: {list(excel_data.keys())}")
        validation_errors = []
        validated_data = {}
        
        try:
            # Validate restaurant info (critical - must pass)
            restaurant_validation = self._validate_restaurant_data(excel_data["restaurant_info"])
            if restaurant_validation["errors"]:
                return OrderResult.error(
                    "Restaurant data validation failed",
                    errors=restaurant_validation["errors"]
                )
            validated_data["restaurant"] = restaurant_validation["data"]
            
            # Validate categories (critical - needed for menu items)
            categories_validation = self._validate_categories_data(excel_data["categories"])
            if categories_validation["errors"]:
                return OrderResult.error(
                    "Categories validation failed",
                    errors=categories_validation["errors"]
                )
            validated_data["categories"] = categories_validation["data"]
            
            # Validate ingredients (critical - needed for relationships)
            ingredients_validation = self._validate_ingredients_data(excel_data["ingredients"])
            if ingredients_validation["errors"]:
                return OrderResult.error(
                    "Ingredients validation failed",
                    errors=ingredients_validation["errors"]
                )
            validated_data["ingredients"] = ingredients_validation["data"]
            
            # Validate menu items (collect errors but continue)
            try:
                menu_items_validation = self._validate_menu_items_data(
                    excel_data["menu_items"], 
                    validated_data["categories"]
                )
                validated_data["menu_items"] = menu_items_validation["data"]
                validation_errors.extend(menu_items_validation["errors"])
            except Exception as e:
                validation_errors.append(f"Menu items validation failed: {str(e)}")
                validated_data["menu_items"] = []
            
            # Validate menu item ingredients (collect errors but continue)
            try:
                menu_item_ingredients_validation = self._validate_menu_item_ingredients_data(
                    excel_data["menu_item_ingredients"],
                    validated_data["menu_items"],
                    validated_data["ingredients"]
                )
                validated_data["menu_item_ingredients"] = menu_item_ingredients_validation["data"]
                validation_errors.extend(menu_item_ingredients_validation["errors"])
            except Exception as e:
                validation_errors.append(f"Menu item ingredients validation failed: {str(e)}")
                validated_data["menu_item_ingredients"] = []
            
            # Validate inventory (collect errors but continue)
            try:
                inventory_validation = self._validate_inventory_data(
                    excel_data["inventory"],
                    validated_data["ingredients"]
                )
                validated_data["inventory"] = inventory_validation["data"]
                validation_errors.extend(inventory_validation["errors"])
            except Exception as e:
                validation_errors.append(f"Inventory validation failed: {str(e)}")
                validated_data["inventory"] = []
            
            # Validate tags (collect errors but continue)
            try:
                tags_validation = self._validate_tags_data(excel_data["tags"])
                validated_data["tags"] = tags_validation["data"]
                validation_errors.extend(tags_validation["errors"])
            except Exception as e:
                validation_errors.append(f"Tags validation failed: {str(e)}")
                validated_data["tags"] = []
            
            # Validate menu item tags (collect errors but continue)
            try:
                menu_item_tags_validation = self._validate_menu_item_tags_data(
                    excel_data["menu_item_tags"],
                    validated_data["menu_items"],
                    validated_data["tags"]
                )
                validated_data["menu_item_tags"] = menu_item_tags_validation["data"]
                validation_errors.extend(menu_item_tags_validation["errors"])
            except Exception as e:
                validation_errors.append(f"Menu item tags validation failed: {str(e)}")
                validated_data["menu_item_tags"] = []
            
            # If we have critical errors, fail the entire import
            if validation_errors:
                return OrderResult.error(
                    "Data validation failed - fix errors and retry",
                    errors=validation_errors
                )
            
            return OrderResult.success(
                "All data validated successfully",
                data=validated_data
            )
            
        except Exception as e:
            return OrderResult.error(f"Data validation failed: {str(e)}")
    
    def _validate_restaurant_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate restaurant data"""
        errors = []
        data = []
        
        for idx, row in df.iterrows():
            row_errors = []
            
            # Required fields
            if not row.get("name") or not str(row["name"]).strip():
                row_errors.append("Restaurant name is required")
            
            if not row.get("primary_color") or not str(row["primary_color"]).strip():
                row_errors.append("Primary color is required")
            
            if not row.get("secondary_color") or not str(row["secondary_color"]).strip():
                row_errors.append("Secondary color is required")
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "name": str(row["name"]).strip(),
                    "primary_color": str(row["primary_color"]).strip(),
                    "secondary_color": str(row["secondary_color"]).strip(),
                    "phone": str(row.get("phone", "")).strip() or None,
                    "address": str(row.get("address", "")).strip() or None,
                    "logo_url": str(row.get("logo_url", "")).strip() or None
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_categories_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate categories data"""
        errors = []
        data = []
        
        for idx, row in df.iterrows():
            row_errors = []
            
            if not row.get("name") or not str(row["name"]).strip():
                row_errors.append("Category name is required")
            
            try:
                sort_order = int(row.get("sort_order", 0))
            except (ValueError, TypeError):
                row_errors.append("Sort order must be a number")
                sort_order = 0
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "name": str(row["name"]).strip(),
                    "description": str(row.get("description", "")).strip() or None,
                    "sort_order": sort_order,
                    "is_active": bool(row.get("is_active", True))
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_ingredients_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate ingredients data"""
        errors = []
        data = []
        
        for idx, row in df.iterrows():
            row_errors = []
            
            if not row.get("name") or not str(row["name"]).strip():
                row_errors.append("Ingredient name is required")
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "name": str(row["name"]).strip(),
                    "description": str(row.get("description", "")).strip() or None,
                    "allergens": str(row.get("allergens", "")).strip() or None,
                    "unit_type": str(row.get("unit_type", "piece")).strip() or "piece"
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_menu_items_data(self, df: pd.DataFrame, categories: List[Dict]) -> Dict[str, Any]:
        """Validate menu items data"""
        errors = []
        data = []
        
        category_names = {cat["name"].lower(): cat["name"] for cat in categories}
        
        for idx, row in df.iterrows():
            row_errors = []
            
            if not row.get("name") or not str(row["name"]).strip():
                row_errors.append("Menu item name is required")
            
            # Validate category reference
            category_name = str(row.get("category_name", "")).strip()
            if not category_name or category_name.lower() not in category_names:
                row_errors.append(f"Category '{category_name}' not found in categories sheet")
            
            # Validate price
            try:
                price = float(row.get("price", 0))
                if price <= 0:
                    row_errors.append("Price must be greater than 0")
            except (ValueError, TypeError):
                row_errors.append("Price must be a valid number")
                price = 0
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "name": str(row["name"]).strip(),
                    "category_name": category_names[category_name.lower()],
                    "price": Decimal(str(price)),
                    "description": str(row.get("description", "")).strip() or None,
                    "image_url": str(row.get("image_url", "")).strip() or None,
                    "is_available": bool(row.get("is_available", True)),
                    "is_upsell": bool(row.get("is_upsell", False)),
                    "is_special": bool(row.get("is_special", False)),
                    "sort_order": int(row.get("sort_order", 0))
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_menu_item_ingredients_data(self, df: pd.DataFrame, menu_items: List[Dict], ingredients: List[Dict]) -> Dict[str, Any]:
        """Validate menu item ingredients data"""
        errors = []
        data = []
        
        menu_item_names = {item["name"].lower(): item["name"] for item in menu_items}
        ingredient_names = {ing["name"].lower(): ing["name"] for ing in ingredients}
        
        for idx, row in df.iterrows():
            row_errors = []
            
            menu_item_name = str(row.get("menu_item_name", "")).strip()
            ingredient_name = str(row.get("ingredient_name", "")).strip()
            
            if not menu_item_name or menu_item_name.lower() not in menu_item_names:
                row_errors.append(f"Menu item '{menu_item_name}' not found")
            
            if not ingredient_name or ingredient_name.lower() not in ingredient_names:
                row_errors.append(f"Ingredient '{ingredient_name}' not found")
            
            try:
                quantity = float(row.get("quantity", 0))
                if quantity <= 0:
                    row_errors.append("Quantity must be greater than 0")
            except (ValueError, TypeError):
                row_errors.append("Quantity must be a valid number")
                quantity = 0
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "menu_item_name": menu_item_names[menu_item_name.lower()],
                    "ingredient_name": ingredient_names[ingredient_name.lower()],
                    "quantity": Decimal(str(quantity)),
                    "is_required": bool(row.get("is_required", True))
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_inventory_data(self, df: pd.DataFrame, ingredients: List[Dict]) -> Dict[str, Any]:
        """Validate inventory data"""
        errors = []
        data = []
        
        ingredient_names = {ing["name"].lower(): ing["name"] for ing in ingredients}
        
        for idx, row in df.iterrows():
            row_errors = []
            
            ingredient_name = str(row.get("ingredient_name", "")).strip()
            if not ingredient_name or ingredient_name.lower() not in ingredient_names:
                row_errors.append(f"Ingredient '{ingredient_name}' not found")
            
            try:
                current_stock = float(row.get("current_stock", 0))
                if current_stock < 0:
                    row_errors.append("Current stock cannot be negative")
            except (ValueError, TypeError):
                row_errors.append("Current stock must be a valid number")
                current_stock = 0
            
            try:
                min_stock = float(row.get("min_stock", 0))
                if min_stock < 0:
                    row_errors.append("Min stock cannot be negative")
            except (ValueError, TypeError):
                row_errors.append("Min stock must be a valid number")
                min_stock = 0
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "ingredient_name": ingredient_names[ingredient_name.lower()],
                    "current_stock": Decimal(str(current_stock)),
                    "min_stock": Decimal(str(min_stock))
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_tags_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate tags data"""
        errors = []
        data = []
        
        for idx, row in df.iterrows():
            row_errors = []
            
            if not row.get("name") or not str(row["name"]).strip():
                row_errors.append("Tag name is required")
            
            if not row.get("color") or not str(row["color"]).strip():
                row_errors.append("Tag color is required")
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "name": str(row["name"]).strip(),
                    "color": str(row["color"]).strip(),
                    "description": str(row.get("description", "")).strip() or None
                })
        
        return {"data": data, "errors": errors}
    
    def _validate_menu_item_tags_data(self, df: pd.DataFrame, menu_items: List[Dict], tags: List[Dict]) -> Dict[str, Any]:
        """Validate menu item tags data"""
        errors = []
        data = []
        
        menu_item_names = {item["name"].lower(): item["name"] for item in menu_items}
        tag_names = {tag["name"].lower(): tag["name"] for tag in tags}
        
        for idx, row in df.iterrows():
            row_errors = []
            
            menu_item_name = str(row.get("menu_item_name", "")).strip()
            tag_name = str(row.get("tag_name", "")).strip()
            
            if not menu_item_name or menu_item_name.lower() not in menu_item_names:
                row_errors.append(f"Menu item '{menu_item_name}' not found")
            
            if not tag_name or tag_name.lower() not in tag_names:
                row_errors.append(f"Tag '{tag_name}' not found")
            
            if row_errors:
                errors.append(f"Row {idx + 2}: {', '.join(row_errors)}")
            else:
                data.append({
                    "menu_item_name": menu_item_names[menu_item_name.lower()],
                    "tag_name": tag_names[tag_name.lower()]
                })
        
        return {"data": data, "errors": errors}
    
    async def _save_all_data_atomically(self, validated_data: Dict[str, Any], overwrite_existing: bool) -> OrderResult:
        """Save all validated data in a single atomic transaction"""
        try:
            async with self.db.begin():
                # Create restaurant
                restaurant_data = validated_data["restaurant"][0]  # Should only be one restaurant
                restaurant = await self.restaurant_repo.create(**restaurant_data)
                
                # Create categories
                categories = {}
                for cat_data in validated_data["categories"]:
                    category = await self.category_repo.create(
                        restaurant_id=restaurant.id,
                        **cat_data
                    )
                    categories[cat_data["name"]] = category
                
                # Create ingredients
                ingredients = {}
                for ing_data in validated_data["ingredients"]:
                    ingredient = await self.ingredient_repo.create(
                        restaurant_id=restaurant.id,
                        **ing_data
                    )
                    ingredients[ing_data["name"]] = ingredient
                
                # Create menu items
                menu_items = {}
                for item_data in validated_data["menu_items"]:
                    category = categories[item_data["category_name"]]
                    menu_item = await self.menu_item_repo.create(
                        restaurant_id=restaurant.id,
                        category_id=category.id,
                        **{k: v for k, v in item_data.items() if k != "category_name"}
                    )
                    menu_items[item_data["name"]] = menu_item
                
                # Create menu item ingredients
                for mii_data in validated_data["menu_item_ingredients"]:
                    menu_item = menu_items[mii_data["menu_item_name"]]
                    ingredient = ingredients[mii_data["ingredient_name"]]
                    await self.menu_item_ingredient_repo.create(
                        menu_item_id=menu_item.id,
                        ingredient_id=ingredient.id,
                        quantity=mii_data["quantity"],
                        is_required=mii_data["is_required"]
                    )
                
                # Create inventory
                for inv_data in validated_data["inventory"]:
                    ingredient = ingredients[inv_data["ingredient_name"]]
                    await self.inventory_repo.create(
                        ingredient_id=ingredient.id,
                        current_stock=inv_data["current_stock"],
                        min_stock=inv_data["min_stock"]
                    )
                
                # Create tags
                tags = {}
                for tag_data in validated_data["tags"]:
                    tag = await self.tag_repo.create(
                        restaurant_id=restaurant.id,
                        **tag_data
                    )
                    tags[tag_data["name"]] = tag
                
                # Create menu item tags
                for mit_data in validated_data["menu_item_tags"]:
                    menu_item = menu_items[mit_data["menu_item_name"]]
                    tag = tags[mit_data["tag_name"]]
                    await self.menu_item_tag_repo.create(
                        menu_item_id=menu_item.id,
                        tag_id=tag.id
                    )
                
                # Transaction will auto-commit if we get here
            
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
            # Transaction will auto-rollback
            return OrderResult.error(f"Failed to save restaurant data: {str(e)}")
