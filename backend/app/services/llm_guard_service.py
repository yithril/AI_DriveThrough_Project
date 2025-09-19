"""
LLM Guard service for input validation and safety
"""

from typing import Dict, Any, List
from llm_guard.input_scanners import PromptInjection, Toxicity
from llm_guard.input_scanners.prompt_injection import MatchType as PI_MatchType
from llm_guard.input_scanners.toxicity import MatchType as Toxicity_MatchType

from ..dto.order_result import OrderResult


class LLMGuardService:
    """
    Service for validating user input against prompt injection, toxicity, etc.
    """
    
    def __init__(self):
        """Initialize LLM Guard service with scanners"""
        # Initialize prompt injection scanner
        self.prompt_injection_scanner = PromptInjection(
            threshold=0.5, 
            match_type=PI_MatchType.FULL
        )
        
        # Initialize toxicity scanner
        self.toxicity_scanner = Toxicity(
            threshold=0.5, 
            match_type=Toxicity_MatchType.SENTENCE
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
            validation_errors = []
            risk_scores = {}
            
            # Check for prompt injection
            pi_sanitized, pi_is_valid, pi_risk_score = self.prompt_injection_scanner.scan(text)
            risk_scores["prompt_injection"] = pi_risk_score
            
            if not pi_is_valid:
                validation_errors.append(f"Prompt injection detected (risk: {pi_risk_score:.2f})")
            
            # Check for toxicity
            tox_sanitized, tox_is_valid, tox_risk_score = self.toxicity_scanner.scan(text)
            risk_scores["toxicity"] = tox_risk_score
            
            if not tox_is_valid:
                validation_errors.append(f"Toxic content detected (risk: {tox_risk_score:.2f})")
            
            # If any validation failed, block the input
            if validation_errors:
                return OrderResult.error(
                    "Input blocked by safety filter",
                    errors=validation_errors,
                    data={
                        "text": text,
                        "risk_scores": risk_scores,
                        "validation_passed": False
                    }
                )
            
            # Input passed all safety checks
            return OrderResult.success(
                "Input passed safety validation",
                data={
                    "text": text,
                    "sanitized_text": pi_sanitized,  # Use prompt injection sanitized version
                    "validation_passed": True,
                    "risk_scores": risk_scores,
                    "flags": []
                }
            )
            
        except Exception as e:
            # If LLM Guard fails, err on the side of caution and block
            return OrderResult.error(
                "Safety validation failed - input blocked",
                errors=[f"LLM Guard error: {str(e)}"],
                data={
                    "text": text,
                    "validation_passed": False,
                    "error": "Safety scanner failure"
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
        
        if max_risk >= 0.8:
            return f"High risk detected ({max_risk:.2f})"
        elif max_risk >= 0.5:
            return f"Medium risk detected ({max_risk:.2f})"
        else:
            return f"Low risk detected ({max_risk:.2f})"
