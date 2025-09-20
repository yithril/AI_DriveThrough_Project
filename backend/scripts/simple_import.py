#!/usr/bin/env python3
"""
Simple restaurant import script
Takes JSON file, creates objects, saves to DB, uploads files to S3
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_session
from app.core.unit_of_work import UnitOfWork
from app.models import Restaurant, Category, MenuItem, Ingredient, MenuItemIngredient, Inventory, Tag, MenuItemTag
from app.services.file_storage_service import S3FileStorageService
from app.services.canned_audio_service import CannedAudioService
from app.core.config import settings


class RestaurantImporter:
    """Simple restaurant importer using OOP"""
    
    def __init__(self):
        self.restaurant = None
        self.categories = []
        self.menu_items = []
        self.ingredients = []
        self.tags = []
    
    async def import_from_json(self, json_file_path: str, audio_dir: str = None, img_dir: str = None):
        """Import restaurant data from JSON file"""
        
        print("🚀 Starting simple restaurant import...")
        
        # 1. Load JSON data
        print("📄 Loading JSON data...")
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # 2. Create objects from JSON
        print("🏗️  Creating objects...")
        await self._create_objects(data)
        
        # 3. Save to database
        print("💾 Saving to database...")
        async with get_async_session() as db:
            async with UnitOfWork(db) as uow:
                await self._save_to_database(uow)
        
        # 4. Upload files to S3
        if audio_dir or img_dir:
            print("☁️  Uploading files to S3...")
            await self._upload_files(audio_dir, img_dir)
        
        print(f"✅ Import complete! Restaurant ID: {self.restaurant.id}")
        return self.restaurant.id
    
    async def _create_objects(self, data: Dict[str, Any]):
        """Create model objects from JSON data"""
        
        # Create Restaurant
        restaurant_data = data['restaurant'][0]
        self.restaurant = Restaurant(
            name=restaurant_data['name'],
            primary_color=restaurant_data['primary_color'],
            secondary_color=restaurant_data['secondary_color'],
            logo_url=restaurant_data.get('logo_url', ''),
            description=restaurant_data.get('description', ''),
            is_active=restaurant_data.get('is_active', True)
        )
        
        # Create Categories
        for cat_data in data['categories']:
            category = Category(
                name=cat_data['name'],
                description=cat_data.get('description', ''),
                display_order=cat_data['display_order'],
                is_active=cat_data.get('is_active', True)
            )
            self.categories.append(category)
        
        # Create Ingredients
        for ing_data in data['ingredients']:
            ingredient = Ingredient(
                name=ing_data['name'],
                description=ing_data.get('description', ''),
                allergen_type=ing_data.get('allergen_type'),
                is_allergen=ing_data.get('is_allergen', False)
            )
            self.ingredients.append(ingredient)
        
        # Create Tags
        for tag_data in data['tags']:
            tag = Tag(
                name=tag_data['name'],
                color=tag_data.get('color', '#6B7280'),
                restaurant_id=self.restaurant.id
            )
            self.tags.append(tag)
        
        # Create Menu Items
        for item_data in data['menu_items']:
            menu_item = MenuItem(
                name=item_data['name'],
                description=item_data.get('description', ''),
                price=float(item_data['price']),
                image_url=item_data.get('image_url', ''),
                is_special=item_data.get('is_special', False),
                is_upsell=item_data.get('is_upsell', False),
                is_available=item_data.get('is_available', True)
            )
            # Store category name as a temporary attribute for later matching
            menu_item._temp_category_name = item_data.get('category_name', '')
            self.menu_items.append(menu_item)
    
    async def _save_to_database(self, uow: UnitOfWork):
        """Save all objects to database"""
        
        # Save restaurant first
        uow.db.add(self.restaurant)
        await uow.db.flush()  # Get restaurant ID
        
        # Set restaurant_id for all related objects
        for category in self.categories:
            category.restaurant_id = self.restaurant.id
            uow.db.add(category)
        
        for ingredient in self.ingredients:
            ingredient.restaurant_id = self.restaurant.id
            uow.db.add(ingredient)
        
        for tag in self.tags:
            tag.restaurant_id = self.restaurant.id
            uow.db.add(tag)
        
        await uow.db.flush()  # Get IDs for categories, ingredients, tags
        
        # Create menu items with category relationships
        category_map = {cat.name: cat for cat in self.categories}
        for menu_item in self.menu_items:
            menu_item.restaurant_id = self.restaurant.id
            # Find category by name using the stored category name
            if hasattr(menu_item, '_temp_category_name') and menu_item._temp_category_name in category_map:
                menu_item.category_id = category_map[menu_item._temp_category_name].id
            uow.db.add(menu_item)
        
        # Commit everything
        await uow.commit()
    
    async def _upload_files(self, audio_dir: str = None, img_dir: str = None):
        """Upload audio and image files to S3"""
        
        from app.services.file_storage_service import S3FileStorageService
        from app.core.config import settings
        
        # Initialize file storage service
        file_storage = S3FileStorageService(
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.S3_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL
        )
        
        if audio_dir and os.path.exists(audio_dir):
            print(f"🎵 Uploading audio files from {audio_dir}...")
            audio_files = [f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav', '.m4a'))]
            for audio_file in audio_files:
                audio_path = os.path.join(audio_dir, audio_file)
                # Read file and upload with restaurant ID pattern
                with open(audio_path, 'rb') as f:
                    file_data = f.read()
                
                # Determine content type
                content_type = 'audio/mp3' if audio_file.endswith('.mp3') else 'audio/wav' if audio_file.endswith('.wav') else 'audio/m4a'
                
                # Use just the filename - S3FileStorageService will organize it by restaurant_id
                result = await file_storage.store_file(
                    file_data=file_data,
                    file_name=audio_file,  # Just the filename
                    content_type=content_type,
                    restaurant_id=self.restaurant.id
                )
                
                if result.success:
                    print(f"  ✅ Uploaded {audio_file}")
                else:
                    print(f"  ❌ Failed to upload {audio_file}: {result.message}")
        
        if img_dir and os.path.exists(img_dir):
            print(f"🖼️  Uploading image files from {img_dir}...")
            image_files = [f for f in os.listdir(img_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            for image_file in image_files:
                image_path = os.path.join(img_dir, image_file)
                # Read file and upload with restaurant ID pattern
                with open(image_path, 'rb') as f:
                    file_data = f.read()
                
                # Determine content type
                content_type = 'image/png' if image_file.endswith('.png') else 'image/jpeg'
                
                # Use just the filename - S3FileStorageService will organize it by restaurant_id
                result = await file_storage.store_file(
                    file_data=file_data,
                    file_name=image_file,  # Just the filename
                    content_type=content_type,
                    restaurant_id=self.restaurant.id
                )
                
                if result.success:
                    print(f"  ✅ Uploaded {image_file}")
                else:
                    print(f"  ❌ Failed to upload {image_file}: {result.message}")


async def main():
    """Main function - just run this script"""
    
    # File paths (adjust these to your actual files)
    json_file = "import/import_excel_prepared_data.json"
    audio_dir = "import/audio_output"  # Optional
    img_dir = "import/img"  # Optional
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return
    
    # Create importer and run
    importer = RestaurantImporter()
    restaurant_id = await importer.import_from_json(json_file, audio_dir, img_dir)
    
    print(f"🎉 Success! Restaurant ID: {restaurant_id}")
    print(f"🌐 Your restaurant is ready at: http://localhost:8000/api/restaurants/{restaurant_id}/menu")


if __name__ == "__main__":
    asyncio.run(main())
