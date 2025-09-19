#!/usr/bin/env python3
"""
Check database contents to verify import worked
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.database import get_async_session
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.tag import Tag
from sqlalchemy import select


async def check_database():
    """Check what's actually in the database"""
    
    print("🔍 Checking database contents...")
    
    try:
        async with get_async_session() as db:
            # Check restaurants
            print("\n📊 RESTAURANTS:")
            result = await db.execute(select(Restaurant))
            restaurants = result.scalars().all()
            print(f"   Found {len(restaurants)} restaurants")
            for restaurant in restaurants:
                print(f"   - ID: {restaurant.id}, Name: {restaurant.name}, Colors: {restaurant.primary_color}/{restaurant.secondary_color}")
            
            # Check categories
            print("\n📊 CATEGORIES:")
            result = await db.execute(select(Category))
            categories = result.scalars().all()
            print(f"   Found {len(categories)} categories")
            for category in categories:
                print(f"   - ID: {category.id}, Name: {category.name}, Restaurant ID: {category.restaurant_id}")
            
            # Check menu items
            print("\n📊 MENU ITEMS:")
            result = await db.execute(select(MenuItem))
            menu_items = result.scalars().all()
            print(f"   Found {len(menu_items)} menu items")
            for item in menu_items[:5]:  # Show first 5
                print(f"   - ID: {item.id}, Name: {item.name}, Price: {item.price}, Restaurant ID: {item.restaurant_id}")
            if len(menu_items) > 5:
                print(f"   ... and {len(menu_items) - 5} more")
            
            # Check ingredients
            print("\n📊 INGREDIENTS:")
            result = await db.execute(select(Ingredient))
            ingredients = result.scalars().all()
            print(f"   Found {len(ingredients)} ingredients")
            for ingredient in ingredients[:5]:  # Show first 5
                print(f"   - ID: {ingredient.id}, Name: {ingredient.name}, Restaurant ID: {ingredient.restaurant_id}")
            if len(ingredients) > 5:
                print(f"   ... and {len(ingredients) - 5} more")
            
            # Check tags
            print("\n📊 TAGS:")
            result = await db.execute(select(Tag))
            tags = result.scalars().all()
            print(f"   Found {len(tags)} tags")
            for tag in tags:
                print(f"   - ID: {tag.id}, Name: {tag.name}, Color: {tag.color}, Restaurant ID: {tag.restaurant_id}")
            
            print(f"\n✅ Database check complete!")
            print(f"📊 Summary: {len(restaurants)} restaurants, {len(categories)} categories, {len(menu_items)} menu items, {len(ingredients)} ingredients, {len(tags)} tags")
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_database())
