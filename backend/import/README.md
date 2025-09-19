# Restaurant Import Folder

This folder contains files for importing restaurant data into the AI DriveThru system.

## 📁 Folder Structure

```
import/
├── README.md                 # This file
├── restaurant.xlsx          # Excel file with restaurant data
└── images/                  # Images folder
    ├── logo.png            # Restaurant logo
    ├── big-mac.jpg         # Menu item images
    ├── fries.jpg
    └── ...
```

## 🚀 Usage

### 1. Prepare Your Files

1. **Excel File**: Create `restaurant.xlsx` with all restaurant data (see Excel Import Guide)
2. **Images**: Place images in `images/` folder
3. **Naming**: Use descriptive filenames (e.g., `big-mac.jpg`, `fries.jpg`)

### 2. Run Import Script

```bash
# From backend directory
cd backend

# Basic import (Excel only)
python scripts/import_restaurant.py import/restaurant.xlsx

# Import with images
python scripts/import_restaurant.py import/restaurant.xlsx --images import/images

# Overwrite existing data
python scripts/import_restaurant.py import/restaurant.xlsx --overwrite
```

### 3. Check Results

The script will output:
- ✅ Success message with import summary
- ❌ Error messages with details
- ⚠️ Warnings for non-critical issues

## 📊 Excel File Requirements

See the complete guide: `app/docs/excel-import-guide.md`

**Required Sheets:**
- `restaurant_info` - Basic restaurant info
- `categories` - Menu categories
- `menu_items` - Menu items with prices
- `ingredients` - Available ingredients
- `menu_item_ingredients` - What goes in each item
- `inventory` - Current stock levels
- `tags` - Tags for organizing items
- `menu_item_tags` - Which tags apply to items

## 📸 Image Handling

**Supported Formats:**
- `.jpg`, `.jpeg` - Photos
- `.png` - Logos and graphics
- `.webp` - Modern web format

**Naming Convention:**
- Restaurant logo: `logo.png`
- Menu items: Use item name (e.g., `big-mac.jpg`)
- Keep filenames simple and descriptive

## 🔧 Troubleshooting

### Common Issues

**File Not Found:**
```
❌ Excel file not found: import/restaurant.xlsx
```
- Check file path and name
- Ensure file exists in import folder

**Import Errors:**
```
❌ Import failed: Data validation failed
```
- Check Excel file structure
- Verify all required sheets exist
- Check column names match exactly

**Database Errors:**
```
❌ Import failed with exception: connection error
```
- Ensure database is running
- Check database connection settings
- Verify environment variables

### Getting Help

1. Check the Excel Import Guide: `app/docs/excel-import-guide.md`
2. Verify your Excel file structure
3. Check database connection
4. Review error messages for specific issues

## 📝 Example Workflow

1. **Create Excel file** with restaurant data
2. **Add images** to images folder
3. **Run import script** from backend directory
4. **Check results** and fix any errors
5. **Test menu API** to verify import

```bash
# Example commands
cd backend
python scripts/import_restaurant.py import/restaurant.xlsx --images import/images
curl http://localhost:8000/restaurants/1/menu  # Test the import
```
