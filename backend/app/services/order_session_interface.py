"""
Interface for OrderSessionService - Redis primary with PostgreSQL fallback
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession


class OrderSessionInterface(ABC):
    """
    Abstract interface for order and session storage operations
    Provides Redis primary storage with PostgreSQL fallback
    """

    @abstractmethod
    async def is_redis_available(self) -> bool:
        """
        Check if Redis is available and connected
        
        Returns:
            bool: True if Redis is available, False otherwise
        """
        pass

    @abstractmethod
    async def get_current_session_id(self) -> Optional[str]:
        """
        Get the current active session ID
        
        Returns:
            str: Current session ID if exists, None otherwise
        """
        pass

    @abstractmethod
    async def set_current_session_id(self, session_id: str, ttl: int = 900) -> bool:
        """
        Set the current active session ID
        
        Args:
            session_id: Session ID to set as current
            ttl: Time to live in seconds (default 15 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def clear_current_session_id(self) -> bool:
        """
        Clear the current active session ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            dict: Session data if exists, None otherwise
        """
        pass

    @abstractmethod
    async def create_session(self, session_data: Dict[str, Any], ttl: int = 900) -> bool:
        """
        Create a new session
        
        Args:
            session_data: Session data dictionary
            ttl: Time to live in seconds (default 15 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def update_session(self, session_id: str, updates: Dict[str, Any], ttl: int = 900) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID to update
            updates: Data to merge into session
            ttl: Time to live in seconds (default 15 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_order(self, db: AsyncSession, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order data (Redis first, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_id: Order ID to retrieve
            
        Returns:
            dict: Order data if exists, None otherwise
        """
        pass

    @abstractmethod
    async def create_order(self, db: AsyncSession, order_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Create a new order (Redis primary, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_data: Order data dictionary
            ttl: Time to live in seconds for Redis (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def update_order(self, db: AsyncSession, order_id: str, updates: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Update order data (Redis primary, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_id: Order ID to update
            updates: Data to merge into order
            ttl: Time to live in seconds for Redis (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete_order(self, db: AsyncSession, order_id: str) -> bool:
        """
        Delete an order (Redis primary, PostgreSQL fallback)
        
        Args:
            db: Database session for PostgreSQL fallback
            order_id: Order ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def archive_order_to_postgres(self, db: AsyncSession, order_data: Dict[str, Any]) -> Optional[int]:
        """
        Archive order from Redis to PostgreSQL
        
        Args:
            db: Database session
            order_data: Order data to archive
            
        Returns:
            int: PostgreSQL order ID if successful, None otherwise
        """
        pass
