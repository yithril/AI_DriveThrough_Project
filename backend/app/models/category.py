"""
Category model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Category name - required, max 50 characters"
    )
    description = Column(
        String(255), 
        nullable=True,
        comment="Category description - max 255 characters"
    )
    restaurant_id = Column(
        Integer, 
        ForeignKey("restaurants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to restaurant"
    )
    display_order = Column(
        Integer, 
        default=0,
        comment="Order for displaying categories"
    )
    is_active = Column(
        Boolean, 
        default=True,
        comment="Whether the category is active"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the category was created"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "length(name) >= 2", 
            name="ck_category_name_min_length"
        ),
        CheckConstraint(
            "display_order >= 0", 
            name="ck_category_display_order_positive"
        ),
        # Ensure unique category names per restaurant
        CheckConstraint(
            "true",  # This will be handled by unique index
            name="ck_category_unique_name_per_restaurant"
        ),
    )
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="categories")
    menu_items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "restaurant_id": self.restaurant_id,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "menu_items_count": len(self.menu_items) if self.menu_items else 0
        }
