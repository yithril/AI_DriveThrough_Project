"""
Lightweight validation service using dependency-free prompt guard
"""

from typing import Dict, Any
from .validation_interface import ValidationServiceInterface
from .prompt_guard import PromptGuard, simple_toxicity
from ..dto.order_result import OrderResult


class LightweightValidationService(ValidationServiceInterface):
    """
    Lightweight validation service using dependency-free prompt guard
    No heavy ML dependencies - just regex patterns and simple word lists
    """
    
    def __init__(self):
        """Initialize lightweight validation service"""
        # Allow trusted domains for drive-thru context
        self.prompt_guard = PromptGuard(
            allow_domains={
                "openai.com",  # OpenAI API
                "aws.amazon.com",  # AWS services
                "google.com",  # Google services
                "microsoft.com",  # Microsoft services
            },
            threshold=5,  # Block at score 5 or higher
            max_untrusted_links=3
        )
    
    async def validate_input(self, text: str) -> OrderResult:
        """
        Validate input text for safety and appropriateness
        
        Args:
            text: User input text to validate
            
        Returns:
            OrderResult: Success if safe, error if blocked
        """
        try:
            # Check for prompt injection and suspicious patterns
            prompt_verdict = self.prompt_guard.check(text)
            
            # Check for toxicity
            toxicity_verdict = simple_toxicity(text, threshold=4)
            
            # Combine results
            total_score = prompt_verdict["score"] + toxicity_verdict["score"]
            all_signals = prompt_verdict["signals"] + toxicity_verdict["terms"]
            
            # If either check blocks, or total score is too high
            if prompt_verdict["blocked"] or toxicity_verdict["blocked"] or total_score >= 8:
                return OrderResult.error(
                    "Input blocked by safety filter",
                    errors=[
                        f"Safety check failed (score: {total_score})",
                        f"Signals detected: {', '.join(all_signals)}"
                    ],
                    data={
                        "text": text,
                        "prompt_verdict": prompt_verdict,
                        "toxicity_verdict": toxicity_verdict,
                        "total_score": total_score,
                        "validation_passed": False
                    }
                )
            
            # Input passed all safety checks
            sanitized_text = self.prompt_guard.sanitize(text)
            
            return OrderResult.success(
                "Input passed safety validation",
                data={
                    "text": text,
                    "sanitized_text": sanitized_text,
                    "validation_passed": True,
                    "prompt_score": prompt_verdict["score"],
                    "toxicity_score": toxicity_verdict["score"],
                    "total_score": total_score,
                    "signals": all_signals
                }
            )
            
        except Exception as e:
            # If validation fails, err on the side of caution and block
            return OrderResult.error(
                "Safety validation failed - input blocked",
                errors=[f"Validation error: {str(e)}"],
                data={
                    "text": text,
                    "validation_passed": False,
                    "error": "Validation service failure"
                }
            )
    
    async def validate_with_context(self, text: str, context: Dict[str, Any]) -> OrderResult:
        """
        Validate input with additional context
        
        Args:
            text: User input text
            context: Additional context (user history, restaurant info, etc.)
            
        Returns:
            OrderResult: Validation result
        """
        # For now, use the same validation as without context
        # Future enhancement: Could adjust thresholds based on context
        # e.g., more lenient for returning customers, stricter for new users
        
        return await self.validate_input(text)
    
    def get_risk_summary(self, risk_scores: Dict[str, float]) -> str:
        """
        Generate a human-readable risk summary
        
        Args:
            risk_scores: Dictionary of risk scores from scanners
            
        Returns:
            str: Risk summary description
        """
        if not risk_scores:
            return "No risk detected"
        
        max_risk = max(risk_scores.values())
        
        if max_risk >= 8:
            return f"High risk detected ({max_risk:.2f})"
        elif max_risk >= 5:
            return f"Medium risk detected ({max_risk:.2f})"
        else:
            return f"Low risk detected ({max_risk:.2f})"
