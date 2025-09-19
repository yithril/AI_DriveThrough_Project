"""
Tag repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.tag import Tag


class TagRepository(BaseRepository[Tag]):
    """
    Repository for Tag model with tag-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Tag, db)
    
    async def get_by_name_and_restaurant(self, name: str, restaurant_id: int) -> Optional[Tag]:
        """
        Get tag by name and restaurant
        
        Args:
            name: Tag name
            restaurant_id: Restaurant ID
            
        Returns:
            Tag or None: Tag instance if found
        """
        result = await self.db.execute(
            select(Tag)
            .where(Tag.name == name, Tag.restaurant_id == restaurant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_restaurant(self, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Tag]:
        """
        Get all tags for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Tag]: List of tags for the restaurant
        """
        return await self.get_all_by_filter({"restaurant_id": restaurant_id}, skip, limit)
    
    async def get_tag_with_menu_items(self, tag_id: int) -> Optional[Tag]:
        """
        Get tag with its associated menu items loaded
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag or None: Tag with menu items if found
        """
        return await self.get_by_id_with_relations(tag_id, ["menu_item_tags"])
    
    async def search_tags(self, restaurant_id: int, search_term: str, skip: int = 0, limit: int = 100) -> List[Tag]:
        """
        Search tags by name within a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Tag]: List of matching tags
        """
        result = await self.db.execute(
            select(Tag)
            .where(
                Tag.restaurant_id == restaurant_id,
                Tag.name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_by_restaurant(self, restaurant_id: int) -> int:
        """
        Count tags for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            int: Number of tags for the restaurant
        """
        return await self.count({"restaurant_id": restaurant_id})
