#!/usr/bin/env python3
"""
Quick database check script
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_async_session
from sqlalchemy import text

async def check_database():
    """Check if the is_special column exists"""
    try:
        async with get_async_session() as db:
            # Check if is_special column exists
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'menu_items' 
                AND column_name = 'is_special'
            """))
            
            columns = result.fetchall()
            if columns:
                print("✅ is_special column found in menu_items table:")
                for col in columns:
                    print(f"   Column: {col[0]}, Type: {col[1]}, Nullable: {col[2]}")
            else:
                print("❌ is_special column not found in menu_items table")
            
            # Check if is_upsell column exists too
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'menu_items' 
                AND column_name = 'is_upsell'
            """))
            
            columns = result.fetchall()
            if columns:
                print("✅ is_upsell column found in menu_items table:")
                for col in columns:
                    print(f"   Column: {col[0]}, Type: {col[1]}, Nullable: {col[2]}")
            else:
                print("❌ is_upsell column not found in menu_items table")
                
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_database())
