"""
Ingredient model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, CheckConstraint, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Ingredient name - required, max 100 characters"
    )
    description = Column(
        String(255), 
        nullable=True,
        comment="Ingredient description"
    )
    restaurant_id = Column(
        Integer, 
        ForeignKey("restaurants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to restaurant"
    )
    is_allergen = Column(
        Boolean, 
        default=False,
        comment="Whether this ingredient is a common allergen"
    )
    allergen_type = Column(
        String(50), 
        nullable=True,
        comment="Type of allergen (nuts, dairy, gluten, etc.)"
    )
    unit_cost = Column(
        Numeric(10, 2), 
        nullable=False,
        default=0.0,
        comment="Cost per unit of this ingredient (e.g., cost per slice of cheese)"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the ingredient was created"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "length(name) >= 2", 
            name="ck_ingredient_name_min_length"
        ),
        CheckConstraint(
            "length(description) >= 5 OR description IS NULL", 
            name="ck_ingredient_description_min_length"
        ),
        CheckConstraint(
            "unit_cost >= 0", 
            name="ck_ingredient_unit_cost_positive"
        ),
        CheckConstraint(
            "unit_cost <= 999999.99", 
            name="ck_ingredient_unit_cost_max"
        ),
        # Ensure unique ingredient names per restaurant
        CheckConstraint(
            "true",  # This will be handled by unique index
            name="ck_ingredient_unique_name_per_restaurant"
        ),
    )
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="ingredients")
    menu_item_ingredients = relationship("MenuItemIngredient", back_populates="ingredient")
    inventory = relationship("Inventory", back_populates="ingredient", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ingredient(id={self.id}, name='{self.name}', restaurant_id={self.restaurant_id})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "restaurant_id": self.restaurant_id,
            "is_allergen": self.is_allergen,
            "allergen_type": self.allergen_type,
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
