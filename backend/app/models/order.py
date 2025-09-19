"""
Order model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(
        String(100), 
        nullable=True,
        comment="Customer name - optional for anonymous orders"
    )
    customer_phone = Column(
        String(20), 
        nullable=True,
        comment="Customer phone number - optional"
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        index=True,
        comment="Reference to registered user - optional"
    )
    restaurant_id = Column(
        Integer, 
        ForeignKey("restaurants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to restaurant"
    )
    status = Column(
        Enum(OrderStatus), 
        default=OrderStatus.PENDING,
        nullable=False,
        comment="Current order status"
    )
    subtotal = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Subtotal before tax"
    )
    tax_amount = Column(
        Numeric(10, 2), 
        default=0,
        comment="Tax amount"
    )
    total_amount = Column(
        Numeric(10, 2), 
        nullable=False,
        comment="Total amount including tax"
    )
    special_instructions = Column(
        Text, 
        nullable=True,
        comment="Special instructions for the order"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the order was created"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="When the order was last updated"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "subtotal >= 0", 
            name="ck_order_subtotal_positive"
        ),
        CheckConstraint(
            "tax_amount >= 0", 
            name="ck_order_tax_positive"
        ),
        CheckConstraint(
            "total_amount >= 0", 
            name="ck_order_total_positive"
        ),
        CheckConstraint(
            "total_amount >= subtotal", 
            name="ck_order_total_ge_subtotal"
        ),
        CheckConstraint(
            "length(customer_name) >= 2 OR customer_name IS NULL", 
            name="ck_order_customer_name_min_length"
        ),
        CheckConstraint(
            "length(customer_phone) >= 10 OR customer_phone IS NULL", 
            name="ck_order_customer_phone_min_length"
        ),
    )
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="orders")
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, status='{self.status}', total={self.total_amount})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "user_id": self.user_id,
            "restaurant_id": self.restaurant_id,
            "status": self.status.value if self.status else None,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "special_instructions": self.special_instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "order_items": [item.to_dict() for item in self.order_items] if self.order_items else []
        }
    
    @property
    def formatted_total(self):
        """Return formatted total amount string"""
        return f"${self.total_amount:.2f}" if self.total_amount else "$0.00"
    
    @property
    def item_count(self):
        """Return total number of items in the order"""
        return sum(item.quantity for item in self.order_items) if self.order_items else 0
