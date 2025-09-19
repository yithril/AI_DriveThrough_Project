"""
Session management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from pydantic import BaseModel, ValidationError
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.container import Container
from ..core.database import get_db
from ..services.order_service import OrderService
import logging

logger = logging.getLogger(__name__)

class NewCarRequest(BaseModel):
    restaurant_id: int

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/new-car")
@inject
async def new_car(
    request_data: NewCarRequest,
    db: AsyncSession = Depends(get_db),
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Handle new car arriving (NEW_CAR event)
    
    Args:
        request_data: New car request data
        
    Returns:
        dict: New session data
    """
    try:
        logger.info(f"Received new car request: {request_data}")
        
        # Use the injected order service with database session from FastAPI DI
        result = await order_service.handle_new_car(db, request_data.restaurant_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle new car: {str(e)}"
        )


@router.post("/next-car")
@inject
async def next_car(
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Handle next car (NEXT_CAR event)
    
    Returns:
        dict: Result of operation
    """
    try:
        result = await order_service.handle_next_car()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return {
            "success": True,
            "message": result.message
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle next car: {str(e)}"
        )


@router.get("/current")
async def get_current_session(
    order_service: OrderService = Depends(Container.order_service)
):
    """
    Get current active session
    
    Returns:
        dict: Current session data
    """
    try:
        result = await order_service.get_current_session()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current session: {str(e)}"
        )


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    updates: dict,
    order_service: OrderService = Depends(Container.order_service)
):
    """
    Update session data (ORDER_ACTIVITY event)
    
    Args:
        session_id: Session ID to update
        updates: Data to merge into session
        
    Returns:
        dict: Updated session data
    """
    try:
        result = await order_service.update_session(session_id, updates)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )
