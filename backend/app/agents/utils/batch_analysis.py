"""
Batch analysis utilities for command results

This module contains functions for analyzing command execution results
to determine batch outcomes and error patterns.
"""

from typing import List, Optional
from app.dto.order_result import OrderResult, ErrorCategory


def get_first_error_code(results: List[OrderResult]) -> Optional[str]:
    """
    Get the first error code from a list of command results.
    
    Prioritizes BUSINESS and VALIDATION errors over SYSTEM errors for better UX.
    
    Args:
        results: List of OrderResult objects from command execution
        
    Returns:
        First error code found, or None if no errors
    """
    if not results:
        return None
    
    # First pass: Look for BUSINESS or VALIDATION errors (better UX)
    for result in results:
        if result.is_error and result.error_code:
            if result.error_category in [ErrorCategory.BUSINESS, ErrorCategory.VALIDATION]:
                return result.error_code.value
    
    # Second pass: Look for any error (including SYSTEM)
    for result in results:
        if result.is_error and result.error_code:
            return result.error_code.value
    
    return None


def analyze_batch_outcome(results: List[OrderResult]) -> str:
    """
    Analyze command results to determine batch outcome.
    
    Args:
        results: List of OrderResult objects from command execution
        
    Returns:
        Batch outcome: "ALL_SUCCESS", "PARTIAL_SUCCESS_ASK", "PARTIAL_SUCCESS_CONTINUE", 
                      "ALL_FAIL", or "FATAL_SYSTEM"
    """
    if not results:
        return "ALL_FAIL"
    
    # Analyze result patterns
    has_success = any(result.is_success for result in results)
    has_business_or_validation = any(
        result.is_error and result.error_category in [ErrorCategory.BUSINESS, ErrorCategory.VALIDATION]
        for result in results
    )
    has_system = any(
        result.is_error and result.error_category == ErrorCategory.SYSTEM
        for result in results
    )
    
    # Apply outcome rules (first match wins)
    if has_system:
        return "FATAL_SYSTEM"
    
    if has_business_or_validation and has_success:
        # Check if any error requires user choice
        requires_user_choice = any(
            result.is_error and result.error_category in [ErrorCategory.BUSINESS, ErrorCategory.VALIDATION]
            and _requires_user_choice(result)
            for result in results
        )
        return "PARTIAL_SUCCESS_ASK" if requires_user_choice else "PARTIAL_SUCCESS_CONTINUE"
    
    if has_business_or_validation and not has_success:
        return "ALL_FAIL"
    
    # All succeeded (or no errors)
    return "ALL_SUCCESS"


def _requires_user_choice(result: OrderResult) -> bool:
    """
    Determine if an error result requires user choice.
    
    Args:
        result: OrderResult with error
        
    Returns:
        True if user choice is required, False otherwise
    """
    # Error codes that typically require user choice
    choice_required_codes = [
        "ITEM_UNAVAILABLE",
        "SIZE_NOT_AVAILABLE", 
        "SIZE_REQUIRED",
        "MODIFIER_CONFLICT",
        "OPTION_REQUIRED_MISSING"
    ]
    
    return result.error_code and result.error_code.value in choice_required_codes
