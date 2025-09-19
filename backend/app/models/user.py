"""
User model with validation
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="User email address - required, unique"
    )
    phone = Column(
        String(20), 
        nullable=True,
        index=True,
        comment="User phone number - optional"
    )
    first_name = Column(
        String(50), 
        nullable=True,
        comment="User first name - optional"
    )
    last_name = Column(
        String(50), 
        nullable=True,
        comment="User last name - optional"
    )
    is_active = Column(
        Boolean, 
        default=True,
        comment="Whether the user account is active"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the user account was created"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="When the user account was last updated"
    )
    
    # Table constraints for validation
    __table_args__ = (
        CheckConstraint(
            "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", 
            name="ck_user_email_format"
        ),
        CheckConstraint(
            "length(email) >= 5", 
            name="ck_user_email_min_length"
        ),
        CheckConstraint(
            "length(first_name) >= 2 OR first_name IS NULL", 
            name="ck_user_first_name_min_length"
        ),
        CheckConstraint(
            "length(last_name) >= 2 OR last_name IS NULL", 
            name="ck_user_last_name_min_length"
        ),
        CheckConstraint(
            "length(phone) >= 10 OR phone IS NULL", 
            name="ck_user_phone_min_length"
        ),
        # Index for faster queries
        Index('ix_users_email_active', 'email', 'is_active'),
    )
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "orders_count": len(self.orders) if self.orders else 0
        }
    
    @property
    def full_name(self):
        """Return full name if available"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return None
