"""
Response builder utilities for command results

This module contains functions for building structured responses
from command execution results.
"""

from typing import List, Dict, Any, Optional
from app.dto.order_result import OrderResult, ResponsePayload


def build_summary_events(results: List[OrderResult]) -> List[Dict[str, Any]]:
    """
    Build structured summary events from command results.
    
    Args:
        results: List of OrderResult objects from command execution
        
    Returns:
        List of structured events describing what happened
    """
    events = []
    
    for result in results:
        if result.is_success:
            # Extract success event
            event = _extract_success_event(result)
            if event:
                events.append(event)
        elif result.is_error:
            # Extract failure event
            event = _extract_failure_event(result)
            if event:
                events.append(event)
    
    return events


# Removed generate_follow_up_options - command executor should not suggest actions


def build_response_payload(batch_outcome: str, summary_events: List[Dict[str, Any]], 
                          first_error_code: Optional[str] = None, 
                          intent_type: str = "UNKNOWN") -> ResponsePayload:
    """
    Build response payload that describes what happened.
    Does NOT suggest what to do next - that's for downstream components.
    
    Args:
        batch_outcome: Result of batch analysis
        summary_events: Structured events from results
        first_error_code: First error code if any failures
        intent_type: Original intent type for context
        
    Returns:
        ResponsePayload with template key and args (no suggestions)
    """
    # Determine template key based on intent and outcome
    enum_key = _determine_template_key(intent_type, batch_outcome)
    
    # Extract args from summary events
    args = _extract_args_from_events(summary_events)
    
    # Add error context if available
    if first_error_code:
        args["first_error_code"] = first_error_code
    
    # Build telemetry data
    telemetry = {
        "batch_outcome": batch_outcome,
        "events_count": len(summary_events),
        "intent_type": intent_type
    }
    
    return ResponsePayload(
        enum_key=enum_key,
        args=args,
        telemetry=telemetry
    )


def _extract_success_event(result: OrderResult) -> Optional[Dict[str, Any]]:
    """Extract success event from result."""
    if not result.data:
        return None
    
    # Extract item information from result data
    item_name = result.data.get("item_name", "item")
    qty = result.data.get("qty", 1)
    
    # Determine event type based on command context
    # This is a simplified version - in practice, you'd determine this from the command type
    if "add" in result.message.lower() or "added" in result.message.lower():
        return {
            "type": "ADDED_ITEM",
            "item_name": item_name,
            "qty": qty
        }
    elif "remove" in result.message.lower() or "removed" in result.message.lower():
        return {
            "type": "REMOVED_ITEM", 
            "item_name": item_name,
            "qty": qty
        }
    elif "update" in result.message.lower() or "updated" in result.message.lower():
        return {
            "type": "UPDATED_ITEM",
            "item_name": item_name,
            "qty": qty
        }
    
    return None


def _extract_failure_event(result: OrderResult) -> Optional[Dict[str, Any]]:
    """Extract failure event from result."""
    if not result.error_code:
        return None
    
    # Extract item information from result data
    item_name = result.data.get("item_name", "item") if result.data else "item"
    
    # Map error codes to event types
    error_mapping = {
        "item_unavailable": "FAILED_ITEM_UNAVAILABLE",
        "item_not_found": "FAILED_ITEM_NOT_FOUND", 
        "size_not_available": "FAILED_SIZE_NOT_AVAILABLE",
        "size_required": "FAILED_SIZE_REQUIRED",
        "modifier_conflict": "FAILED_MODIFIER_CONFLICT",
        "quantity_exceeds_limit": "FAILED_QUANTITY_EXCEEDS_LIMIT"
    }
    
    event_type = error_mapping.get(result.error_code.value, "FAILED_UNKNOWN")
    
    return {
        "type": event_type,
        "item_name": item_name,
        "error_code": result.error_code.value
    }


def _determine_template_key(intent_type: str, batch_outcome: str) -> str:
    """Determine template key based on intent and outcome."""
    return f"{intent_type}_{batch_outcome}"


def _extract_args_from_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract template arguments from summary events."""
    args = {}
    
    # Extract successful items
    successful_items = [event["item_name"] for event in events if event["type"].startswith("ADDED_")]
    if successful_items:
        args["successful_items"] = successful_items
    
    # Extract failed items
    failed_items = [event["item_name"] for event in events if event["type"].startswith("FAILED_")]
    if failed_items:
        args["failed_items"] = failed_items
    
    return args
