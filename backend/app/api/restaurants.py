"""
Restaurant management API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
import os
from pathlib import Path

from ..core.database import get_db
from ..repository import RestaurantRepository, CategoryRepository, MenuItemRepository

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants"])




@router.get("/health")
async def restaurant_api_health_check():
    """
    Health check endpoint for restaurant API
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "restaurant_api",
        "message": "Restaurant API is running"
    }






@router.get("/{restaurant_id}/menu")
async def get_restaurant_menu(restaurant_id: int, db = Depends(get_db)):
    """
    Get public menu for a restaurant (no authentication required)
    
    Args:
        restaurant_id: Restaurant ID
        
    Returns:
        dict: Restaurant menu with categories and items
    """
    try:
        
        # Get restaurant info
        restaurant_repo = RestaurantRepository(db)
        restaurant = await restaurant_repo.get_by_id(restaurant_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        # Get categories
        category_repo = CategoryRepository(db)
        categories = await category_repo.get_active_by_restaurant(restaurant_id)
        
        # Get menu items for each category
        menu_item_repo = MenuItemRepository(db)
        menu_data = []
        
        for category in categories:
            menu_items = await menu_item_repo.get_available_by_category(category.id)
            
            # Build category data
            category_items = []
            for item in menu_items:
                # Get tags for this menu item (simplified - no relationships)
                tags = []
                try:
                    # Query tags directly instead of using relationships
                    from sqlalchemy import select
                    from ..models.menu_item_tag import MenuItemTag
                    from ..models.tag import Tag
                    
                    tag_result = await db.execute(
                        select(Tag)
                        .join(MenuItemTag, Tag.id == MenuItemTag.tag_id)
                        .where(MenuItemTag.menu_item_id == item.id)
                    )
                    tag_records = tag_result.scalars().all()
                    tags = [{"name": tag.name, "color": tag.color} for tag in tag_records]
                except Exception:
                    tags = []
                
                category_items.append({
                    "id": item.id,
                    "name": item.name,
                    "price": float(item.price),
                    "description": item.description,
                    "image_url": item.image_url,
                    "sort_order": item.display_order,
                    "restaurant_id": item.restaurant_id,
                    "tags": tags
                })
            
            if category_items:
                menu_data.append({
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "sort_order": category.display_order,
                    "items": category_items
                })
        
        # Sort categories and items
        menu_data.sort(key=lambda x: x["sort_order"])
        for category in menu_data:
            category["items"].sort(key=lambda x: x["sort_order"])
        
        return {
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "primary_color": restaurant.primary_color,
                "secondary_color": restaurant.secondary_color,
                "logo_url": restaurant.logo_url
            },
            "menu": menu_data,
            "total_items": sum(len(cat["items"]) for cat in menu_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve menu: {str(e)}"
        )

    """
    Get Excel template structure for restaurant import
    
    Returns:
        dict: Template information with required sheets and columns
    """
    return {
        "message": "Excel import template structure",
        "required_sheets": {
            "restaurant_info": {
                "required_columns": ["name", "primary_color", "secondary_color"],
                "optional_columns": ["phone", "address", "logo_url"],
                "description": "Basic restaurant information"
            },
            "categories": {
                "required_columns": ["name", "description", "sort_order"],
                "optional_columns": ["is_active"],
                "description": "Menu categories (e.g., Burgers, Sides, Drinks)"
            },
            "menu_items": {
                "required_columns": ["name", "category_name", "price", "description"],
                "optional_columns": ["image_url", "is_available", "sort_order"],
                "description": "Menu items with prices and descriptions"
            },
            "ingredients": {
                "required_columns": ["name", "description", "allergens"],
                "optional_columns": ["unit_type"],
                "description": "Ingredients used in menu items"
            },
            "menu_item_ingredients": {
                "required_columns": ["menu_item_name", "ingredient_name", "quantity"],
                "optional_columns": ["is_required"],
                "description": "Which ingredients go in each menu item"
            },
            "inventory": {
                "required_columns": ["ingredient_name", "current_stock", "min_stock"],
                "optional_columns": [],
                "description": "Current inventory levels for ingredients"
            },
            "tags": {
                "required_columns": ["name", "color", "description"],
                "optional_columns": [],
                "description": "Tags for grouping menu items (e.g., Popular, Spicy)"
            },
            "menu_item_tags": {
                "required_columns": ["menu_item_name", "tag_name"],
                "optional_columns": [],
                "description": "Which tags apply to which menu items"
            }
        },
        "validation_rules": {
            "restaurant_info": "Only one row allowed, all required fields must be filled",
            "categories": "Names must be unique, sort_order must be numeric",
            "menu_items": "Prices must be > 0, category_name must exist in categories sheet",
            "ingredients": "Names must be unique within restaurant",
            "menu_item_ingredients": "Both menu_item_name and ingredient_name must exist",
            "inventory": "Stock values must be >= 0, ingredient_name must exist",
            "tags": "Names must be unique, colors should be valid hex codes",
            "menu_item_tags": "Both menu_item_name and tag_name must exist"
        },
        "tips": [
            "Use exact column names as shown above",
            "All sheets are required - even if empty, include them",
            "Reference names must match exactly (case-insensitive)",
            "Prices and quantities should be numeric values",
            "Boolean fields (is_active, is_available, is_required) accept true/false or 1/0"
        ]
    }
