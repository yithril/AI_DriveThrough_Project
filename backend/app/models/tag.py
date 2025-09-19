"""
Tag model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Tag name - required, max 50 characters"
    )
    color = Column(
        String(7), 
        default="#6B7280",
        comment="Tag color in hex format"
    )
    restaurant_id = Column(
        Integer, 
        ForeignKey("restaurants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to restaurant"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the tag was created"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "length(name) >= 2", 
            name="ck_tag_name_min_length"
        ),
        CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'", 
            name="ck_tag_color_format"
        ),
        # Ensure unique tag names per restaurant
        CheckConstraint(
            "true",  # This will be handled by unique index
            name="ck_tag_unique_name_per_restaurant"
        ),
    )
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="tags")
    menu_item_tags = relationship("MenuItemTag", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "restaurant_id": self.restaurant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "menu_items_count": len(self.menu_item_tags) if self.menu_item_tags else 0
        }
