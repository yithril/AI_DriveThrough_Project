#!/usr/bin/env python3
"""
Reset alembic version table to start fresh
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text

def reset_alembic_version():
    """Reset the alembic version table"""
    try:
        with engine.connect() as conn:
            # Drop the alembic_version table if it exists
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.commit()
            print("✅ Dropped alembic_version table")
            
            # Create a fresh alembic_version table
            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            conn.commit()
            print("✅ Created fresh alembic_version table")
            
    except Exception as e:
        print(f"❌ Error resetting alembic: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Resetting alembic version table...")
    if reset_alembic_version():
        print("✅ Alembic version table reset successfully!")
        print("💡 You can now create a fresh migration")
    else:
        print("❌ Failed to reset alembic version table")
        sys.exit(1)
