"""
MenuItemIngredient model (Many-to-Many with quantity and units)
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class MenuItemIngredient(Base):
    __tablename__ = "menu_item_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(
        Integer, 
        ForeignKey("menu_items.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to menu item"
    )
    ingredient_id = Column(
        Integer, 
        ForeignKey("ingredients.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to ingredient"
    )
    quantity = Column(
        Numeric(8, 2), 
        nullable=False,
        comment="Quantity of ingredient (e.g., 1.0, 2.5)"
    )
    unit = Column(
        String(20), 
        nullable=False,
        comment="Unit of measurement (pieces, oz, cups, lbs, etc.)"
    )
    is_optional = Column(
        Boolean, 
        default=False,
        comment="Whether this ingredient is optional (e.g., 'extra cheese')"
    )
    additional_cost = Column(
        Numeric(10, 2), 
        nullable=False,
        default=0.0,
        comment="Additional cost when adding extra of this ingredient"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the menu item ingredient was created"
    )
    
    # Table constraints for validation
    __table_args__ = (
        # Ensure unique combinations of menu_item_id and ingredient_id
        UniqueConstraint(
            'menu_item_id', 
            'ingredient_id', 
            name='uq_menu_item_ingredient'
        ),
        CheckConstraint(
            "quantity > 0", 
            name="ck_menu_item_ingredient_quantity_positive"
        ),
        CheckConstraint(
            "quantity <= 1000", 
            name="ck_menu_item_ingredient_quantity_max"
        ),
        CheckConstraint(
            "length(unit) >= 1", 
            name="ck_menu_item_ingredient_unit_min_length"
        ),
        CheckConstraint(
            "length(unit) <= 20", 
            name="ck_menu_item_ingredient_unit_max_length"
        ),
        CheckConstraint(
            "additional_cost >= 0", 
            name="ck_menu_item_ingredient_additional_cost_positive"
        ),
        CheckConstraint(
            "additional_cost <= 999999.99", 
            name="ck_menu_item_ingredient_additional_cost_max"
        ),
    )
    
    # Relationships
    menu_item = relationship("MenuItem", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="menu_item_ingredients")
    
    def __repr__(self):
        return f"<MenuItemIngredient(menu_item_id={self.menu_item_id}, ingredient_id={self.ingredient_id}, quantity={self.quantity} {self.unit})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "ingredient_id": self.ingredient_id,
            "quantity": float(self.quantity) if self.quantity else 0.0,
            "unit": self.unit,
            "is_optional": self.is_optional,
            "additional_cost": float(self.additional_cost) if self.additional_cost else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ingredient": self.ingredient.to_dict() if self.ingredient else None
        }
