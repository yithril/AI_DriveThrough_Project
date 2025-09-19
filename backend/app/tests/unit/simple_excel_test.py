"""
Simple Excel parsing test without complex imports
"""

import pandas as pd
from pathlib import Path


def test_excel_structure():
    """Test Excel file structure and content"""
    
    # Path to the test Excel file
    excel_file_path = Path(__file__).parent.parent / "test_import" / "import_excel.xlsx"
    
    if not excel_file_path.exists():
        print(f"❌ Excel file not found: {excel_file_path}")
        return False
    
    print(f"📊 Testing Excel file: {excel_file_path}")
    
    try:
        # Read the Excel file
        excel_file = pd.ExcelFile(excel_file_path)
        
        print(f"📊 Excel file sheets: {excel_file.sheet_names}")
        
        # Check each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"\n📋 Sheet: {sheet_name}")
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {list(df.columns)}")
            
            if len(df) > 0:
                print(f"   First row: {df.iloc[0].to_dict()}")
            else:
                print("   (No data in sheet)")
        
        return True
        
    except Exception as e:
        print(f"❌ Excel reading failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🧪 Simple Excel Structure Test")
    print("=" * 50)
    
    success = test_excel_structure()
    
    if success:
        print("\n✅ Excel structure test passed!")
    else:
        print("\n❌ Excel structure test failed!")
    
    return success


if __name__ == "__main__":
    main()
