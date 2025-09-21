"""
Unit tests for response builder utilities
"""

import pytest
from app.agents.utils.response_builder import build_summary_events, build_response_payload
from app.dto.order_result import OrderResult, OrderResultStatus, ErrorCategory, ErrorCode
from app.dto.order_result import ResponsePayload


class TestBuildSummaryEvents:
    """Test build_summary_events function"""
    
    def test_no_results(self):
        """Test with empty results list"""
        events = build_summary_events([])
        assert events == []
    
    def test_success_add_item(self):
        """Test successful add item event extraction"""
        results = [
            OrderResult.success("Added burger to order", data={"item_name": "burger", "qty": 1})
        ]
        events = build_summary_events(results)
        assert len(events) == 1
        assert events[0]["type"] == "ADDED_ITEM"
        assert events[0]["item_name"] == "burger"
        assert events[0]["qty"] == 1
    
    def test_success_remove_item(self):
        """Test successful remove item event extraction"""
        results = [
            OrderResult.success("Removed fries from order", data={"item_name": "fries", "qty": 1})
        ]
        events = build_summary_events(results)
        assert len(events) == 1
        assert events[0]["type"] == "REMOVED_ITEM"
        assert events[0]["item_name"] == "fries"
        assert events[0]["qty"] == 1
    
    def test_failure_item_unavailable(self):
        """Test failure event extraction for unavailable item"""
        result = OrderResult.error("Item unavailable", error_category=ErrorCategory.BUSINESS, 
                                 error_code=ErrorCode.ITEM_UNAVAILABLE)
        result.data = {"item_name": "foie gras"}  # Set data after creation
        results = [result]
        events = build_summary_events(results)
        assert len(events) == 1
        assert events[0]["type"] == "FAILED_ITEM_UNAVAILABLE"
        assert events[0]["item_name"] == "foie gras"
        assert events[0]["error_code"] == "item_unavailable"
    
    def test_failure_size_required(self):
        """Test failure event extraction for size required"""
        result = OrderResult.error("Size required", error_category=ErrorCategory.BUSINESS,
                                 error_code=ErrorCode.OPTION_REQUIRED_MISSING)
        result.data = {"item_name": "burger"}  # Set data after creation
        results = [result]
        events = build_summary_events(results)
        assert len(events) == 1
        assert events[0]["type"] == "FAILED_UNKNOWN"  # OPTION_REQUIRED_MISSING not in mapping
        assert events[0]["item_name"] == "burger"
        assert events[0]["error_code"] == "option_required_missing"
    
    def test_mixed_success_and_failure(self):
        """Test mixed success and failure events"""
        success_result = OrderResult.success("Added burger to order", data={"item_name": "burger", "qty": 1})
        failure_result = OrderResult.error("Item unavailable", error_category=ErrorCategory.BUSINESS,
                                         error_code=ErrorCode.ITEM_UNAVAILABLE)
        failure_result.data = {"item_name": "foie gras"}  # Set data after creation
        
        results = [success_result, failure_result]
        events = build_summary_events(results)
        assert len(events) == 2
        
        # Check success event
        success_event = next(e for e in events if e["type"] == "ADDED_ITEM")
        assert success_event["item_name"] == "burger"
        assert success_event["qty"] == 1
        
        # Check failure event
        failure_event = next(e for e in events if e["type"] == "FAILED_ITEM_UNAVAILABLE")
        assert failure_event["item_name"] == "foie gras"
        assert failure_event["error_code"] == "item_unavailable"
    
    def test_no_data_in_result(self):
        """Test result with no data field"""
        results = [
            OrderResult.success("Item added")  # No data field
        ]
        events = build_summary_events(results)
        assert events == []  # Should return empty list when no data
    
    def test_unknown_error_code(self):
        """Test unknown error code mapping"""
        result = OrderResult.error("Unknown error", error_category=ErrorCategory.BUSINESS,
                                 error_code=ErrorCode.DATABASE_ERROR)
        result.data = {"item_name": "item"}  # Set data after creation
        results = [result]
        events = build_summary_events(results)
        assert len(events) == 1
        assert events[0]["type"] == "FAILED_UNKNOWN"
        assert events[0]["item_name"] == "item"


class TestBuildResponsePayload:
    """Test build_response_payload function"""
    
    def test_add_item_success(self):
        """Test response payload for successful add item"""
        summary_events = [{"type": "ADDED_ITEM", "item_name": "burger", "qty": 1}]
        
        payload = build_response_payload("ALL_SUCCESS", summary_events, intent_type="ADD_ITEM")
        
        assert payload.enum_key == "ADD_ITEM_ALL_SUCCESS"
        assert payload.telemetry["batch_outcome"] == "ALL_SUCCESS"
        assert "successful_items" in payload.args
    
    def test_add_item_partial_success(self):
        """Test response payload for partial success"""
        summary_events = [
            {"type": "ADDED_ITEM", "item_name": "burger", "qty": 1},
            {"type": "FAILED_ITEM_UNAVAILABLE", "item_name": "foie gras"}
        ]
        
        payload = build_response_payload("PARTIAL_SUCCESS_ASK", summary_events, 
                                       first_error_code="item_unavailable", intent_type="ADD_ITEM")
        
        assert payload.enum_key == "ADD_ITEM_PARTIAL_SUCCESS_ASK"
        assert payload.telemetry["batch_outcome"] == "PARTIAL_SUCCESS_ASK"
        assert "successful_items" in payload.args
        assert "failed_items" in payload.args
        assert payload.args["first_error_code"] == "item_unavailable"
    
    def test_fatal_system_error(self):
        """Test response payload for fatal system error"""
        summary_events = []
        
        payload = build_response_payload("FATAL_SYSTEM", summary_events, intent_type="ADD_ITEM")
        
        assert payload.enum_key == "ADD_ITEM_FATAL_SYSTEM"
        assert payload.telemetry["batch_outcome"] == "FATAL_SYSTEM"
