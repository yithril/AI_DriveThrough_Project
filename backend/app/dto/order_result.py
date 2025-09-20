"""
Order result DTO for AI command responses
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict


class OrderResultStatus(str, Enum):
    """Status of an order operation"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL_SUCCESS = "partial_success"


class ErrorCategory(str, Enum):
    """Category of error for better AI follow-up handling"""
    VALIDATION = "validation"      # Input validation errors (unclear input, malformed data)
    BUSINESS = "business"          # Business logic errors (item unavailable, inventory issues)
    SYSTEM = "system"             # System/technical errors (database issues, API failures)


class ErrorCode(str, Enum):
    """Specific error codes for granular error handling"""
    # Business errors
    ITEM_UNAVAILABLE = "item_unavailable"
    ITEM_NOT_FOUND = "item_not_found"
    SIZE_NOT_AVAILABLE = "size_not_available"
    OPTION_REQUIRED_MISSING = "option_required_missing"
    
    # Modifier errors
    MODIFIER_REMOVE_NOT_PRESENT = "modifier_remove_not_present"
    MODIFIER_ADD_NOT_ALLOWED = "modifier_add_not_allowed"
    MODIFIER_CONFLICT = "modifier_conflict"
    
    # Quantity/Inventory errors
    QUANTITY_EXCEEDS_LIMIT = "quantity_exceeds_limit"
    INVENTORY_SHORTAGE = "inventory_shortage"
    
    # Validation errors
    INVALID_INPUT_FORMAT = "invalid_input_format"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_QUANTITY = "invalid_quantity"
    
    # System errors
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    INTERNAL_ERROR = "internal_error"


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
    error_category: Optional[ErrorCategory] = None
    error_code: Optional[ErrorCode] = None
    
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
    def error(cls, message: str, errors: Optional[List[str]] = None, 
              error_category: Optional[ErrorCategory] = None, 
              error_code: Optional[ErrorCode] = None) -> "OrderResult":
        """Create an error result"""
        return cls(
            status=OrderResultStatus.ERROR,
            message=message,
            errors=errors or [],
            error_category=error_category,
            error_code=error_code
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
    
    @classmethod
    def validation_error(cls, message: str, errors: Optional[List[str]] = None, 
                         error_code: Optional[ErrorCode] = None) -> "OrderResult":
        """Create a validation error result"""
        return cls.error(message, errors, ErrorCategory.VALIDATION, error_code)
    
    @classmethod
    def business_error(cls, message: str, errors: Optional[List[str]] = None, 
                       error_code: Optional[ErrorCode] = None) -> "OrderResult":
        """Create a business logic error result"""
        return cls.error(message, errors, ErrorCategory.BUSINESS, error_code)
    
    @classmethod
    def system_error(cls, message: str, errors: Optional[List[str]] = None, 
                     error_code: Optional[ErrorCode] = None) -> "OrderResult":
        """Create a system error result"""
        return cls.error(message, errors, ErrorCategory.SYSTEM, error_code)
    
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
            "error_category": self.error_category.value if self.error_category else None,
            "error_code": self.error_code.value if self.error_code else None,
            "is_success": self.is_success,
            "is_error": self.is_error,
            "has_warnings": self.has_warnings
        }
    
    def __str__(self) -> str:
        """String representation for logging"""
        result = f"OrderResult({self.status.value}): {self.message}"
        if self.error_category:
            result += f" | Category: {self.error_category.value}"
        if self.error_code:
            result += f" | Code: {self.error_code.value}"
        if self.errors:
            result += f" | Errors: {', '.join(self.errors)}"
        if self.warnings:
            result += f" | Warnings: {', '.join(self.warnings)}"
        return result


class FollowUpAction(str, Enum):
    """Recommended follow-up action for AI agent"""
    CONTINUE = "continue"      # Continue with successful commands, mention issues
    ASK = "ask"               # Ask user for clarification or substitution
    STOP = "stop"             # Stop processing, ask user to retry


@dataclass
class CommandBatchResult:
    """
    Aggregated result of executing multiple commands
    Provides summary statistics and follow-up recommendations for AI
    """
    
    results: List[OrderResult]
    total_commands: int
    successful_commands: int
    failed_commands: int
    warnings_count: int
    errors_by_category: Dict[ErrorCategory, int]
    errors_by_code: Dict[ErrorCode, int]
    follow_up_action: FollowUpAction
    summary_message: str
    
    @classmethod
    def from_results(cls, results: List[OrderResult], command_names: Optional[List[str]] = None) -> "CommandBatchResult":
        """Create CommandBatchResult from a list of OrderResult objects"""
        total_commands = len(results)
        successful_commands = sum(1 for r in results if r.is_success)
        failed_commands = sum(1 for r in results if r.is_error)
        warnings_count = sum(1 for r in results if r.has_warnings)
        
        # Group errors by category and code
        errors_by_category = defaultdict(int)
        errors_by_code = defaultdict(int)
        
        for result in results:
            if result.error_category:
                errors_by_category[result.error_category] += 1
            if result.error_code:
                errors_by_code[result.error_code] += 1
        
        # Determine follow-up action based on error types
        follow_up_action = cls._determine_follow_up_action(errors_by_category, failed_commands, total_commands)
        
        # Generate summary message
        summary_message = cls._generate_summary_message(
            total_commands, successful_commands, failed_commands, 
            warnings_count, errors_by_category, command_names
        )
        
        return cls(
            results=results,
            total_commands=total_commands,
            successful_commands=successful_commands,
            failed_commands=failed_commands,
            warnings_count=warnings_count,
            errors_by_category=dict(errors_by_category),
            errors_by_code=dict(errors_by_code),
            follow_up_action=follow_up_action,
            summary_message=summary_message
        )
    
    @staticmethod
    def _determine_follow_up_action(errors_by_category: Dict[ErrorCategory, int], 
                                  failed_commands: int, total_commands: int) -> FollowUpAction:
        """Determine the recommended follow-up action based on error analysis"""
        if failed_commands == 0:
            # All commands succeeded (possibly with warnings)
            return FollowUpAction.CONTINUE
        
        # Check for system errors first (most critical)
        if ErrorCategory.SYSTEM in errors_by_category:
            return FollowUpAction.STOP
        
        # Check for validation errors (need clarification)
        if ErrorCategory.VALIDATION in errors_by_category:
            return FollowUpAction.ASK
        
        # Check for business errors (can suggest alternatives)
        if ErrorCategory.BUSINESS in errors_by_category:
            return FollowUpAction.ASK
        
        # If we have successful commands, continue with those
        successful_commands = total_commands - failed_commands
        if successful_commands > 0:
            return FollowUpAction.CONTINUE
        
        # All commands failed with unknown error types
        return FollowUpAction.STOP
    
    @staticmethod
    def _generate_summary_message(total_commands: int, successful_commands: int, 
                                failed_commands: int, warnings_count: int,
                                errors_by_category: Dict[ErrorCategory, int],
                                command_names: Optional[List[str]] = None) -> str:
        """Generate a human-readable summary message"""
        if total_commands == 1:
            # Single command
            if successful_commands == 1:
                return "Command executed successfully"
            else:
                return "Command failed"
        
        # Multiple commands
        parts = []
        
        if successful_commands > 0:
            if successful_commands == 1:
                parts.append("1 command succeeded")
            else:
                parts.append(f"{successful_commands} commands succeeded")
        
        if failed_commands > 0:
            if failed_commands == 1:
                parts.append("1 command failed")
            else:
                parts.append(f"{failed_commands} commands failed")
        
        if warnings_count > 0:
            parts.append(f"{warnings_count} commands had warnings")
        
        if not parts:
            return "No commands processed"
        
        return "; ".join(parts) + "."
    
    @property
    def has_successes(self) -> bool:
        """Check if any commands succeeded"""
        return self.successful_commands > 0
    
    @property
    def has_failures(self) -> bool:
        """Check if any commands failed"""
        return self.failed_commands > 0
    
    @property
    def all_succeeded(self) -> bool:
        """Check if all commands succeeded"""
        return self.failed_commands == 0
    
    @property
    def all_failed(self) -> bool:
        """Check if all commands failed"""
        return self.successful_commands == 0
    
    def get_successful_results(self) -> List[OrderResult]:
        """Get only the successful results"""
        return [r for r in self.results if r.is_success]
    
    def get_failed_results(self) -> List[OrderResult]:
        """Get only the failed results"""
        return [r for r in self.results if r.is_error]
    
    def get_results_by_category(self, category: ErrorCategory) -> List[OrderResult]:
        """Get results that have a specific error category"""
        return [r for r in self.results if r.error_category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_commands": self.total_commands,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands,
            "warnings_count": self.warnings_count,
            "errors_by_category": {cat.value: count for cat, count in self.errors_by_category.items()},
            "errors_by_code": {code.value: count for code, count in self.errors_by_code.items()},
            "follow_up_action": self.follow_up_action.value,
            "summary_message": self.summary_message,
            "results": [result.to_dict() for result in self.results],
            "has_successes": self.has_successes,
            "has_failures": self.has_failures,
            "all_succeeded": self.all_succeeded,
            "all_failed": self.all_failed
        }
    
    def __str__(self) -> str:
        """String representation for logging"""
        return f"CommandBatchResult: {self.summary_message} | Action: {self.follow_up_action.value}"
