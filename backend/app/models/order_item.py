"""
OrderItem model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, 
        ForeignKey("orders.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to order"
    )
    menu_item_id = Column(
        Integer, 
        ForeignKey("menu_items.id", ondelete="RESTRICT"), 
        nullable=False,
        index=True,
        comment="Reference to menu item"
    )
    quantity = Column(
        Integer, 
        nullable=False, 
        default=1,
        comment="Quantity of the menu item"
    )
    unit_price = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Price per unit at time of order"
    )
    total_price = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Total price for this line item (quantity * unit_price)"
    )
    special_instructions = Column(
        String(255), 
        nullable=True,
        comment="Special instructions for this specific item"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the order item was created"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "quantity > 0", 
            name="ck_order_item_quantity_positive"
        ),
        CheckConstraint(
            "quantity <= 10", 
            name="ck_order_item_quantity_max"
        ),
        CheckConstraint(
            "unit_price >= 0", 
            name="ck_order_item_unit_price_positive"
        ),
        CheckConstraint(
            "total_price >= 0", 
            name="ck_order_item_total_price_positive"
        ),
        CheckConstraint(
            "total_price = quantity * unit_price", 
            name="ck_order_item_total_price_calculation"
        ),
    )
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    menu_item = relationship("MenuItem", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, menu_item_id={self.menu_item_id}, quantity={self.quantity})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "special_instructions": self.special_instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "menu_item": self.menu_item.to_dict() if self.menu_item else None
        }
    
    @property
    def formatted_unit_price(self):
        """Return formatted unit price string"""
        return f"${self.unit_price:.2f}" if self.unit_price else "$0.00"
    
    @property
    def formatted_total_price(self):
        """Return formatted total price string"""
        return f"${self.total_price:.2f}" if self.total_price else "$0.00"
