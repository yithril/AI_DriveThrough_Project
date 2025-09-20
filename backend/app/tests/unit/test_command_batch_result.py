"""
Unit tests for CommandBatchResult and enhanced OrderResult functionality
"""

import pytest
from app.dto.order_result import (
    OrderResult, 
    OrderResultStatus, 
    ErrorCategory, 
    ErrorCode,
    CommandBatchResult, 
    FollowUpAction
)


class TestOrderResultEnhancements:
    """Test the enhanced OrderResult with error categorization and recovery suggestions"""
    
    def test_validation_error_with_suggestion(self):
        """Test creating a validation error"""
        result = OrderResult.validation_error(
            "Invalid quantity",
            errors=["Quantity must be positive"],
            error_code=ErrorCode.INVALID_QUANTITY
        )
        
        assert result.status == OrderResultStatus.ERROR
        assert result.error_category == ErrorCategory.VALIDATION
        assert result.error_code == ErrorCode.INVALID_QUANTITY
        assert "Invalid quantity" in result.message
        assert "Quantity must be positive" in result.errors
    
    def test_business_error_with_suggestion(self):
        """Test creating a business error"""
        result = OrderResult.business_error(
            "Item unavailable",
            errors=["Foie gras burger not available"],
            error_code=ErrorCode.ITEM_UNAVAILABLE
        )
        
        assert result.status == OrderResultStatus.ERROR
        assert result.error_category == ErrorCategory.BUSINESS
        assert result.error_code == ErrorCode.ITEM_UNAVAILABLE
    
    def test_system_error_with_suggestion(self):
        """Test creating a system error"""
        result = OrderResult.system_error(
            "Database connection failed",
            errors=["Connection timeout"],
            error_code=ErrorCode.DATABASE_ERROR
        )
        
        assert result.status == OrderResultStatus.ERROR
        assert result.error_category == ErrorCategory.SYSTEM
        assert result.error_code == ErrorCode.DATABASE_ERROR
    
    def test_to_dict_includes_new_fields(self):
        """Test that to_dict includes error_category and error_code"""
        result = OrderResult.business_error("Test error", error_code=ErrorCode.ITEM_UNAVAILABLE)
        
        data = result.to_dict()
        assert data["error_category"] == "business"
        assert data["error_code"] == "item_unavailable"
    
    def test_str_includes_new_fields(self):
        """Test that string representation includes new fields"""
        result = OrderResult.validation_error("Test error", error_code=ErrorCode.INVALID_QUANTITY)
        
        str_repr = str(result)
        assert "Category: validation" in str_repr
        assert "Code: invalid_quantity" in str_repr


class TestCommandBatchResult:
    """Test the CommandBatchResult aggregation functionality"""
    
    def test_all_successful_commands(self):
        """Test batch result when all commands succeed"""
        results = [
            OrderResult.success("Added burger"),
            OrderResult.success("Added fries"),
            OrderResult.success("Added coke")
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add", "add", "add"])
        
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 3
        assert batch_result.failed_commands == 0
        assert batch_result.follow_up_action == FollowUpAction.CONTINUE
        assert "3 commands succeeded" in batch_result.summary_message
    
    def test_mixed_success_and_failure(self):
        """Test batch result with mixed success and failure"""
        results = [
            OrderResult.success("Added burger"),
            OrderResult.business_error("Item unavailable", error_code=ErrorCode.ITEM_UNAVAILABLE),
            OrderResult.success("Added coke")
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add", "add", "add"])
        
        assert batch_result.total_commands == 3
        assert batch_result.successful_commands == 2
        assert ErrorCode.ITEM_UNAVAILABLE in batch_result.errors_by_code
        assert batch_result.errors_by_code[ErrorCode.ITEM_UNAVAILABLE] == 1
        assert batch_result.failed_commands == 1
        assert batch_result.follow_up_action == FollowUpAction.ASK
        assert "2 commands succeeded" in batch_result.summary_message
        assert "1 command failed" in batch_result.summary_message
    
    def test_system_error_stops_execution(self):
        """Test that system errors result in STOP action"""
        results = [
            OrderResult.success("Added burger"),
            OrderResult.system_error("Database error")
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add", "add"])
        
        assert batch_result.follow_up_action == FollowUpAction.STOP
        assert batch_result.errors_by_category[ErrorCategory.SYSTEM] == 1
    
    def test_validation_error_asks_for_clarification(self):
        """Test that validation errors result in ASK action"""
        results = [
            OrderResult.validation_error("Unclear input")
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add"])
        
        assert batch_result.follow_up_action == FollowUpAction.ASK
        assert batch_result.errors_by_category[ErrorCategory.VALIDATION] == 1
    
    def test_get_successful_and_failed_results(self):
        """Test filtering methods for successful and failed results"""
        results = [
            OrderResult.success("Success 1"),
            OrderResult.business_error("Error 1"),
            OrderResult.success("Success 2"),
            OrderResult.validation_error("Error 2")
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add", "add", "add", "add"])
        
        successful = batch_result.get_successful_results()
        failed = batch_result.get_failed_results()
        
        assert len(successful) == 2
        assert len(failed) == 2
        assert all(r.is_success for r in successful)
        assert all(r.is_error for r in failed)
    
    def test_get_results_by_category(self):
        """Test filtering results by error category"""
        results = [
            OrderResult.business_error("Business error 1"),
            OrderResult.validation_error("Validation error 1"),
            OrderResult.business_error("Business error 2")
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add", "add", "add"])
        
        business_errors = batch_result.get_results_by_category(ErrorCategory.BUSINESS)
        validation_errors = batch_result.get_results_by_category(ErrorCategory.VALIDATION)
        
        assert len(business_errors) == 2
        assert len(validation_errors) == 1
        assert all(r.error_category == ErrorCategory.BUSINESS for r in business_errors)
        assert all(r.error_category == ErrorCategory.VALIDATION for r in validation_errors)
    
    def test_to_dict_comprehensive(self):
        """Test that to_dict includes all relevant information"""
        results = [
            OrderResult.success("Success"),
            OrderResult.business_error("Error", error_code=ErrorCode.ITEM_UNAVAILABLE)
        ]
        
        batch_result = CommandBatchResult.from_results(results, ["add", "add"])
        data = batch_result.to_dict()
        
        assert "total_commands" in data
        assert "successful_commands" in data
        assert "failed_commands" in data
        assert "errors_by_category" in data
        assert "errors_by_code" in data
        assert "follow_up_action" in data
        assert "summary_message" in data
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["errors_by_code"]["item_unavailable"] == 1


class TestErrorCodeFunctionality:
    """Test specific error code functionality"""
    
    def test_error_code_enum_values(self):
        """Test that all error codes have expected values"""
        assert ErrorCode.ITEM_UNAVAILABLE == "item_unavailable"
        assert ErrorCode.ITEM_NOT_FOUND == "item_not_found"
        assert ErrorCode.SIZE_NOT_AVAILABLE == "size_not_available"
        assert ErrorCode.MODIFIER_REMOVE_NOT_PRESENT == "modifier_remove_not_present"
        assert ErrorCode.MODIFIER_ADD_NOT_ALLOWED == "modifier_add_not_allowed"
        assert ErrorCode.MODIFIER_CONFLICT == "modifier_conflict"
        assert ErrorCode.QUANTITY_EXCEEDS_LIMIT == "quantity_exceeds_limit"
        assert ErrorCode.INVENTORY_SHORTAGE == "inventory_shortage"
        assert ErrorCode.INVALID_QUANTITY == "invalid_quantity"
        assert ErrorCode.DATABASE_ERROR == "database_error"
    
    def test_business_error_codes(self):
        """Test business error codes with appropriate categorization"""
        # Item-related errors
        result1 = OrderResult.business_error("Item not available", error_code=ErrorCode.ITEM_UNAVAILABLE)
        assert result1.error_category == ErrorCategory.BUSINESS
        assert result1.error_code == ErrorCode.ITEM_UNAVAILABLE
        
        result2 = OrderResult.business_error("Item not found", error_code=ErrorCode.ITEM_NOT_FOUND)
        assert result2.error_category == ErrorCategory.BUSINESS
        assert result2.error_code == ErrorCode.ITEM_NOT_FOUND
        
        # Modifier errors
        result3 = OrderResult.business_error("Cannot remove rabbit", error_code=ErrorCode.MODIFIER_REMOVE_NOT_PRESENT)
        assert result3.error_category == ErrorCategory.BUSINESS
        assert result3.error_code == ErrorCode.MODIFIER_REMOVE_NOT_PRESENT
        
        result4 = OrderResult.business_error("Cannot add foie gras", error_code=ErrorCode.MODIFIER_ADD_NOT_ALLOWED)
        assert result4.error_category == ErrorCategory.BUSINESS
        assert result4.error_code == ErrorCode.MODIFIER_ADD_NOT_ALLOWED
        
        result5 = OrderResult.business_error("Conflicting modifiers", error_code=ErrorCode.MODIFIER_CONFLICT)
        assert result5.error_category == ErrorCategory.BUSINESS
        assert result5.error_code == ErrorCode.MODIFIER_CONFLICT
        
        # Quantity errors
        result6 = OrderResult.business_error("Too many items", error_code=ErrorCode.QUANTITY_EXCEEDS_LIMIT)
        assert result6.error_category == ErrorCategory.BUSINESS
        assert result6.error_code == ErrorCode.QUANTITY_EXCEEDS_LIMIT
        
        result7 = OrderResult.business_error("Out of stock", error_code=ErrorCode.INVENTORY_SHORTAGE)
        assert result7.error_category == ErrorCategory.BUSINESS
        assert result7.error_code == ErrorCode.INVENTORY_SHORTAGE
    
    def test_validation_error_codes(self):
        """Test validation error codes"""
        result1 = OrderResult.validation_error("Invalid quantity format", error_code=ErrorCode.INVALID_QUANTITY)
        assert result1.error_category == ErrorCategory.VALIDATION
        assert result1.error_code == ErrorCode.INVALID_QUANTITY
        
        result2 = OrderResult.validation_error("Missing required field", error_code=ErrorCode.MISSING_REQUIRED_FIELD)
        assert result2.error_category == ErrorCategory.VALIDATION
        assert result2.error_code == ErrorCode.MISSING_REQUIRED_FIELD
        
        result3 = OrderResult.validation_error("Invalid input format", error_code=ErrorCode.INVALID_INPUT_FORMAT)
        assert result3.error_category == ErrorCategory.VALIDATION
        assert result3.error_code == ErrorCode.INVALID_INPUT_FORMAT
    
    def test_system_error_codes(self):
        """Test system error codes"""
        result1 = OrderResult.system_error("Database connection failed", error_code=ErrorCode.DATABASE_ERROR)
        assert result1.error_category == ErrorCategory.SYSTEM
        assert result1.error_code == ErrorCode.DATABASE_ERROR
        
        result2 = OrderResult.system_error("External service unavailable", error_code=ErrorCode.EXTERNAL_SERVICE_ERROR)
        assert result2.error_category == ErrorCategory.SYSTEM
        assert result2.error_code == ErrorCode.EXTERNAL_SERVICE_ERROR
        
        result3 = OrderResult.system_error("Internal server error", error_code=ErrorCode.INTERNAL_ERROR)
        assert result3.error_category == ErrorCategory.SYSTEM
        assert result3.error_code == ErrorCode.INTERNAL_ERROR
    
    def test_command_batch_result_error_code_aggregation(self):
        """Test that CommandBatchResult properly aggregates error codes"""
        results = [
            OrderResult.success("Added burger"),
            OrderResult.business_error("Item unavailable", error_code=ErrorCode.ITEM_UNAVAILABLE),
            OrderResult.business_error("Item unavailable", error_code=ErrorCode.ITEM_UNAVAILABLE),
            OrderResult.validation_error("Invalid quantity", error_code=ErrorCode.INVALID_QUANTITY),
            OrderResult.business_error("Modifier conflict", error_code=ErrorCode.MODIFIER_CONFLICT)
        ]
        
        batch_result = CommandBatchResult.from_results(results)
        
        # Check error code aggregation
        assert batch_result.errors_by_code[ErrorCode.ITEM_UNAVAILABLE] == 2
        assert batch_result.errors_by_code[ErrorCode.INVALID_QUANTITY] == 1
        assert batch_result.errors_by_code[ErrorCode.MODIFIER_CONFLICT] == 1
        
        # Check that to_dict includes error codes
        data = batch_result.to_dict()
        assert data["errors_by_code"]["item_unavailable"] == 2
        assert data["errors_by_code"]["invalid_quantity"] == 1
        assert data["errors_by_code"]["modifier_conflict"] == 1
    
    def test_error_code_without_category(self):
        """Test that error_code can be set without error_category"""
        result = OrderResult.error("Generic error", error_code=ErrorCode.INTERNAL_ERROR)
        assert result.error_code == ErrorCode.INTERNAL_ERROR
        assert result.error_category is None  # No category set
    
    def test_error_category_without_code(self):
        """Test that error_category can be set without error_code"""
        result = OrderResult.business_error("Business error without specific code")
        assert result.error_category == ErrorCategory.BUSINESS
        assert result.error_code is None  # No specific code set


class TestFollowUpActionLogic:
    """Test the follow-up action decision logic"""
    
    def test_continue_when_all_succeed(self):
        """Test CONTINUE action when all commands succeed"""
        results = [OrderResult.success("Success")]
        batch_result = CommandBatchResult.from_results(results, ["add"])
        assert batch_result.follow_up_action == FollowUpAction.CONTINUE
    
    def test_stop_on_system_error(self):
        """Test STOP action when system error occurs"""
        results = [OrderResult.system_error("System error")]
        batch_result = CommandBatchResult.from_results(results, ["add"])
        assert batch_result.follow_up_action == FollowUpAction.STOP
    
    def test_ask_on_validation_error(self):
        """Test ASK action when validation error occurs"""
        results = [OrderResult.validation_error("Validation error")]
        batch_result = CommandBatchResult.from_results(results, ["add"])
        assert batch_result.follow_up_action == FollowUpAction.ASK
    
    def test_ask_on_business_error(self):
        """Test ASK action when business error occurs"""
        results = [OrderResult.business_error("Business error")]
        batch_result = CommandBatchResult.from_results(results, ["add"])
        assert batch_result.follow_up_action == FollowUpAction.ASK
    
    def test_continue_with_mixed_results(self):
        """Test CONTINUE action when some succeed and some fail (non-system errors)"""
        results = [
            OrderResult.success("Success"),
            OrderResult.business_error("Business error")
        ]
        batch_result = CommandBatchResult.from_results(results, ["add", "add"])
        assert batch_result.follow_up_action == FollowUpAction.ASK  # ASK because of business error
