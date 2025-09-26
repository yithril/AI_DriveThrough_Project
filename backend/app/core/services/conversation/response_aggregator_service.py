"""
Response Aggregator Service

Processes command batch results into comprehensive, user-friendly responses.
Handles success acknowledgments, unavailable items, and clarification questions.

Converted from final_response_aggregator_node.py to be a reusable service.
"""

import logging
from typing import Dict, Any, List, Optional
from app.agents.command_agents.clarification_agent import clarification_agent_service
from app.constants.audio_phrases import AudioPhraseType
from app.dto.order_result import ErrorCode

logger = logging.getLogger(__name__)


class ResponseAggregatorService:
    """
    Service for aggregating command batch results into comprehensive responses.
    
    Processes command batch results into comprehensive, user-friendly responses.
    Handles success acknowledgments, unavailable items, and clarification questions.
    """
    
    def __init__(self):
        """
        Initialize the response aggregator service.
        """
        self.logger = logging.getLogger(__name__)
    
    async def aggregate_response(
        self,
        command_batch_result: Any,
        session_id: str,
        restaurant_id: str,
        conversation_history: List[Dict[str, Any]],
        order_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate command batch results into a comprehensive final response.
        
        Args:
            command_batch_result: Command execution results
            session_id: Session identifier
            restaurant_id: Restaurant identifier
            conversation_history: Previous conversation turns
            order_state: Current order state
            
        Returns:
            Dictionary with final response text and phrase type
        """
        try:
            print(f"\n🔍 DEBUG - RESPONSE AGGREGATOR SERVICE:")
            print(f"   Command batch result: {command_batch_result is not None}")
            
            if not command_batch_result:
                print(f"   No batch result - using fallback response")
                # No batch result - fallback response
                return {
                    "success": False,
                    "response_text": "I'm sorry, I didn't understand. Could you please try again?",
                    "response_phrase_type": AudioPhraseType.DIDNT_UNDERSTAND
                }
            
            print(f"   Batch result: {command_batch_result}")
            print(f"   Successful commands: {command_batch_result.successful_commands}")
            print(f"   Failed commands: {command_batch_result.failed_commands}")
            print(f"   Results: {len(command_batch_result.results) if command_batch_result.results else 0}")
            
            # Debug: Print details of each result
            if command_batch_result.results:
                for i, result in enumerate(command_batch_result.results):
                    print(f"   Result {i+1}: success={result.is_success}, message='{result.message}', error_code={result.error_code}")
            
            # Check if clarification is needed
            needs_clarification = self._needs_clarification(command_batch_result)
            clarification_response = None
            
            if needs_clarification:
                # Call clarification service
                clarification_response = await clarification_agent_service(
                    batch_result=command_batch_result,
                    state={
                        "session_id": session_id,
                        "restaurant_id": restaurant_id,
                        "conversation_history": conversation_history,
                        "order_state": order_state
                    },
                    config={"configurable": {}}
                )
            
            # Build final aggregated response
            final_response = self._build_final_response(command_batch_result, clarification_response)
            
            # Check if user wants to finish order
            if self._wants_to_finish_order(command_batch_result):
                final_response += " Would you like anything else?"
            
            # Determine phrase type
            phrase_type = self._determine_phrase_type(command_batch_result)
            print(f"   🔍 DEBUG - Phrase type determined: {phrase_type}")
            
            self.logger.info(f"Final response aggregated: {final_response}")
            
            return {
                "success": True,
                "response_text": final_response,
                "response_phrase_type": phrase_type
            }
            
        except Exception as e:
            self.logger.error(f"Response aggregator failed: {e}")
            # Fallback response
            return {
                "success": False,
                "response_text": "I'm sorry, I had trouble processing your request. Please try again.",
                "response_phrase_type": AudioPhraseType.DIDNT_UNDERSTAND
            }
    
    def _needs_clarification(self, batch_result) -> bool:
        """
        Check if the batch result contains commands that need clarification.
        
        Args:
            batch_result: Command execution results
            
        Returns:
            True if clarification is needed
        """
        # Check for clarification commands in successful results
        for result in batch_result.results:
            if (result.is_success and result.data and 
                result.data.get("response_type") == "clarification_needed"):
                return True
        
        # Check for ambiguous items that need user choice
        for result in batch_result.results:
            if (result.is_success and result.data and 
                result.data.get("clarification_type") == "ambiguous_item"):
                return True
        
        return False
    
    def _build_final_response(self, batch_result, clarification_response) -> str:
        """
        Build the final aggregated response from batch results and clarification.
        
        Args:
            batch_result: Command execution results
            clarification_response: Response from clarification service (if any)
            
        Returns:
            Final aggregated response text
        """
        response_parts = []
        
        # 1. Success acknowledgment (if anything succeeded)
        if batch_result.successful_commands > 0:
            response_parts.append("Your order has been updated.")
        
        # 2. Unavailable items and quantity limits (straightforward, no LLM needed)
        unavailable_items = []
        quantity_limit_items = []
        for result in batch_result.results:
            if result.data and result.data.get("response_type") == "item_unavailable":
                requested_item = result.data.get("requested_item", "that item")
                unavailable_items.append(requested_item)
            elif result.error_code == ErrorCode.ITEM_UNAVAILABLE or result.error_code == ErrorCode.ITEM_NOT_FOUND:
                # Use the error message from the validation result
                if result.message:
                    unavailable_items.append(result.message)
                else:
                    unavailable_items.append("that item")
            elif result.error_code == ErrorCode.QUANTITY_EXCEEDS_LIMIT:
                # Use the error message from the validation result
                if result.message:
                    quantity_limit_items.append(result.message)
                else:
                    quantity_limit_items.append("That quantity is too high")
        
        if unavailable_items:
            if len(unavailable_items) == 1:
                response_parts.append(f"Sorry, we don't have {unavailable_items[0]}.")
            else:
                items_list = ", ".join(unavailable_items[:-1]) + f" and {unavailable_items[-1]}"
                response_parts.append(f"Sorry, we don't have {items_list}.")
        
        if quantity_limit_items:
            response_parts.extend(quantity_limit_items)
        
        # 3. Clarification questions (from clarification service, if any)
        if clarification_response:
            response_parts.append(clarification_response.response_text)
        
        # Combine all parts
        final_response = " ".join(response_parts)
        
        # Ensure we have a response
        if not final_response.strip():
            final_response = "I'm sorry, I didn't understand. Could you please try again?"
        
        return final_response
    
    def _wants_to_finish_order(self, batch_result) -> bool:
        """
        Check if the user wants to finish their order based on batch results.
        
        Args:
            batch_result: Command execution results
            
        Returns:
            True if user seems to want to finish order
        """
        # Check for confirm order commands
        for result in batch_result.results:
            if (result.is_success and result.data and 
                result.data.get("response_type") == "order_confirmed"):
                return True
        
        # Check if all items were successfully added (no clarifications needed)
        if (batch_result.successful_commands > 0 and 
            batch_result.failed_commands == 0 and
            not self._needs_clarification(batch_result)):
            return True
        
        return False
    
    def _determine_phrase_type(self, batch_result) -> AudioPhraseType:
        """
        Determine the appropriate phrase type based on batch results.
        
        Args:
            batch_result: Command execution results
            
        Returns:
            Appropriate AudioPhraseType for the response
        """
        # Check for specific command types in results (both success and failure)
        for result in batch_result.results:
            print(f"   🔍 DEBUG - Checking result: error_code={result.error_code}")
            # Check error codes first (for failed commands)
            if result.error_code == ErrorCode.QUANTITY_EXCEEDS_LIMIT:
                print(f"   🔍 DEBUG - Found QUANTITY_EXCEEDS_LIMIT, returning QUANTITY_TOO_HIGH")
                return AudioPhraseType.QUANTITY_TOO_HIGH  # Use specific phrase for quantity limits
            elif result.error_code == ErrorCode.ITEM_UNAVAILABLE:
                print(f"   🔍 DEBUG - Found ITEM_UNAVAILABLE, returning ITEM_UNAVAILABLE")
                return AudioPhraseType.ITEM_UNAVAILABLE
            elif result.error_code == ErrorCode.ITEM_NOT_FOUND:
                print(f"   🔍 DEBUG - Found ITEM_NOT_FOUND, returning ITEM_UNAVAILABLE")
                return AudioPhraseType.ITEM_UNAVAILABLE
            
            # Check response types (for successful commands with data)
            if result.data:
                response_type = result.data.get("response_type")
                if response_type == "item_unavailable":
                    return AudioPhraseType.ITEM_UNAVAILABLE
                elif response_type == "clarification_needed":
                    return AudioPhraseType.CLARIFICATION_QUESTION
                elif response_type == "order_confirmed":
                    return AudioPhraseType.ORDER_CONFIRM
        
        # Check for success/failure patterns (only if no specific error phrase was found above)
        if batch_result.successful_commands > 0 and batch_result.failed_commands == 0:
            return AudioPhraseType.ITEM_ADDED_SUCCESS
        elif batch_result.successful_commands > 0 and batch_result.failed_commands > 0:
            return AudioPhraseType.CUSTOM_RESPONSE  # Mixed results need custom response
        elif batch_result.failed_commands > 0:
            return AudioPhraseType.DIDNT_UNDERSTAND
        else:
            return AudioPhraseType.CUSTOM_RESPONSE
