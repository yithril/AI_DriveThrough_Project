"""
Order result DTO for AI command responses
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass


class OrderResultStatus(str, Enum):
    """Status of an order operation"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class OrderResult:
    """
    Result object for AI order operations
    Provides clear success/failure feedback to AI
    """
    
    status: OrderResultStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        """Ensure errors and warnings are lists if provided"""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @classmethod
    def success(cls, message: str, data: Optional[Dict[str, Any]] = None) -> "OrderResult":
        """Create a successful result"""
        return cls(
            status=OrderResultStatus.SUCCESS,
            message=message,
            data=data
        )
    
    @classmethod
    def error(cls, message: str, errors: Optional[List[str]] = None) -> "OrderResult":
        """Create an error result"""
        return cls(
            status=OrderResultStatus.ERROR,
            message=message,
            errors=errors or []
        )
    
    @classmethod
    def warning(cls, message: str, warnings: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None) -> "OrderResult":
        """Create a warning result"""
        return cls(
            status=OrderResultStatus.WARNING,
            message=message,
            warnings=warnings or [],
            data=data
        )
    
    @classmethod
    def partial_success(cls, message: str, warnings: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None) -> "OrderResult":
        """Create a partial success result"""
        return cls(
            status=OrderResultStatus.PARTIAL_SUCCESS,
            message=message,
            warnings=warnings or [],
            data=data
        )
    
    @property
    def is_success(self) -> bool:
        """Check if operation was successful"""
        return self.status in [OrderResultStatus.SUCCESS, OrderResultStatus.PARTIAL_SUCCESS]
    
    @property
    def is_error(self) -> bool:
        """Check if operation failed"""
        return self.status == OrderResultStatus.ERROR
    
    @property
    def has_warnings(self) -> bool:
        """Check if operation has warnings"""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "is_success": self.is_success,
            "is_error": self.is_error,
            "has_warnings": self.has_warnings
        }
    
    def __str__(self) -> str:
        """String representation for logging"""
        result = f"OrderResult({self.status.value}): {self.message}"
        if self.errors:
            result += f" | Errors: {', '.join(self.errors)}"
        if self.warnings:
            result += f" | Warnings: {', '.join(self.warnings)}"
        return result
