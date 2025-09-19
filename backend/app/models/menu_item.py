"""
MenuItem model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Menu item name - required, max 100 characters"
    )
    description = Column(
        Text, 
        nullable=True,
        comment="Menu item description"
    )
    price = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Menu item price - required, max 99999999.99"
    )
    image_url = Column(
        String(255), 
        nullable=True,
        comment="URL to menu item image"
    )
    category_id = Column(
        Integer, 
        ForeignKey("categories.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to category"
    )
    restaurant_id = Column(
        Integer, 
        ForeignKey("restaurants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to restaurant"
    )
    is_available = Column(
        Boolean, 
        default=True,
        comment="Whether the menu item is available for ordering"
    )
    is_upsell = Column(
        Boolean, 
        default=False,
        comment="Whether this item should be suggested for upselling"
    )
    is_special = Column(
        Boolean, 
        default=False,
        comment="Whether this item is a special/featured item"
    )
    prep_time_minutes = Column(
        Integer, 
        default=5,
        comment="Estimated preparation time in minutes"
    )
    display_order = Column(
        Integer, 
        default=0,
        comment="Order for displaying menu items within category"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the menu item was created"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="When the menu item was last updated"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "length(name) >= 2", 
            name="ck_menu_item_name_min_length"
        ),
        CheckConstraint(
            "price >= 0", 
            name="ck_menu_item_price_positive"
        ),
        CheckConstraint(
            "price <= 999999.99", 
            name="ck_menu_item_price_max"
        ),
        CheckConstraint(
            "prep_time_minutes >= 1", 
            name="ck_menu_item_prep_time_min"
        ),
        CheckConstraint(
            "prep_time_minutes <= 120", 
            name="ck_menu_item_prep_time_max"
        ),
        CheckConstraint(
            "display_order >= 0", 
            name="ck_menu_item_display_order_positive"
        ),
    )
    
    # Relationships
    category = relationship("Category", back_populates="menu_items")
    restaurant = relationship("Restaurant", back_populates="menu_items")
    tags = relationship("MenuItemTag", back_populates="menu_item", cascade="all, delete-orphan")
    ingredients = relationship("MenuItemIngredient", back_populates="menu_item", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="menu_item")
    
    def __repr__(self):
        return f"<MenuItem(id={self.id}, name='{self.name}', price={self.price})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else 0.0,
            "image_url": self.image_url,
            "category_id": self.category_id,
            "restaurant_id": self.restaurant_id,
            "is_available": self.is_available,
            "is_upsell": self.is_upsell,
            "is_special": self.is_special,
            "prep_time_minutes": self.prep_time_minutes,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": [tag.tag.to_dict() for tag in self.tags] if self.tags else []
        }
    
    @property
    def formatted_price(self):
        """Return formatted price string"""
        return f"${self.price:.2f}" if self.price else "$0.00"
