#!/usr/bin/env python3
"""
Clear all data from the database
WARNING: This will delete ALL data!
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_session
from app.models import *  # Import all models
from sqlalchemy import text


async def clear_database():
    """Clear all data from the database"""
    
    print("⚠️  WARNING: This will delete ALL data from the database!")
    print("🗑️  Clearing database...")
    
    # Use TRUNCATE CASCADE for a clean, fast clear
    async with get_async_session() as db:
        try:
            # Get all table names from the database
            result = await db.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'alembic%'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("⚠️  No tables found to clear")
                return
            
            print(f"📋 Found {len(tables)} tables to clear")
            
            # Use TRUNCATE CASCADE to clear everything at once
            # This is much faster and handles dependencies automatically
            table_list = ', '.join(tables)
            await db.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))
            
            await db.commit()
            print("✅ Database cleared successfully!")
            print(f"🗑️  Cleared {len(tables)} tables")
            
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            await db.rollback()
            raise


async def main():
    """Main function"""
    print("🗑️  Database Clearer")
    print("=" * 50)
    
    # Check if running in non-interactive mode (like Docker exec)
    import sys
    if sys.stdin.isatty():
        # Interactive mode - ask for confirmation
        confirm = input("Are you sure you want to delete ALL data? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
    else:
        # Non-interactive mode - auto-confirm
        print("⚠️  Non-interactive mode detected - proceeding with database clear")
    
    await clear_database()


if __name__ == "__main__":
    asyncio.run(main())
