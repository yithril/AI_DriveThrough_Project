"""
Test Excel parsing functionality in isolation
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path so we can import from app
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.services.excel_import_service import ExcelImportService


async def test_excel_parsing():
    """Test Excel parsing with detailed debugging"""
    
    # Path to the test Excel file - use the fixed version (renamed back to original)
    excel_file_path = Path(__file__).parent.parent / "test_import" / "import_excel.xlsx"
    
    if not excel_file_path.exists():
        print(f"❌ Excel file not found: {excel_file_path}")
        return False
    
    print(f"📊 Testing Excel file: {excel_file_path}")
    
    # Read the Excel file
    with open(excel_file_path, 'rb') as f:
        excel_data = f.read()
    
    print(f"📊 Excel file size: {len(excel_data)} bytes")
    
    try:
        # Create Excel import service (no database needed for parsing)
        excel_service = ExcelImportService(None)  # Pass None since we don't need DB for parsing
        
        print("🔄 Testing Excel parsing...")
        
        # Parse the Excel file
        result = await excel_service.parse_restaurant_excel(excel_data)
        
        print(f"🔍 Parse result success: {result.success}")
        print(f"🔍 Parse result message: {result.message}")
        
        if result.data is None:
            print("❌ Parse result data is None!")
            return False
        
        print(f"🔍 Parse result data type: {type(result.data)}")
        print(f"🔍 Parse result data keys: {list(result.data.keys())}")
        
        # Print detailed structure
        for key, value in result.data.items():
            if isinstance(value, list):
                print(f"   {key}: {len(value)} items")
                if len(value) > 0:
                    print(f"      First item: {value[0]}")
                    print(f"      Last item: {value[-1]}")
            else:
                print(f"   {key}: {value}")
        
        if result.errors:
            print("❌ Parse errors:")
            for error in result.errors:
                print(f"   - {error}")
        
        if result.warnings:
            print("⚠️  Parse warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🧪 Excel Parsing Test")
    print("=" * 50)
    
    success = await test_excel_parsing()
    
    if success:
        print("\n✅ Excel parsing test passed!")
    else:
        print("\n❌ Excel parsing test failed!")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
