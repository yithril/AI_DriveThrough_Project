# Excel Import Guide for AI DriveThru

This guide provides detailed specifications for importing restaurant data via Excel files into the AI DriveThru system.

## 📋 Table of Contents

1. [Overview](#overview)
2. [File Requirements](#file-requirements)
3. [Sheet Specifications](#sheet-specifications)
4. [Data Validation Rules](#data-validation-rules)
5. [Example Files](#example-files)
6. [Common Errors](#common-errors)
7. [API Usage](#api-usage)

## 🎯 Overview

The Excel import system allows you to create a complete restaurant setup in one operation. It imports:
- Restaurant information and branding
- Menu categories and items
- Ingredients and inventory levels
- Tags for menu organization
- All relationships between entities

**Important**: All data is imported atomically - either everything succeeds or nothing is saved.

## 📁 File Requirements

### Supported Formats
- ✅ `.xlsx` (Excel 2007+)
- ✅ `.xls` (Excel 97-2003)

### File Size Limits
- **Maximum size**: 10MB
- **Minimum size**: Must not be empty

### File Structure Requirements
- **All 8 sheets must be present** (even if empty)
- **Exact column names** required (case-sensitive)
- **No empty rows** in the middle of data

## 📊 Sheet Specifications

### 1. `restaurant_info` Sheet

**Purpose**: Basic restaurant information and branding

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `name` | Text | Restaurant name (2-100 chars) | "Burger Palace" |
| `primary_color` | Text | Primary brand color (hex) | "#FF5733" |
| `secondary_color` | Text | Secondary brand color (hex) | "#FFFFFF" |

**Optional Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `phone` | Text | Contact phone number | "+1-555-0123" |
| `address` | Text | Restaurant address | "123 Main St, City, State" |
| `logo_url` | Text | URL to logo image | "https://example.com/logo.png" |

**Example**:
```
name           | primary_color | secondary_color | phone        | address           | logo_url
Burger Palace  | #FF5733       | #FFFFFF         | +1-555-0123  | 123 Main St       | https://example.com/logo.png
```

**Validation Rules**:
- Only **one row** allowed
- `name` must be 2-100 characters
- Colors must be valid hex format (#RRGGBB)
- All required columns must have values

---

### 2. `categories` Sheet

**Purpose**: Menu categories (Burgers, Sides, Drinks, etc.)

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `name` | Text | Category name (unique) | "Burgers" |
| `description` | Text | Category description | "Our signature burgers" |
| `sort_order` | Number | Display order | 1 |

**Optional Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `is_active` | Boolean | Whether category is active | true |

**Example**:
```
name      | description           | sort_order | is_active
Burgers   | Our signature burgers | 1          | true
Sides     | Delicious sides       | 2          | true
Drinks    | Refreshing beverages  | 3          | true
Desserts  | Sweet treats          | 4          | false
```

**Validation Rules**:
- Category names must be unique
- `sort_order` must be numeric
- `description` can be empty
- `is_active` accepts: true/false, 1/0, yes/no

---

### 3. `menu_items` Sheet

**Purpose**: Individual menu items with prices and descriptions

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `name` | Text | Item name (unique) | "Big Mac" |
| `category_name` | Text | Must match category name | "Burgers" |
| `price` | Number | Item price (must be > 0) | 5.99 |
| `description` | Text | Item description | "Two beef patties with special sauce" |

**Optional Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `image_url` | Text | URL to item image | "https://example.com/big-mac.jpg" |
| `is_available` | Boolean | Whether item is available | true |
| `is_upsell` | Boolean | Whether to suggest for upselling | false |
| `sort_order` | Number | Display order within category | 1 |

**Example**:
```
name        | category_name | price | description                    | image_url              | is_available | is_upsell | sort_order
Big Mac     | Burgers       | 5.99  | Two beef patties with sauce    | https://example.com/... | true         | true      | 1
Quarter     | Burgers       | 6.99  | Quarter pound beef patty       | https://example.com/... | true         | false     | 2
Fries       | Sides         | 2.99  | Golden crispy french fries     | https://example.com/... | true         | true      | 1
Coke        | Drinks        | 1.99  | Refreshing cola beverage       | https://example.com/... | true         | true      | 1
```

**Validation Rules**:
- `category_name` must exist in categories sheet
- `price` must be greater than 0
- `description` can be empty
- `is_available` accepts: true/false, 1/0, yes/no
- `is_upsell` accepts: true/false, 1/0, yes/no
- `sort_order` must be numeric

**Meals and Combos**:
Meals are treated as regular menu items in a "Meals" category:
- Create a "Meals" category in the categories sheet
- Add meal items (e.g., "Big Mac Meal") as menu items
- Set `is_upsell: true` for meals to enable AI upselling
- Price meals as complete combos (e.g., $8.99 for burger + fries + drink)
- Include all ingredients in the menu_item_ingredients sheet

---

### 4. `ingredients` Sheet

**Purpose**: Ingredients used in menu items

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `name` | Text | Ingredient name (unique) | "Beef Patty" |
| `description` | Text | Ingredient description | "100% pure beef patty" |
| `allergens` | Text | Comma-separated allergens | "None" |

**Optional Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `unit_type` | Text | Unit of measurement | "piece" |

**Example**:
```
name        | description              | allergens    | unit_type
Beef Patty  | 100% pure beef patty     | None         | piece
Lettuce     | Fresh iceberg lettuce    | None         | piece
Cheese      | American cheese slice    | Dairy        | slice
Bun         | Sesame seed bun          | Gluten       | piece
Tomato      | Fresh tomato slice       | None         | slice
```

**Validation Rules**:
- Ingredient names must be unique
- `description` can be empty
- `allergens` can be empty or comma-separated list
- `unit_type` defaults to "piece" if empty

---

### 5. `menu_item_ingredients` Sheet

**Purpose**: Define which ingredients go in each menu item

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `menu_item_name` | Text | Must match menu item name | "Big Mac" |
| `ingredient_name` | Text | Must match ingredient name | "Beef Patty" |
| `quantity` | Number | Quantity needed (must be > 0) | 2 |

**Optional Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `is_required` | Boolean | Whether ingredient is required | true |

**Example**:
```
menu_item_name | ingredient_name | quantity | is_required
Big Mac        | Beef Patty      | 2        | true
Big Mac        | Bun             | 1        | true
Big Mac        | Lettuce         | 1        | true
Big Mac        | Cheese          | 2        | true
Big Mac        | Special Sauce   | 1        | true
Quarter        | Beef Patty      | 1        | true
Quarter        | Bun             | 1        | true
Fries          | Potatoes        | 1        | true
```

**Validation Rules**:
- Both `menu_item_name` and `ingredient_name` must exist in their respective sheets
- `quantity` must be greater than 0
- `is_required` accepts: true/false, 1/0, yes/no

---

### 6. `inventory` Sheet

**Purpose**: Current stock levels for ingredients

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `ingredient_name` | Text | Must match ingredient name | "Beef Patty" |
| `current_stock` | Number | Current stock level (>= 0) | 50 |
| `min_stock` | Number | Minimum stock level (>= 0) | 10 |

**Example**:
```
ingredient_name | current_stock | min_stock
Beef Patty      | 50           | 10
Lettuce         | 30           | 5
Cheese          | 25           | 8
Bun             | 100          | 20
Potatoes        | 200          | 50
```

**Validation Rules**:
- `ingredient_name` must exist in ingredients sheet
- Both stock values must be >= 0
- `min_stock` is used for low stock alerts

---

### 7. `tags` Sheet

**Purpose**: Tags for organizing and highlighting menu items

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `name` | Text | Tag name (unique) | "Popular" |
| `color` | Text | Tag color (hex) | "#FFD700" |
| `description` | Text | Tag description | "Customer favorites" |

**Example**:
```
name     | color    | description
Popular  | #FFD700  | Customer favorites
Spicy    | #FF4500  | Contains spicy ingredients
New      | #32CD32  | New menu items
Healthy  | #00CED1  | Healthier options
```

**Validation Rules**:
- Tag names must be unique
- Colors must be valid hex format (#RRGGBB)
- `description` can be empty

---

### 8. `menu_item_tags` Sheet

**Purpose**: Apply tags to specific menu items

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `menu_item_name` | Text | Must match menu item name | "Big Mac" |
| `tag_name` | Text | Must match tag name | "Popular" |

**Example**:
```
menu_item_name | tag_name
Big Mac        | Popular
Big Mac        | Signature
Quarter        | Popular
Fries          | Popular
Coke           | Popular
```

**Validation Rules**:
- Both `menu_item_name` and `tag_name` must exist in their respective sheets
- Multiple tags can be applied to the same menu item
- Same tag can be applied to multiple menu items

## 🔍 Data Validation Rules

### Critical Validation (Import Fails)
- Restaurant info validation fails
- Categories validation fails  
- Ingredients validation fails

### Non-Critical Validation (Import Continues)
- Individual menu items fail
- Individual inventory entries fail
- Individual tags fail
- Individual relationships fail

### General Rules
1. **References must exist**: All referenced names must exist in their respective sheets
2. **Names are case-insensitive**: "Big Mac" matches "big mac"
3. **Numeric validation**: Prices, quantities, stock must be valid numbers
4. **Boolean values**: Accept true/false, 1/0, yes/no
5. **Empty cells**: Treated as empty strings or default values

## 📝 Example Files

### Complete Example Structure
```
restaurant_info (1 row):
Burger Palace | #FF5733 | #FFFFFF | +1-555-0123 | 123 Main St | https://example.com/logo.png

categories (5 rows):
Burgers | Our signature burgers | 1 | true
Sides   | Delicious sides       | 2 | true
Drinks  | Refreshing beverages  | 3 | true
Meals   | Complete meal combos  | 4 | true
Desserts| Sweet treats          | 5 | false

menu_items (6 rows):
Big Mac     | Burgers | 5.99 | Two beef patties with special sauce     | https://example.com/big-mac.jpg     | true  | false | 1
Quarter     | Burgers | 6.99 | Quarter pound beef patty               | https://example.com/quarter.jpg     | true  | false | 2
Fries       | Sides   | 2.99 | Golden crispy french fries             | https://example.com/fries.jpg       | true  | true  | 1
Coke        | Drinks  | 1.99 | Refreshing cola beverage               | https://example.com/coke.jpg        | true  | true  | 1
Big Mac Meal| Meals   | 8.99 | Big Mac, Fries, and Drink combo       | https://example.com/big-mac-meal.jpg| true  | true  | 1
Quarter Meal| Meals   | 9.99 | Quarter Pounder, Fries, and Drink     | https://example.com/quarter-meal.jpg| true  | true  | 2

ingredients (5 rows):
Beef Patty  | 100% pure beef patty     | None   | piece
Lettuce     | Fresh iceberg lettuce    | None   | piece
Cheese      | American cheese slice    | Dairy  | slice
Bun         | Sesame seed bun          | Gluten | piece
Potatoes    | Fresh cut potatoes       | None   | piece

menu_item_ingredients (8 rows):
Big Mac  | Beef Patty | 2 | true
Big Mac  | Bun        | 1 | true
Big Mac  | Lettuce    | 1 | true
Big Mac  | Cheese     | 2 | true
Quarter  | Beef Patty | 1 | true
Quarter  | Bun        | 1 | true
Fries    | Potatoes   | 1 | true
Coke     | (no ingredients needed)

inventory (5 rows):
Beef Patty | 50  | 10
Lettuce    | 30  | 5
Cheese     | 25  | 8
Bun        | 100 | 20
Potatoes   | 200 | 50

tags (3 rows):
Popular | #FFD700 | Customer favorites
New     | #32CD32 | New menu items
Spicy   | #FF4500 | Contains spicy ingredients

menu_item_tags (3 rows):
Big Mac | Popular
Quarter | Popular
Fries   | Popular
```

## ❌ Common Errors

### File Structure Errors
```
❌ "Missing required sheets: categories, menu_items"
✅ Ensure all 8 sheets exist (even if empty)

❌ "Sheet 'menu_items' missing headers: price, description"
✅ Use exact column names (case-sensitive)

❌ "Sheet 'restaurant_info' is empty"
✅ Include at least one row of data
```

### Data Validation Errors
```
❌ "Row 2: Restaurant name is required"
✅ Fill all required columns

❌ "Row 3: Price must be greater than 0"
✅ Use valid numeric values > 0

❌ "Row 4: Category 'Burgers' not found in categories sheet"
✅ Ensure referenced names exist exactly

❌ "Row 5: Primary color format invalid"
✅ Use hex format: #RRGGBB
```

### Relationship Errors
```
❌ "Row 6: Menu item 'Big Mac' not found"
✅ Create menu items before referencing them

❌ "Row 7: Ingredient 'Beef Patty' not found"
✅ Create ingredients before referencing them
```

## 🚀 API Usage

### Import Endpoint
```bash
POST /restaurants/import-from-excel
Content-Type: multipart/form-data

Parameters:
- excel_file: Excel file (.xlsx or .xls)
- overwrite_existing: boolean (default: false)
```

### Success Response
```json
{
  "success": true,
  "message": "Restaurant data imported successfully",
  "data": {
    "restaurant_id": 1,
    "restaurant_name": "Burger Palace",
    "categories_created": 4,
    "menu_items_created": 15,
    "ingredients_created": 12,
    "tags_created": 3
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Data validation failed - fix errors and retry",
  "errors": [
    "Row 2: Menu item name is required",
    "Row 3: Price must be greater than 0"
  ]
}
```

### Template Endpoint
```bash
GET /restaurants/import-template
```
Returns detailed template specifications and validation rules.

## 🍔 Meals and Combos Strategy

### **Approach: Meals as Menu Items**
Meals are treated as regular menu items in a dedicated "Meals" category:

**Benefits:**
- ✅ Simple implementation - no complex relationships
- ✅ AI-friendly - easy to suggest "make it a meal"
- ✅ Clear pricing - fixed combo prices
- ✅ Flexible - can have multiple meal variations

### **Implementation:**

1. **Create Meals Category:**
   ```
   categories sheet:
   name: "Meals"
   description: "Complete meal combos"
   sort_order: 4
   ```

2. **Add Meal Items:**
   ```
   menu_items sheet:
   name: "Big Mac Meal"
   category_name: "Meals"
   price: 8.99
   description: "Big Mac, Fries, and Drink combo"
   is_upsell: true
   ```

3. **Include All Ingredients:**
   ```
   menu_item_ingredients sheet:
   menu_item_name: "Big Mac Meal"
   ingredient_name: "Beef Patty"
   quantity: 2
   
   menu_item_name: "Big Mac Meal"
   ingredient_name: "Bun"
   quantity: 1
   
   menu_item_name: "Big Mac Meal"
   ingredient_name: "Potatoes"
   quantity: 1
   ```

### **AI Upselling Strategy:**
- Set `is_upsell: true` for meal items
- AI can suggest: "Would you like to make that a meal for $3 more?"
- Customers get clear combo pricing
- Restaurant increases average order value

## 💡 Tips for Success

1. **Start simple**: Create a basic restaurant with few items first
2. **Use the template**: Check `/restaurants/import-template` for exact specifications
3. **Validate references**: Ensure all referenced names exist in their sheets
4. **Check data types**: Use proper formats for numbers, booleans, and colors
5. **Test incrementally**: Add items gradually to catch errors early
6. **Keep backups**: Save working Excel files for reference
7. **Plan meals**: Create meal combos with attractive pricing for upselling

## 🔧 Troubleshooting

### Import Fails Completely
- Check file format (.xlsx or .xls)
- Verify all 8 sheets exist
- Check column names match exactly
- Ensure restaurant info is valid

### Partial Import Success
- Review error messages for specific rows
- Fix data validation issues
- Re-import with corrected data

### Data Not Showing
- Check if items are marked as available
- Verify category relationships
- Ensure proper sort orders

For additional help, check the API health endpoint: `GET /restaurants/health`
