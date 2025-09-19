"""
Inventory model for tracking ingredient stock levels
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(
        Integer, 
        ForeignKey("ingredients.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to ingredient"
    )
    current_stock = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Current stock quantity"
    )
    min_stock_level = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Minimum stock level before reorder alert"
    )
    max_stock_level = Column(
        Numeric(10, 2), 
        nullable=True,
        comment="Maximum stock level for ordering"
    )
    unit = Column(
        String(20), 
        nullable=False,
        comment="Unit of measurement (pieces, oz, lbs, etc.)"
    )
    cost_per_unit = Column(
        Numeric(10, 2), 
        nullable=True,
        comment="Cost per unit for inventory valuation"
    )
    supplier = Column(
        String(100), 
        nullable=True,
        comment="Supplier name"
    )
    supplier_contact = Column(
        String(100), 
        nullable=True,
        comment="Supplier contact information"
    )
    is_active = Column(
        Boolean, 
        default=True,
        comment="Whether this inventory item is active"
    )
    last_updated = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        comment="When the inventory was last updated"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the inventory record was created"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "current_stock >= 0", 
            name="ck_inventory_current_stock_positive"
        ),
        CheckConstraint(
            "min_stock_level >= 0", 
            name="ck_inventory_min_stock_positive"
        ),
        CheckConstraint(
            "max_stock_level IS NULL OR max_stock_level >= min_stock_level", 
            name="ck_inventory_max_stock_gte_min"
        ),
        CheckConstraint(
            "cost_per_unit IS NULL OR cost_per_unit >= 0", 
            name="ck_inventory_cost_per_unit_positive"
        ),
        CheckConstraint(
            "length(unit) >= 1", 
            name="ck_inventory_unit_min_length"
        ),
        CheckConstraint(
            "length(unit) <= 20", 
            name="ck_inventory_unit_max_length"
        ),
        # Ensure one inventory record per ingredient
        CheckConstraint(
            "true",  # This will be handled by unique constraint
            name="ck_inventory_unique_per_ingredient"
        ),
    )
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="inventory")
    
    def __repr__(self):
        return f"<Inventory(ingredient_id={self.ingredient_id}, current_stock={self.current_stock}, unit='{self.unit}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "ingredient_id": self.ingredient_id,
            "current_stock": float(self.current_stock) if self.current_stock else 0.0,
            "min_stock_level": float(self.min_stock_level) if self.min_stock_level else 0.0,
            "max_stock_level": float(self.max_stock_level) if self.max_stock_level else None,
            "unit": self.unit,
            "cost_per_unit": float(self.cost_per_unit) if self.cost_per_unit else None,
            "supplier": self.supplier,
            "supplier_contact": self.supplier_contact,
            "is_active": self.is_active,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_low_stock": self.is_low_stock,
            "is_out_of_stock": self.is_out_of_stock,
            "total_value": self.total_value
        }
    
    @property
    def is_low_stock(self) -> bool:
        """Check if current stock is below minimum level"""
        return self.current_stock <= self.min_stock_level
    
    @property
    def is_out_of_stock(self) -> bool:
        """Check if current stock is zero"""
        return self.current_stock <= 0
    
    @property
    def total_value(self) -> float:
        """Calculate total inventory value"""
        if self.cost_per_unit and self.current_stock:
            return float(self.cost_per_unit * self.current_stock)
        return 0.0
    
    @property
    def stock_status(self) -> str:
        """Get human-readable stock status"""
        if self.is_out_of_stock:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        else:
            return "In Stock"
