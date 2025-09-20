#!/usr/bin/env python3
"""
Quick script to check database contents
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_async_session

async def check_data():
    """Check what data exists in the database"""
    try:
        async with get_async_session() as db:
            # Check restaurants
            result = await db.execute("SELECT COUNT(*) FROM restaurants")
            restaurant_count = result.scalar()
            print(f"Restaurants: {restaurant_count}")
            
            # Check menu items
            result = await db.execute("SELECT COUNT(*) FROM menu_items")
            menu_item_count = result.scalar()
            print(f"Menu Items: {menu_item_count}")
            
            # Check categories
            result = await db.execute("SELECT COUNT(*) FROM categories")
            category_count = result.scalar()
            print(f"Categories: {category_count}")
            
            # Check ingredients
            result = await db.execute("SELECT COUNT(*) FROM ingredients")
            ingredient_count = result.scalar()
            print(f"Ingredients: {ingredient_count}")
            
            # If we have restaurants, show details
            if restaurant_count > 0:
                result = await db.execute("SELECT id, name FROM restaurants LIMIT 5")
                restaurants = result.fetchall()
                print("\nRestaurant details:")
                for restaurant in restaurants:
                    print(f"  ID: {restaurant[0]}, Name: {restaurant[1]}")
            
            # If we have menu items, show some details
            if menu_item_count > 0:
                result = await db.execute("SELECT name, price FROM menu_items LIMIT 5")
                menu_items = result.fetchall()
                print("\nMenu items:")
                for item in menu_items:
                    print(f"  {item[0]} - ${item[1]}")
                    
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    asyncio.run(check_data())
