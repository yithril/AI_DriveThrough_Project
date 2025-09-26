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
from ..services.order_session_service import OrderSessionService
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
    
    Creates both a session and an order, just like OrderService.handle_new_car
    
    Args:
        request_data: New car request data
        
    Returns:
        dict: New session and order data
    """
    try:
        logger.info(f"Received new car request: {request_data}")
        
        # Create both session and order using OrderService.handle_new_car
        order_result = await order_service.handle_new_car(
            db=db,
            restaurant_id=request_data.restaurant_id,
            customer_name=None
        )
        
        if not order_result.is_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create session and order: {order_result.message}"
            )
        
        # Extract session data from the result
        session_data = order_result.data.get("session", {})
        session_id = session_data.get("id")
        greeting_audio_url = order_result.data.get("greeting_audio_url")
        
        return {
            "success": True,
            "message": "New car session and order created",
            "data": {
                "session_id": session_id,
                "restaurant_id": request_data.restaurant_id,
                "greeting_audio_url": greeting_audio_url,
                "session": session_data
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle new car: {str(e)}"
        )


@router.post("/next-car")
@inject
async def next_car(
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service])
):
    """
    Handle next car (NEXT_CAR event)
    
    Returns:
        dict: Result of operation
    """
    try:
        # Clear current session
        await order_session_service.clear_current_session_id()
        logger.info("Next car handled - cleared current session")
        
        return {
            "success": True,
            "message": "Next car handled - session cleared, ready for new session"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle next car: {str(e)}"
        )


@router.get("/current")
@inject
async def get_current_session(
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service])
):
    """
    Get current active session
    
    Returns:
        dict: Current session data
    """
    try:
        # Get current session from OrderSessionService
        current_session = await order_session_service.get_current_session()
        
        if not current_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current session. Please call /new-car first to create a session."
            )
        
        # Clean up session data for frontend (remove customer name but keep order_id)
        clean_session = {
            "id": current_session.get('id'),
            "restaurant_id": current_session.get('restaurant_id'),
            "order_id": current_session.get('order_id'),
            "status": current_session.get('status'),
            "created_at": current_session.get('created_at'),
            "updated_at": current_session.get('updated_at')
        }
        
        return {
            "success": True,
            "message": "Current session retrieved",
            "data": {
                "session": clean_session
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current session: {str(e)}"
        )


@router.get("/current-order")
@inject
async def get_current_order(
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current order with items for frontend display
    
    Returns:
        dict: Current order data with items
    """
    try:
        # Get current session
        current_session = await order_session_service.get_current_session()
        
        if not current_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current session. Please call /new-car first to create a session."
            )
        
        # Get the order ID from session
        session_id = current_session.get('id')
        order_id = current_session.get('order_id')
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No session ID found in current session"
            )
        
        if not order_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No order ID found in current session"
            )
        
        # Get the order data using the order ID
        order_data = await order_session_service.get_order(db, order_id)
        
        if not order_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No order found for current session"
            )
        
        # Return clean order data for frontend
        return {
            "success": True,
            "message": "Current order retrieved",
            "data": {
                "order": {
                    "id": order_data.get('id'),
                    "items": order_data.get('items', []),
                    "subtotal": order_data.get('subtotal', 0.0),
                    "tax_amount": order_data.get('tax_amount', 0.0),
                    "total_amount": order_data.get('total_amount', 0.0),
                    "status": order_data.get('status'),
                    "created_at": order_data.get('created_at'),
                    "updated_at": order_data.get('updated_at')
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current order: {str(e)}"
        )


@router.put("/{session_id}")
@inject
async def update_session(
    session_id: str,
    updates: dict,
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service])
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
        # For now, we'll return a simple success since the workflow manages session updates
        # In the future, this could be used for manual session updates if needed
        logger.info(f"Session {session_id} update requested: {updates}")
        
        return {
            "success": True,
            "message": "Session update handled by workflow",
            "data": {
                "session_id": session_id,
                "updates": updates
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )
