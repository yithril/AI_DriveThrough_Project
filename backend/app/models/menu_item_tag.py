"""
MenuItemTag model (Many-to-Many relationship) with validation
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base


class MenuItemTag(Base):
    __tablename__ = "menu_item_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(
        Integer, 
        ForeignKey("menu_items.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to menu item"
    )
    tag_id = Column(
        Integer, 
        ForeignKey("tags.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to tag"
    )
    
    # Table constraints for validation
    __table_args__ = (
        # Ensure unique combinations of menu_item_id and tag_id
        UniqueConstraint(
            'menu_item_id', 
            'tag_id', 
            name='uq_menu_item_tag'
        ),
    )
    
    # Relationships
    menu_item = relationship("MenuItem", back_populates="tags")
    tag = relationship("Tag", back_populates="menu_item_tags")
    
    def __repr__(self):
        return f"<MenuItemTag(menu_item_id={self.menu_item_id}, tag_id={self.tag_id})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "tag_id": self.tag_id,
            "tag": self.tag.to_dict() if self.tag else None
        }
