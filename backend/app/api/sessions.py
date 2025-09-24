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
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service])
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
        
        # Use OrderService.handle_new_car to create both session and order
        from ..services.order_service import OrderService
        from ..services.customization_validation_service import CustomizationValidationService
        from ..core.service_factory import ServiceFactory
        from ..core.container import Container
        
        # Create service factory and order service using the real container
        container = Container()
        service_factory = ServiceFactory(container)
        order_service = service_factory.create_order_service(db)
        
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
        
        return {
            "success": True,
            "message": "Current session retrieved",
            "data": {
                "session": current_session
            }
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
