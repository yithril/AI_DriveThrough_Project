#!/usr/bin/env python3
"""
Restaurant import script for AI DriveThru
Imports restaurant data from Excel file and images from local folders
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional, Dict
import mimetypes

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_session
from app.services.excel_import_service import ExcelImportService
from app.services.restaurant_import_service import RestaurantImportService
from app.services.file_storage_service import S3FileStorageService
from app.services.canned_audio_service import CannedAudioService
from app.services.tts_service import TTSService
from app.services.tts_provider import OpenAITTSProvider
from app.constants.audio_phrases import AudioPhraseConstants


async def get_restaurant_from_db(restaurant_id: int, db) -> Optional[Dict]:
    """
    Get restaurant data from database by ID
    """
    try:
        from app.repository.restaurant_repository import RestaurantRepository
        
        repo = RestaurantRepository(db)
        restaurant = await repo.get_by_id(restaurant_id)
        
        if restaurant:
            return {
                'name': restaurant.name,
                'slug': restaurant.slug
            }
        return None
    except Exception as e:
        # Error fetching restaurant from database
        return None


async def import_restaurant_data(
    excel_file_path: str,
    images_folder_path: Optional[str] = None,
    overwrite_existing: bool = False,
    import_menu: bool = True,
    upload_images: bool = True,
    generate_audio: bool = True
):
    """
    Import restaurant data from Excel file and optionally process images and audio
    
    Args:
        excel_file_path: Path to Excel file
        images_folder_path: Optional path to images folder
        overwrite_existing: Whether to update existing records
        generate_audio: Whether to generate canned audio phrases
    """
    try:
        # Check if Excel file exists
        if not os.path.exists(excel_file_path):
            return False
        
        # Check if images folder exists (if provided)
        if images_folder_path and not os.path.exists(images_folder_path):
            images_folder_path = None
        
        # Read Excel file (always needed for parsing)
        with open(excel_file_path, 'rb') as f:
            excel_data = f.read()
        
        # Parse Excel data (always needed)
        excel_service = ExcelImportService(None)  # No DB needed for parsing
        
        parse_result = await excel_service.parse_restaurant_excel(excel_data)
        if not parse_result.success:
            return False
        
        # Get database session for operations that need it
        async with get_async_session() as db:
            try:
                result = None
                restaurant_id = None
                restaurant_name = None
                restaurant_slug = None
                
                # Import menu items if requested
                if import_menu:
                    print("🔄 Importing menu items to database...")
                    import_service = RestaurantImportService(db)
                    
                    result = await import_service.import_restaurant_data(
                        validated_data=parse_result.data,
                        overwrite_existing=overwrite_existing
                    )
                    
                    if result.success:
                        print("✅ Menu items imported successfully!")
                        if result.data:
                            print(f"   Restaurant: {result.data.get('restaurant_name', 'Unknown')}")
                            print(f"   Categories: {result.data.get('categories_created', 0)}")
                            print(f"   Menu Items: {result.data.get('menu_items_created', 0)}")
                            print(f"   Ingredients: {result.data.get('ingredients_created', 0)}")
                            print(f"   Tags: {result.data.get('tags_created', 0)}")
                            
                            restaurant_id = result.data.get('restaurant_id', 20)
                            restaurant_name = result.data.get('restaurant_name', 'Restaurant')
                            restaurant_slug = result.data.get('restaurant_slug', 'default')
                        else:
                            print("   (No detailed data available)")
                        
                        if result.warnings:
                            print("⚠️  Warnings:")
                            for warning in result.warnings:
                                print(f"   - {warning}")
                    else:
                        print("❌ Menu import failed:")
                        print(f"   {result.message}")
                        if result.errors:
                            print("   Errors:")
                            for error in result.errors:
                                print(f"   - {error}")
                        return False
                else:
                    print("📊 Menu import skipped")
                    # Look up existing restaurant data from database
                    restaurant_id = 20
                    restaurant_data = await get_restaurant_from_db(restaurant_id, db)
                    if restaurant_data:
                        restaurant_name = restaurant_data['name']
                        restaurant_slug = restaurant_data['slug']
                        print(f"✅ Using existing restaurant: {restaurant_name}")
                    else:
                        restaurant_name = "Restaurant"
                        restaurant_slug = f"restaurant_{restaurant_id}"
                        print(f"⚠️ Restaurant {restaurant_id} not found in database, using defaults")
                
                # Process images if requested
                if upload_images and images_folder_path:
                    print("📸 Processing images...")
                    image_result = await process_images(images_folder_path, restaurant_id, db)
                    if image_result:
                        print(f"✅ Uploaded {image_result['uploaded_count']} images")
                        if image_result['errors']:
                            print("⚠️  Image upload errors:")
                            for error in image_result['errors']:
                                print(f"   - {error}")
                    else:
                        print("❌ Image processing failed")
                elif upload_images:
                    print("📸 No images folder provided, skipping image processing")
                else:
                    print("📸 Image upload skipped")
                
                # Generate canned audio if requested
                if generate_audio:
                    print("🎵 Generating canned audio phrases...")
                    audio_result = await generate_canned_audio(
                        restaurant_slug=restaurant_slug,
                        restaurant_name=restaurant_name,
                        db=db,
                        restaurant_data=parse_result.data
                    )
                    if audio_result:
                        print(f"✅ Generated {audio_result['generated_count']} audio files")
                        if audio_result['errors']:
                            print("❌ Audio generation errors:")
                            for error in audio_result['errors']:
                                print(f"   - {error}")
                            print("❌ Import failed due to audio generation errors")
                            return False
                    else:
                        print("❌ Audio generation failed")
                        return False
                else:
                    print("🎵 Audio generation skipped")
                
                return True
                
            except Exception as e:
                print(f"❌ Database error: {str(e)}")
                return False
                
    except Exception as e:
        print(f"❌ Import failed with exception: {str(e)}")
        return False


async def process_images(images_folder_path: str, restaurant_id: int, db) -> Optional[Dict]:
    """
    Process and upload images to S3 storage
    
    Args:
        images_folder_path: Path to images folder
        restaurant_id: Restaurant ID for S3 organization
        db: Database session
        
    Returns:
        Dict with upload results or None if failed
    """
    try:
        # Initialize S3 storage service
        # Note: You'll need to set these environment variables
        bucket_name = os.getenv('S3_BUCKET_NAME', 'ai-drivethru-files')
        region = os.getenv('AWS_REGION', 'us-east-1')
        endpoint_url = os.getenv('AWS_ENDPOINT_URL')
        
        storage_service = S3FileStorageService(bucket_name, region, endpoint_url)
        
        images_path = Path(images_folder_path)
        if not images_path.exists():
            print(f"❌ Images folder not found: {images_folder_path}")
            return None
        
        # Find all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(images_path.glob(f"*{ext}"))
            image_files.extend(images_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print("⚠️  No image files found in folder")
            return {"uploaded_count": 0, "errors": []}
        
        print(f"📁 Found {len(image_files)} image files")
        
        uploaded_count = 0
        errors = []
        
        for image_file in image_files:
            try:
                # Read image file
                with open(image_file, 'rb') as f:
                    image_data = f.read()
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(str(image_file))
                if not content_type:
                    content_type = 'image/png'  # Default fallback
                
                # Upload to S3
                result = await storage_service.store_file(
                    file_data=image_data,
                    file_name=image_file.name,
                    content_type=content_type,
                    restaurant_id=restaurant_id
                )
                
                if result.success and result.data:
                    uploaded_count += 1
                    # Show exactly where the image was uploaded
                    s3_key = result.data.get('s3_key', 'unknown')
                    s3_url = result.data.get('s3_url', 'unknown')
                    print(f"   ✅ Uploaded: {image_file.name}")
                    print(f"      📍 S3 Key: {s3_key}")
                    print(f"      🌐 URL: http://localhost:4566/{s3_key}")
                else:
                    error_msg = result.message if result.message else "Upload failed with no data returned"
                    errors.append(f"Failed to upload {image_file.name}: {error_msg}")
                    print(f"   ❌ Failed: {image_file.name} - {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error processing {image_file.name}: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        return {
            "uploaded_count": uploaded_count,
            "errors": errors
        }
        
    except Exception as e:
        print(f"❌ Image processing failed: {str(e)}")
        return None


def generate_restaurant_suggestions(restaurant_data: dict) -> dict:
    """
    Generate restaurant-specific suggestions based on menu data
    
    Args:
        restaurant_data: Restaurant data from import
        
    Returns:
        Dict of suggestion phrases
    """
    if not restaurant_data:
        print("⚠️  No restaurant data provided for suggestions")
        return {
            "suggestion_1": "Would you like to try our special today?",
            "suggestion_2": "Can I interest you in our combo meal?",
            "suggestion_3": "Would you like to add a drink to your order?"
        }
    
    menu_items = restaurant_data.get('menu_items', [])
    
    # Find items for suggestions based on actual fields
    # Look for items marked as special
    specials = [item for item in menu_items if item.get('is_special', False)]
    
    # Look for items marked as upsell
    upsells = [item for item in menu_items if item.get('is_upsell', False)]
    
    # Look for drinks by category name
    drinks = [item for item in menu_items if 
              item.get('category_name', '').lower() in ['drinks', 'beverages', 'beverage']]
    
    # Fallback: if no specials/upsells found, use first 3 menu items
    if not specials and not upsells:
        fallback_items = menu_items[:3] if len(menu_items) >= 3 else menu_items
        suggestions = {
            "suggestion_1": f"Would you like to try our {fallback_items[0]['name']}?" if fallback_items else "Would you like to try our special today?",
            "suggestion_2": f"Can I interest you in our {fallback_items[1]['name']}?" if len(fallback_items) > 1 else "Can I interest you in our combo meal?",
            "suggestion_3": f"Would you like to add a {fallback_items[2]['name']}?" if len(fallback_items) > 2 else "Would you like to add a drink to your order?"
        }
    else:
        # Use actual specials/upsells if available
        suggestions = {
            "suggestion_1": f"Would you like to try our {specials[0]['name']}?" if specials else f"Would you like to try our {menu_items[0]['name']}?" if menu_items else "Would you like to try our special today?",
            "suggestion_2": f"Can I interest you in our {upsells[0]['name']}?" if upsells else f"Can I interest you in our {menu_items[1]['name']}?" if len(menu_items) > 1 else "Can I interest you in our combo meal?",
            "suggestion_3": f"Would you like to add a {drinks[0]['name']}?" if drinks else f"Would you like to add a {menu_items[2]['name']}?" if len(menu_items) > 2 else "Would you like to add a drink to your order?"
        }
    
    return suggestions


async def generate_canned_audio(restaurant_slug: str, restaurant_name: str, db, restaurant_data: dict = None) -> Optional[Dict]:
    """
    Generate canned audio phrases for a restaurant
    
    Args:
        restaurant_slug: Restaurant slug for file naming
        restaurant_name: Restaurant name for customization
        db: Database session
        restaurant_data: Restaurant data for generating suggestions
        
    Returns:
        Dict with generation results or None if failed
    """
    try:
        # Check if OpenAI API key is available
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print("⚠️  OPENAI_API_KEY not found, skipping audio generation")
            return {"generated_count": 0, "errors": ["OPENAI_API_KEY not found"]}
        
        # Initialize services
        bucket_name = os.getenv('S3_BUCKET_NAME', 'ai-drivethru-files')
        region = os.getenv('AWS_REGION', 'us-east-1')
        endpoint_url = os.getenv('AWS_ENDPOINT_URL')
        
        file_storage = S3FileStorageService(bucket_name, region, endpoint_url)
        tts_provider = OpenAITTSProvider(openai_api_key)
        tts_service = TTSService(tts_provider)
        canned_audio_service = CannedAudioService(file_storage, tts_service)
        
        print(f"   🎤 Generating audio for restaurant: {restaurant_name}")
        print(f"   📁 Restaurant slug: {restaurant_slug}")
        
        # Generate restaurant-specific suggestions if data available
        if restaurant_data:
            print(f"   🔍 Restaurant data keys: {list(restaurant_data.keys()) if restaurant_data else 'None'}")
            suggestions = generate_restaurant_suggestions(restaurant_data)
            print(f"   🎯 Generated {len(suggestions)} restaurant-specific suggestions")
            for suggestion_type, text in suggestions.items():
                print(f"      {suggestion_type}: {text}")
        else:
            print("   ⚠️  No restaurant data provided for suggestions")
        
        # Generate all canned audio phrases
        results = await canned_audio_service.generate_all_canned_audio(
            restaurant_slug=restaurant_slug,
            restaurant_name=restaurant_name
        )
        
        generated_count = len(results)
        errors = []
        
        # Report results
        for phrase_type, url in results.items():
            print(f"   ✅ {phrase_type}: {url}")
        
        # Check for missing phrases
        expected_phrases = [pt.value for pt in AudioPhraseConstants.get_all_phrase_types()]
        missing_phrases = set(expected_phrases) - set(results.keys())
        
        if missing_phrases:
            for missing in missing_phrases:
                error_msg = f"Failed to generate {missing} audio"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        return {
            "generated_count": generated_count,
            "errors": errors,
            "results": results
        }
        
    except Exception as e:
        error_msg = f"Audio generation failed: {str(e)}"
        print(f"   ❌ {error_msg}")
        return {
            "generated_count": 0,
            "errors": [error_msg]
        }


def get_user_input():
    """Get user input interactively"""
    print("🚀 AI DriveThru Restaurant Import Script")
    print("=" * 50)
    
    # Get operation preferences first
    print("🎯 What would you like to do?")
    print("1. Import menu items (Excel → Database)")
    print("2. Upload images (Images → S3)")
    print("3. Generate canned audio (Text → Audio files)")
    print("4. All of the above")
    print("5. Custom combination")
    
    while True:
        choice = input("\nSelect option (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            break
        else:
            print("Please enter 1, 2, 3, 4, or 5")
    
    # Get Excel file path (required for all operations)
    while True:
        excel_file = input("\n📊 Enter Excel file name (e.g., import_excel): ").strip()
        if not excel_file:
            print("❌ Excel file name is required!")
            continue
        
        # Add import/ folder and .xlsx extension
        excel_file_with_path = f"import/{excel_file}.xlsx"
        excel_path = os.path.abspath(excel_file_with_path)
        
        if not os.path.exists(excel_path):
            print(f"❌ File not found: {excel_path}")
            continue
        
        print(f"✅ Found Excel file: {excel_path}")
        break
    
    # Set operations based on choice
    if choice == '1':
        import_menu = True
        upload_images = False
        generate_audio = False
    elif choice == '2':
        import_menu = False
        upload_images = True
        generate_audio = False
    elif choice == '3':
        import_menu = False
        upload_images = False
        generate_audio = True
    elif choice == '4':
        import_menu = True
        upload_images = True
        generate_audio = True
    else:  # choice == '5'
        # Custom combination
        import_menu = input("📊 Import menu items? (y/n): ").strip().lower() in ['y', 'yes']
        upload_images = input("📸 Upload images? (y/n): ").strip().lower() in ['y', 'yes']
        generate_audio = input("🎵 Generate audio? (y/n): ").strip().lower() in ['y', 'yes']
    
    # Get additional settings based on selected operations
    images_path = None
    overwrite_existing = False
    
    if import_menu:
        # Get overwrite preference for menu import
        while True:
            overwrite_input = input("🔄 Overwrite existing menu items? (y/n): ").strip().lower()
            if overwrite_input in ['y', 'yes']:
                overwrite_existing = True
                break
            elif overwrite_input in ['n', 'no']:
                overwrite_existing = False
                break
            else:
                print("Please enter 'y' or 'n'")
    
    if upload_images:
        # Get images folder
        while True:
            images_input = input("📸 Enter images folder name (e.g., img): ").strip()
            if not images_input:
                print("❌ Images folder name is required for image upload!")
                continue
            
            # Add import/ folder
            images_folder_with_path = f"import/{images_input}"
            images_path = os.path.abspath(images_folder_with_path)
            
            if not os.path.exists(images_path):
                print(f"❌ Folder not found: {images_path}")
                continue
            
            print(f"✅ Found images folder: {images_path}")
            break
    
    # Show summary
    print("\n📋 Operation Summary:")
    print(f"   📊 Excel file: {excel_path}")
    print(f"   📊 Import menu items: {'Yes' if import_menu else 'No'}")
    print(f"   📸 Upload images: {'Yes' if upload_images else 'No'}")
    print(f"   🎵 Generate audio: {'Yes' if generate_audio else 'No'}")
    if import_menu:
        print(f"   🔄 Overwrite existing: {'Yes' if overwrite_existing else 'No'}")
    if upload_images:
        print(f"   📸 Images folder: {images_path}")
    
    # Confirm before proceeding
    while True:
        confirm = input("\n🚀 Proceed with selected operations? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            break
        elif confirm in ['n', 'no']:
            print("❌ Operations cancelled by user")
            sys.exit(0)
        else:
            print("Please enter 'y' or 'n'")
    
    return excel_path, images_path, overwrite_existing, import_menu, upload_images, generate_audio


def main():
    """Main function to run the import script"""
    import argparse
    
    # Check if running in interactive mode (no arguments)
    if len(sys.argv) == 1:
        # Interactive mode
        excel_path, images_path, overwrite_existing, import_menu, upload_images, generate_audio = get_user_input()
    else:
        # Command line mode (backward compatibility)
        parser = argparse.ArgumentParser(description="Import restaurant data from Excel file")
        parser.add_argument(
            "excel_file", 
            help="Path to Excel file (e.g., import/restaurant.xlsx)"
        )
        parser.add_argument(
            "--images", 
            help="Path to images folder (e.g., import/img)"
        )
        parser.add_argument(
            "--overwrite", 
            action="store_true",
            help="Overwrite existing records"
        )
        parser.add_argument(
            "--no-audio", 
            action="store_true",
            help="Skip canned audio generation"
        )
        args = parser.parse_args()
        
        # Always use production database from environment variables
        print("🔗 Using production database from environment variables")
        
        # Convert relative paths to absolute
        excel_path = os.path.abspath(args.excel_file)
        images_path = os.path.abspath(args.images) if args.images else None
        overwrite_existing = args.overwrite
        generate_audio = not args.no_audio
        
        print("🚀 AI DriveThru Restaurant Import Script")
        print("=" * 50)
        print(f"📊 Excel file: {excel_path}")
        if images_path:
            print(f"📸 Images folder: {images_path}")
        print(f"🔄 Overwrite existing: {overwrite_existing}")
        print(f"🎵 Generate audio: {generate_audio}")
        print("=" * 50)
    
    # Run the import
    success = asyncio.run(import_restaurant_data(
        excel_file_path=excel_path,
        images_folder_path=images_path,
        overwrite_existing=overwrite_existing,
        import_menu=import_menu,
        upload_images=upload_images,
        generate_audio=generate_audio
    ))
    
    if success:
        print("\n🎉 Import completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Import failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
