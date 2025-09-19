"""
User repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with user-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User or None: User instance if found
        """
        return await self.get_by_field("email", email)
    
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """
        Get user by phone number
        
        Args:
            phone: User phone number
            
        Returns:
            User or None: User instance if found
        """
        return await self.get_by_field("phone", phone)
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of active users
        """
        return await self.get_all_by_filter({"is_active": True}, skip, limit)
    
    async def get_user_with_orders(self, user_id: int) -> Optional[User]:
        """
        Get user with their orders loaded
        
        Args:
            user_id: User ID
            
        Returns:
            User or None: User with orders if found
        """
        return await self.get_by_id_with_relations(user_id, ["orders"])
    
    async def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Search users by name or email
        
        Args:
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of matching users
        """
        result = await self.db.execute(
            select(User)
            .where(
                User.email.ilike(f"%{search_term}%") |
                User.first_name.ilike(f"%{search_term}%") |
                User.last_name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_users_by_name(self, first_name: str = None, last_name: str = None, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users by first name and/or last name
        
        Args:
            first_name: First name to search for
            last_name: Last name to search for
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of matching users
        """
        query = select(User)
        
        if first_name:
            query = query.where(User.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.where(User.last_name.ilike(f"%{last_name}%"))
        
        result = await self.db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def count_active_users(self) -> int:
        """
        Count active users
        
        Returns:
            int: Number of active users
        """
        return await self.count({"is_active": True})
    
    async def is_email_taken(self, email: str, exclude_user_id: int = None) -> bool:
        """
        Check if email is already taken by another user
        
        Args:
            email: Email to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            bool: True if email is taken, False otherwise
        """
        query = select(User.id).where(User.email == email)
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def is_phone_taken(self, phone: str, exclude_user_id: int = None) -> bool:
        """
        Check if phone number is already taken by another user
        
        Args:
            phone: Phone number to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            bool: True if phone is taken, False otherwise
        """
        query = select(User.id).where(User.phone == phone)
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
