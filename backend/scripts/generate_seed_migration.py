#!/usr/bin/env python3
"""
Generate Alembic migration file with seed data from Excel
Creates a migration that can be run in production
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.excel_import_service import ExcelImportService


def escape_sql_string(value):
    """Escape string values for SQL"""
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return f"'{value.replace("'", "''")}'"
    return str(value)


def generate_sql_insert(table_name: str, data_list: list, columns: list = None) -> str:
    """Generate SQL INSERT statements for a table"""
    if not data_list:
        return ""
    
    # Get columns from first item if not provided
    if not columns:
        columns = list(data_list[0].keys())
    
    sql_lines = []
    for item in data_list:
        values = []
        for col in columns:
            value = item.get(col)
            values.append(escape_sql_string(value))
        
        values_str = ', '.join(values)
        columns_str = ', '.join(columns)
        sql_lines.append(f"    INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")
    
    return '\n'.join(sql_lines)


async def parse_excel_data(excel_path: str) -> Dict[str, Any]:
    """Parse Excel file to extract restaurant data"""
    print(f"📊 Reading Excel file: {excel_path}")
    
    # Read the Excel file
    with open(excel_path, 'rb') as f:
        excel_data = f.read()
    
    # Use the existing ExcelImportService (no DB needed for parsing)
    excel_service = ExcelImportService(None)
    parse_result = await excel_service.parse_restaurant_excel(excel_data)
    
    if not parse_result.success:
        raise Exception(f"Failed to parse Excel: {parse_result.message}")
    
    print(f"✅ Successfully parsed Excel file")
    
    # Debug: print the data structure
    print(f"🔍 Data keys: {list(parse_result.data.keys())}")
    for key, value in parse_result.data.items():
        print(f"   {key}: {type(value)} - {len(value) if isinstance(value, (list, dict)) else 'single value'}")
    
    return parse_result.data


def generate_migration_content(data: Dict[str, Any], restaurant_id: int = 20) -> str:
    """Generate the complete migration file content"""
    
    # Update restaurant ID (restaurant is a list with one item)
    if 'restaurant' in data and isinstance(data['restaurant'], list) and len(data['restaurant']) > 0:
        data['restaurant'][0]['id'] = restaurant_id
    
    migration_content = f'''"""Seed restaurant data

Revision ID: {datetime.now().strftime('%Y%m%d%H%M%S')}_seed_restaurant_data
Revises: c51ab00a2b47
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '{datetime.now().strftime('%Y%m%d%H%M%S')}_seed_restaurant_data'
down_revision = 'c51ab00a2b47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed restaurant data from Excel import"""
'''
    
    # 1. Restaurant
    restaurant_data = data.get('restaurant', [])
    if restaurant_data and isinstance(restaurant_data, list) and len(restaurant_data) > 0:
        sql = generate_sql_insert('restaurants', restaurant_data)
        if sql:
            migration_content += f'''
    # Insert restaurant
{sql}
'''
    
    # 2. Categories
    categories_data = data.get('categories', [])
    if categories_data:
        sql = generate_sql_insert('categories', categories_data)
        if sql:
            migration_content += f'''
    # Insert categories
{sql}
'''
    
    # 3. Ingredients
    ingredients_data = data.get('ingredients', [])
    if ingredients_data:
        sql = generate_sql_insert('ingredients', ingredients_data)
        if sql:
            migration_content += f'''
    # Insert ingredients
{sql}
'''
    
    # 4. Tags
    tags_data = data.get('tags', [])
    if tags_data:
        sql = generate_sql_insert('tags', tags_data)
        if sql:
            migration_content += f'''
    # Insert tags
{sql}
'''
    
    # 5. Menu Items
    menu_items_data = data.get('menu_items', [])
    if menu_items_data:
        sql = generate_sql_insert('menu_items', menu_items_data)
        if sql:
            migration_content += f'''
    # Insert menu items
{sql}
'''
    
    # 6. Menu Item Ingredients
    menu_item_ingredients_data = data.get('menu_item_ingredients', [])
    if menu_item_ingredients_data:
        sql = generate_sql_insert('menu_item_ingredients', menu_item_ingredients_data)
        if sql:
            migration_content += f'''
    # Insert menu item ingredients
{sql}
'''
    
    # 7. Inventory
    inventory_data = data.get('inventory', [])
    if inventory_data:
        sql = generate_sql_insert('inventory', inventory_data)
        if sql:
            migration_content += f'''
    # Insert inventory
{sql}
'''
    
    # 8. Menu Item Tags
    menu_item_tags_data = data.get('menu_item_tags', [])
    if menu_item_tags_data:
        sql = generate_sql_insert('menu_item_tags', menu_item_tags_data)
        if sql:
            migration_content += f'''
    # Insert menu item tags
{sql}
'''
    
    # Add downgrade function
    migration_content += f'''

def downgrade() -> None:
    """Remove seeded restaurant data"""
    # Delete in reverse order to respect foreign key constraints
    
    # Delete menu item tags
    op.execute("DELETE FROM menu_item_tags WHERE menu_item_id IN (SELECT id FROM menu_items WHERE restaurant_id = {restaurant_id});")
    
    # Delete inventory
    op.execute("DELETE FROM inventory WHERE restaurant_id = {restaurant_id};")
    
    # Delete menu item ingredients
    op.execute("DELETE FROM menu_item_ingredients WHERE menu_item_id IN (SELECT id FROM menu_items WHERE restaurant_id = {restaurant_id});")
    
    # Delete menu items
    op.execute("DELETE FROM menu_items WHERE restaurant_id = {restaurant_id};")
    
    # Delete categories
    op.execute("DELETE FROM categories WHERE restaurant_id = {restaurant_id};")
    
    # Delete ingredients
    op.execute("DELETE FROM ingredients WHERE restaurant_id = {restaurant_id};")
    
    # Delete tags
    op.execute("DELETE FROM tags WHERE restaurant_id = {restaurant_id};")
    
    # Delete restaurant
    op.execute("DELETE FROM restaurants WHERE id = {restaurant_id};")
'''
    
    return migration_content


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate Alembic migration with seed data from Excel")
    parser.add_argument(
        "excel_file", 
        help="Path to Excel file (e.g., import/import_excel.xlsx)"
    )
    parser.add_argument(
        "--restaurant-id",
        type=int,
        default=20,
        help="Restaurant ID to use (default: 20)"
    )
    parser.add_argument(
        "--output",
        help="Output migration file path (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    excel_path = os.path.abspath(args.excel_file)
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        sys.exit(1)
    
    print("🚀 AI DriveThru Migration Generator")
    print("=" * 50)
    print(f"📊 Excel file: {excel_path}")
    print(f"🏪 Restaurant ID: {args.restaurant_id}")
    print("=" * 50)
    
    try:
        # Parse Excel data
        data = await parse_excel_data(excel_path)
        
        # Generate migration content
        migration_content = generate_migration_content(data, args.restaurant_id)
        
        # Determine output file path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_seed_restaurant_data.py"
            output_path = Path("alembic/versions") / filename
        
        # Write migration file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(migration_content)
        
        print(f"✅ Migration file generated successfully!")
        print(f"📄 File: {output_path}")
        print(f"🏪 Restaurant ID: {args.restaurant_id}")
        
        # Count entities
        counts = {
            "restaurant": 1 if data.get('restaurant') else 0,
            "categories": len(data.get('categories', [])),
            "menu_items": len(data.get('menu_items', [])),
            "ingredients": len(data.get('ingredients', [])),
            "tags": len(data.get('tags', [])),
            "menu_item_ingredients": len(data.get('menu_item_ingredients', [])),
            "inventory": len(data.get('inventory', [])),
            "menu_item_tags": len(data.get('menu_item_tags', []))
        }
        
        print(f"\n📊 Data to be seeded:")
        for entity, count in counts.items():
            if count > 0:
                print(f"   {entity.replace('_', ' ').title()}: {count}")
        
        print(f"\n📋 Next steps:")
        print(f"1. Review the migration file: {output_path}")
        print(f"2. Run migration: poetry run alembic upgrade head")
        print(f"3. Set NEXT_PUBLIC_RESTAURANT_ID={args.restaurant_id} in frontend environment")
        
    except Exception as e:
        print(f"❌ Migration generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
