"""
Menu Item Tag repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.menu_item_tag import MenuItemTag


class MenuItemTagRepository(BaseRepository[MenuItemTag]):
    """
    Repository for MenuItemTag model with menu item tag-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(MenuItemTag, db)
    
    async def get_by_menu_item_id(self, menu_item_id: int) -> List[MenuItemTag]:
        """
        Get all tags for a specific menu item
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            List[MenuItemTag]: List of menu item tags
        """
        result = await self.db.execute(
            select(MenuItemTag).where(MenuItemTag.menu_item_id == menu_item_id)
        )
        return result.scalars().all()
    
    async def get_by_tag_id(self, tag_id: int) -> List[MenuItemTag]:
        """
        Get all menu items for a specific tag
        
        Args:
            tag_id: Tag ID
            
        Returns:
            List[MenuItemTag]: List of menu item tags
        """
        result = await self.db.execute(
            select(MenuItemTag).where(MenuItemTag.tag_id == tag_id)
        )
        return result.scalars().all()
    
    async def get_menu_item_with_tags(self, menu_item_id: int) -> Optional[MenuItemTag]:
        """
        Get menu item tag with relations loaded
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            MenuItemTag or None: Menu item tag with relations if found
        """
        return await self.get_by_id_with_relations(menu_item_id, ["menu_item", "tag"])
