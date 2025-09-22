"""
Intent-Outcome Mapper

Pure function that maps intent + outcome to next node + template.
This is the core routing logic for the response system.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RoutingDecision:
    """Result of intent-outcome mapping"""
    next_node: str
    template_purpose: str
    template_key: str
    args: Dict[str, Any]


class IntentOutcomeMapper:
    """
    Pure function class for mapping intent + outcome to routing decisions.
    
    Maps intent + outcome to next node + template.
    """
    
    # Routing matrix: intent -> outcome -> routing decision
    ROUTING_MATRIX = {
        "ADD_ITEM": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="canned_response",
                template_purpose="Added that to your order. Would you like anything else?",
                template_key="ITEM_ADDED_SUCCESS",
                args={}
            ),
            "PARTIAL_SUCCESS": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="Ask for clarification or continue",
                template_key="ADDITEM_PARTIAL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="I could not add that. Ask which item",
                template_key="ADDITEM_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "REMOVE_ITEM": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="canned_response",
                template_purpose="Removed that from your order. Would you like anything else?",
                template_key="ITEM_REMOVED_SUCCESS",
                args={}
            ),
            "PARTIAL_SUCCESS": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="Show removable items, ask which to remove",
                template_key="REMOVEITEM_PARTIAL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="I could not find that. Offer removable items",
                template_key="REMOVEITEM_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "MODIFY_ITEM": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="canned_response",
                template_purpose="Updated your item. Would you like anything else?",
                template_key="ITEM_UPDATED_SUCCESS",
                args={}
            ),
            "PARTIAL_SUCCESS": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="Ask for needed choice (sizes, modifiers)",
                template_key="MODIFYITEM_PARTIAL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="Explain constraint, offer valid choices",
                template_key="MODIFYITEM_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "CLEAR_ORDER": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="canned_response",
                template_purpose="Your order has been cleared.",
                template_key="ORDER_CLEARED_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="canned_response",
                template_purpose="There is no active order to clear.",
                template_key="CLEARORDER_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "CONFIRM_ORDER": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="canned_response",  # or dynamic_voice_response based on content
                template_purpose="Your order is confirmed",
                template_key="CONFIRMORDER_ALL_SUCCESS",
                args={}
            ),
            "PARTIAL_SUCCESS": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="I need one more detail before we can confirm",
                template_key="CONFIRMORDER_PARTIAL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="Cannot confirm order",
                template_key="CONFIRMORDER_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "QUESTION": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="dynamic_voice_response",
                template_purpose="Generate answer",
                template_key="QUESTION_ALL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="I didn't understand your question",
                template_key="QUESTION_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "REPEAT": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="dynamic_voice_response",
                template_purpose="Repeat order summary",
                template_key="REPEAT_ALL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="canned_response",
                template_purpose="There's nothing to repeat yet.",
                template_key="NOTHING_TO_REPEAT",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "SMALL_TALK": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="canned_response",
                template_purpose="Generic friendly response",
                template_key="SMALLTALK_ALL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="canned_response",
                template_purpose="Generic friendly response",
                template_key="SMALLTALK_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        },
        "UNKNOWN": {
            "ALL_SUCCESS": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="I didn't understand",
                template_key="UNKNOWN_ALL_SUCCESS",
                args={}
            ),
            "ALL_FAILED": RoutingDecision(
                next_node="follow_up_agent",
                template_purpose="I didn't understand",
                template_key="UNKNOWN_ALL_FAILED",
                args={}
            ),
            "FATAL_SYSTEM": RoutingDecision(
                next_node="canned_response",
                template_purpose="I'm sorry, I'm having some technical difficulties. Please try again.",
                template_key="SYSTEM_ERROR_RETRY",
                args={}
            )
        }
    }
    
    @classmethod
    def map_intent_outcome(cls, intent: str, outcome: str) -> RoutingDecision:
        """
        Map intent + outcome to routing decision.
        
        Args:
            intent: Command family (e.g., "ADD_ITEM", "QUESTION")
            outcome: Batch outcome (e.g., "ALL_SUCCESS", "PARTIAL_SUCCESS")
            
        Returns:
            RoutingDecision with next_node, template_purpose, template_key, args
            
        Raises:
            ValueError: If intent or outcome not found in matrix
        """
        intent = intent.upper()
        outcome = outcome.upper()
        
        if intent not in cls.ROUTING_MATRIX:
            raise ValueError(f"Unknown intent: {intent}")
        
        if outcome not in cls.ROUTING_MATRIX[intent]:
            raise ValueError(f"Unknown outcome '{outcome}' for intent '{intent}'")
        
        return cls.ROUTING_MATRIX[intent][outcome]
    
    @classmethod
    def get_available_intents(cls) -> list:
        """Get list of all available intents"""
        return list(cls.ROUTING_MATRIX.keys())
    
    @classmethod
    def get_available_outcomes(cls, intent: str) -> list:
        """Get list of all available outcomes for an intent"""
        intent = intent.upper()
        if intent not in cls.ROUTING_MATRIX:
            raise ValueError(f"Unknown intent: {intent}")
        return list(cls.ROUTING_MATRIX[intent].keys())
