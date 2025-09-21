"""
Unit tests for batch analysis utilities
"""

import pytest
from app.agents.utils.batch_analysis import get_first_error_code, analyze_batch_outcome
from app.dto.order_result import OrderResult, OrderResultStatus, ErrorCategory, ErrorCode


class TestGetFirstErrorCode:
    """Test get_first_error_code function"""
    
    def test_no_results(self):
        """Test with empty results list"""
        result = get_first_error_code([])
        assert result is None
    
    def test_no_errors(self):
        """Test with successful results only"""
        results = [
            OrderResult.success("Item added"),
            OrderResult.success("Item added")
        ]
        result = get_first_error_code(results)
        assert result is None
    
    def test_business_error_first(self):
        """Test that business errors are prioritized"""
        results = [
            OrderResult.success("Item added"),
            OrderResult.error("Item unavailable", error_category=ErrorCategory.BUSINESS, error_code=ErrorCode.ITEM_UNAVAILABLE),
            OrderResult.error("System error", error_category=ErrorCategory.SYSTEM, error_code=ErrorCode.DATABASE_ERROR)
        ]
        result = get_first_error_code(results)
        assert result == "item_unavailable"
    
    def test_system_error_fallback(self):
        """Test that system errors are used if no business/validation errors"""
        results = [
            OrderResult.success("Item added"),
            OrderResult.error("System error", error_category=ErrorCategory.SYSTEM, error_code=ErrorCode.DATABASE_ERROR)
        ]
        result = get_first_error_code(results)
        assert result == "database_error"
    
    def test_validation_error_prioritized(self):
        """Test that validation errors are prioritized over system errors"""
        results = [
            OrderResult.error("System error", error_category=ErrorCategory.SYSTEM, error_code=ErrorCode.DATABASE_ERROR),
            OrderResult.error("Validation error", error_category=ErrorCategory.VALIDATION, error_code=ErrorCode.INVALID_QUANTITY)
        ]
        result = get_first_error_code(results)
        assert result == "invalid_quantity"


class TestAnalyzeBatchOutcome:
    """Test analyze_batch_outcome function"""
    
    def test_all_success(self):
        """Test all commands succeed"""
        results = [
            OrderResult.success("Item added"),
            OrderResult.success("Item added")
        ]
        outcome = analyze_batch_outcome(results)
        assert outcome == "ALL_SUCCESS"
    
    def test_all_fail_business(self):
        """Test all commands fail with business errors"""
        results = [
            OrderResult.error("Item unavailable", error_category=ErrorCategory.BUSINESS, error_code=ErrorCode.ITEM_UNAVAILABLE),
            OrderResult.error("Item unavailable", error_category=ErrorCategory.BUSINESS, error_code=ErrorCode.ITEM_UNAVAILABLE)
        ]
        outcome = analyze_batch_outcome(results)
        assert outcome == "ALL_FAIL"
    
    def test_fatal_system(self):
        """Test system errors result in fatal system"""
        results = [
            OrderResult.success("Item added"),
            OrderResult.error("System error", error_category=ErrorCategory.SYSTEM, error_code=ErrorCode.DATABASE_ERROR)
        ]
        outcome = analyze_batch_outcome(results)
        assert outcome == "FATAL_SYSTEM"
    
    def test_partial_success_continue(self):
        """Test partial success without user choice required"""
        results = [
            OrderResult.success("Item added"),
            OrderResult.error("Item unavailable", error_category=ErrorCategory.BUSINESS, error_code=ErrorCode.ITEM_UNAVAILABLE)
        ]
        outcome = analyze_batch_outcome(results)
        assert outcome == "PARTIAL_SUCCESS_CONTINUE"
