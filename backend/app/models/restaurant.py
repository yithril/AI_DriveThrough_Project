"""
Restaurant model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Restaurant name - required, max 100 characters"
    )
    logo_url = Column(
        String(255), 
        nullable=True,
        comment="URL to restaurant logo image"
    )
    primary_color = Column(
        String(7), 
        default="#FF6B35",
        comment="Primary brand color in hex format"
    )
    secondary_color = Column(
        String(7), 
        default="#F7931E",
        comment="Secondary brand color in hex format"
    )
    description = Column(
        Text, 
        nullable=True,
        comment="Restaurant description"
    )
    address = Column(
        String(255),
        nullable=True,
        comment="Restaurant address"
    )
    phone = Column(
        String(20),
        nullable=True,
        comment="Restaurant phone number"
    )
    hours = Column(
        String(100),
        nullable=True,
        comment="Restaurant operating hours"
    )
    is_active = Column(
        Boolean, 
        default=True,
        comment="Whether the restaurant is active"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the restaurant was created"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="When the restaurant was last updated"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "length(name) >= 2", 
            name="ck_restaurant_name_min_length"
        ),
        CheckConstraint(
            "primary_color ~ '^#[0-9A-Fa-f]{6}$'", 
            name="ck_restaurant_primary_color_format"
        ),
        CheckConstraint(
            "secondary_color ~ '^#[0-9A-Fa-f]{6}$'", 
            name="ck_restaurant_secondary_color_format"
        ),
    )
    
    # Relationships
    categories = relationship("Category", back_populates="restaurant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="restaurant", cascade="all, delete-orphan")
    ingredients = relationship("Ingredient", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Restaurant(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "description": self.description,
            "address": self.address,
            "phone": self.phone,
            "hours": self.hours,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
