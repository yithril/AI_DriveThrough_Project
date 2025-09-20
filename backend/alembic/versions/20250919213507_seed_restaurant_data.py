"""Seed restaurant data

Revision ID: 20250919213507_seed_restaurant_data
Revises: c51ab00a2b47
Create Date: 2025-09-19 21:35:07.085

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250919213507_seed_restaurant_data'
down_revision = 'c51ab00a2b47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed restaurant data from Excel import"""

    # Insert restaurant
    INSERT INTO restaurants (name, primary_color, secondary_color, phone, address, logo_url, id) VALUES ('Quantum Burger', '#00D1FF', '#12141A', '+1-555-0123', '123 Future Ave, Neon City', 'logo.png', 20);

    # Insert categories
    INSERT INTO categories (name, description, sort_order, is_active) VALUES ('Sandwiches', 'Description for Sandwiches', 1, True);
    INSERT INTO categories (name, description, sort_order, is_active) VALUES ('Sides', 'Description for Sandwiches', 2, True);
    INSERT INTO categories (name, description, sort_order, is_active) VALUES ('Drinks', 'Description for Sandwiches', 3, True);
    INSERT INTO categories (name, description, sort_order, is_active) VALUES ('Desserts', 'Description for Sandwiches', 4, True);
    INSERT INTO categories (name, description, sort_order, is_active) VALUES ('Meals', 'Description for Sandwiches', 5, True);

    # Insert ingredients
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Beef Patty', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Burger Bun', 'Fresh Beef Patty', 'Gluten', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Cheese Slice', 'Fresh Beef Patty', 'Dairy', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Lettuce', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Tomato', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Onion', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Quantum Sauce', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Chicken Patty', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Tortilla Wrap', 'Fresh Beef Patty', 'Gluten', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Veggie Mix', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Meteor Sauce', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Potato Fries', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Onion Rings Batter', 'Fresh Beef Patty', 'Gluten', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Nuggets Batter', 'Fresh Beef Patty', 'Gluten', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Salad Greens', 'Fresh Beef Patty', NULL, 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Starlight Dressing', 'Fresh Beef Patty', 'Dairy', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Ice Cream', 'Fresh Beef Patty', 'Dairy', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Cookie Dough', 'Fresh Beef Patty', 'Gluten', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Brownie Mix', 'Fresh Beef Patty', 'Gluten', 'piece');
    INSERT INTO ingredients (name, description, allergens, unit_type) VALUES ('Berry Filling', 'Fresh Beef Patty', NULL, 'piece');

    # Insert tags
    INSERT INTO tags (name, color, description) VALUES ('Popular', '#FF5733', 'Tag for Popular');
    INSERT INTO tags (name, color, description) VALUES ('New', '#33FF57', 'Tag for Popular');
    INSERT INTO tags (name, color, description) VALUES ('Spicy', '#FF3333', 'Tag for Popular');
    INSERT INTO tags (name, color, description) VALUES ('Healthy', '#33C1FF', 'Tag for Popular');

    # Insert menu items
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Quantum Cheeseburger', 'Sandwiches', 7.99, 'Juicy beef patty with cheese and Quantum sauce', 'quantum-cheeseburger.png', True, False, True, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Neon Double Burger', 'Sandwiches', 9.99, 'Two patties stacked high with neon sauce', 'neon-double-burger.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Veggie Nebula Wrap', 'Sandwiches', 6.99, 'A cosmic mix of grilled veggies in a wrap', 'veggie-nebula-wrap.png', True, False, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Spicy Meteor Chicken', 'Sandwiches', 8.49, 'Crispy chicken with fiery meteor sauce', 'spicy-meteor-chicken.png', True, False, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Galactic Fries', 'Sides', 2.99, 'Crispy golden fries', 'galactic-fries.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Cosmic Onion Rings', 'Sides', 3.49, 'Crispy battered onion rings', 'cosmic-onion-rings.png', True, False, True, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Astro Nuggets', 'Sides', 4.49, 'Chicken nuggets with star dust dip', 'astro-nuggets.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Starlight Salad', 'Sides', 3.99, 'Fresh greens with starlight dressing', 'starlight-salad.png', True, False, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Lunar Lemonade', 'Drinks', 1.99, 'Refreshing lemonade', 'lunar-lemonade.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Quantum Cola', 'Drinks', 1.79, 'Signature cola drink', 'quantum-cola.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Milky Way Shake', 'Drinks', 3.99, 'Vanilla shake with cosmic sprinkles', 'milky-way-shake.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Rocket Fuel Coffee', 'Drinks', 2.49, 'Strong brewed coffee', 'rocket-fuel-coffee.png', True, False, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Asteroid Cookie', 'Desserts', 1.49, 'Chocolate chip cookie from the stars', 'asteroid-cookie.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Black Hole Brownie', 'Desserts', 2.49, 'Rich fudge brownie', 'black-hole-brownie.png', True, False, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Nova Sundae', 'Desserts', 3.49, 'Ice cream with galactic toppings', 'nova-sundae.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Galaxy Pie', 'Desserts', 2.99, 'Slice of sweet berry pie', 'galaxy-pie.png', True, False, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Burger Combo Meal', 'Meals', 11.99, 'Cheeseburger, fries, and drink', 'burger-combo-meal.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Chicken Combo Meal', 'Meals', 10.99, 'Spicy chicken sandwich, nuggets, and drink', 'chicken-combo-meal.png', True, True, False, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Veggie Combo Meal', 'Meals', 9.99, 'Veggie wrap, salad, and lemonade', 'veggie-combo-meal.png', True, True, True, 1);
    INSERT INTO menu_items (name, category_name, price, description, image_url, is_available, is_upsell, is_special, sort_order) VALUES ('Family Pack', 'Meals', 24.99, '4 burgers, 2 fries, 2 drinks', 'family-pack.png', True, True, False, 1);

    # Insert menu item ingredients
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Quantum Cheeseburger', 'Beef Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Quantum Cheeseburger', 'Burger Bun', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Quantum Cheeseburger', 'Cheese Slice', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Quantum Cheeseburger', 'Lettuce', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Quantum Cheeseburger', 'Tomato', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Quantum Cheeseburger', 'Quantum Sauce', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Neon Double Burger', 'Beef Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Neon Double Burger', 'Beef Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Neon Double Burger', 'Burger Bun', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Neon Double Burger', 'Cheese Slice', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Veggie Nebula Wrap', 'Tortilla Wrap', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Veggie Nebula Wrap', 'Veggie Mix', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Spicy Meteor Chicken', 'Chicken Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Spicy Meteor Chicken', 'Burger Bun', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Spicy Meteor Chicken', 'Meteor Sauce', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Galactic Fries', 'Potato Fries', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Cosmic Onion Rings', 'Onion Rings Batter', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Astro Nuggets', 'Nuggets Batter', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Starlight Salad', 'Salad Greens', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Starlight Salad', 'Starlight Dressing', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Milky Way Shake', 'Ice Cream', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Asteroid Cookie', 'Cookie Dough', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Black Hole Brownie', 'Brownie Mix', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Nova Sundae', 'Ice Cream', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Galaxy Pie', 'Berry Filling', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Burger Combo Meal', 'Beef Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Burger Combo Meal', 'Burger Bun', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Burger Combo Meal', 'Cheese Slice', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Burger Combo Meal', 'Potato Fries', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Burger Combo Meal', 'Quantum Sauce', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Chicken Combo Meal', 'Chicken Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Chicken Combo Meal', 'Burger Bun', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Chicken Combo Meal', 'Meteor Sauce', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Chicken Combo Meal', 'Nuggets Batter', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Veggie Combo Meal', 'Tortilla Wrap', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Veggie Combo Meal', 'Veggie Mix', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Veggie Combo Meal', 'Salad Greens', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Veggie Combo Meal', 'Starlight Dressing', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Family Pack', 'Beef Patty', 1.0, True);
    INSERT INTO menu_item_ingredients (menu_item_name, ingredient_name, quantity, is_required) VALUES ('Family Pack', 'Burger Bun', 1.0, True);

    # Insert inventory
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Beef Patty', 120.0, 30.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Burger Bun', 200.0, 40.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Cheese Slice', 150.0, 30.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Lettuce', 60.0, 10.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Tomato', 80.0, 15.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Onion', 50.0, 10.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Quantum Sauce', 100.0, 20.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Chicken Patty', 90.0, 20.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Tortilla Wrap', 70.0, 15.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Veggie Mix', 40.0, 10.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Meteor Sauce', 60.0, 10.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Potato Fries', 200.0, 50.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Onion Rings Batter', 100.0, 20.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Nuggets Batter', 100.0, 20.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Salad Greens', 50.0, 10.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Starlight Dressing', 40.0, 10.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Ice Cream', 80.0, 20.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Cookie Dough', 60.0, 15.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Brownie Mix', 60.0, 15.0);
    INSERT INTO inventory (ingredient_name, current_stock, min_stock) VALUES ('Berry Filling', 30.0, 10.0);

    # Insert menu item tags
    INSERT INTO menu_item_tags (menu_item_name, tag_name) VALUES ('Neon Double Burger', 'Popular');
    INSERT INTO menu_item_tags (menu_item_name, tag_name) VALUES ('Spicy Meteor Chicken', 'Spicy');
    INSERT INTO menu_item_tags (menu_item_name, tag_name) VALUES ('Starlight Salad', 'Healthy');
    INSERT INTO menu_item_tags (menu_item_name, tag_name) VALUES ('Milky Way Shake', 'Popular');
    INSERT INTO menu_item_tags (menu_item_name, tag_name) VALUES ('Asteroid Cookie', 'Popular');
    INSERT INTO menu_item_tags (menu_item_name, tag_name) VALUES ('Nova Sundae', 'New');


def downgrade() -> None:
    """Remove seeded restaurant data"""
    # Delete in reverse order to respect foreign key constraints
    
    # Delete menu item tags
    op.execute("DELETE FROM menu_item_tags WHERE menu_item_id IN (SELECT id FROM menu_items WHERE restaurant_id = 20);")
    
    # Delete inventory
    op.execute("DELETE FROM inventory WHERE restaurant_id = 20;")
    
    # Delete menu item ingredients
    op.execute("DELETE FROM menu_item_ingredients WHERE menu_item_id IN (SELECT id FROM menu_items WHERE restaurant_id = 20);")
    
    # Delete menu items
    op.execute("DELETE FROM menu_items WHERE restaurant_id = 20;")
    
    # Delete categories
    op.execute("DELETE FROM categories WHERE restaurant_id = 20;")
    
    # Delete ingredients
    op.execute("DELETE FROM ingredients WHERE restaurant_id = 20;")
    
    # Delete tags
    op.execute("DELETE FROM tags WHERE restaurant_id = 20;")
    
    # Delete restaurant
    op.execute("DELETE FROM restaurants WHERE id = 20;")
