from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import Provide, inject
from typing import Annotated
import os
import asyncio
from pathlib import Path
from datetime import timedelta

from app.core.container import Container
from app.core.database import get_db
from app.services.excel_import_service import ExcelImportService
from app.services.restaurant_import_service import RestaurantImportService
from app.services.file_storage_service import S3FileStorageService
from app.services.canned_audio_service import CannedAudioService
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/import")
@inject
async def admin_import(
    excel_file: UploadFile = File(...),
    images: list[UploadFile] = File(None),
    overwrite: bool = Form(False),
    generate_audio: bool = Form(True),
    excel_import_service: ExcelImportService = Depends(Provide[Container.excel_import_service]),
    restaurant_import_service: RestaurantImportService = Depends(Provide[Container.restaurant_import_service]),
    file_storage_service: S3FileStorageService = Depends(Provide[Container.file_storage_service]),
    audio_generation_service: CannedAudioService = Depends(Provide[Container.canned_audio_service]),
    db: AsyncSession = Depends(get_db)
):
    """Admin import endpoint - no auth for MVP testing"""
    try:
        # Read Excel file
        excel_data = await excel_file.read()
        
        # Parse and validate Excel
        menu_data = excel_import_service.parse_excel(excel_data)
        
        # Import restaurant data
        result = await restaurant_import_service.import_restaurant_data(
            menu_data=menu_data,
            overwrite_existing=overwrite,
            db=db
        )
        
        # Upload images if provided
        if images:
            await file_storage_service.upload_images(
                restaurant_id=result.data.get('restaurant_id'),
                images=images
            )
        
        # Generate audio if requested
        if generate_audio:
            await audio_generation_service.generate_canned_audio(
                restaurant_id=result.data.get('restaurant_id'),
                db=db
            )
        
        return {
            "message": "Import completed successfully",
            "data": result.data,
            "restaurant_id": result.data.get('restaurant_id'),
            "restaurant_name": result.data.get('restaurant_name')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )