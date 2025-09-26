"""
Command Executor Service

Executes commands and validates results.
Runs all commands in batch and aggregates results.

Converted from command_executor_node.py to be a reusable service.
"""

import logging
from typing import Dict, Any, List, Optional
from app.commands.command_invoker import CommandInvoker
from app.commands.command_factory import CommandFactory
from app.commands.command_context import CommandContext
from app.commands.command_data_validator import CommandDataValidator
from app.core.unit_of_work import UnitOfWork
from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
from app.agents.utils.response_builder import build_summary_events, build_response_payload
from app.dto.order_result import OrderResult, OrderResultStatus
from app.dto.order_result import CommandBatchResult

logger = logging.getLogger(__name__)


class CommandExecutorService:
    """
    Service for executing commands and validating results.
    
    Runs all commands in batch and aggregates results.
    """
    
    def __init__(self, order_service):
        """
        Initialize the command executor service.
        
        Args:
            order_service: Order service (includes validation, session management, etc.)
        """
        self.order_service = order_service
        self.logger = logging.getLogger(__name__)
    
    async def execute_commands(
        self,
        commands: List[Dict[str, Any]],
        session_id: str,
        restaurant_id: str,
        shared_db_session: Any
    ) -> Dict[str, Any]:
        """
        Execute generated commands and collect results.
        
        Args:
            commands: List of command dictionaries to execute
            session_id: Session identifier
            restaurant_id: Restaurant identifier
            shared_db_session: Shared database session
            
        Returns:
            Dictionary with command execution results
        """
        print(f"\n🔍 DEBUG - COMMAND EXECUTOR SERVICE:")
        print(f"   Commands count: {len(commands) if commands else 0}")
        if commands:
            print(f"   Commands: {commands}")
        
        # Use the injected order service (includes validation)
        order_service = self.order_service
        
        # Create command context with basic info
        # In this system, the session ID is the order ID
        command_context = CommandContext(
            session_id=session_id,
            restaurant_id=restaurant_id,
            order_id=session_id  # Session ID is the order ID
        )
        
        # Populate command context
        command_context.set_order_service(order_service)
        command_context.set_db_session(shared_db_session)
        
        # Create UnitOfWork for this command batch execution
        # All commands in the batch will share the same transaction
        uow = UnitOfWork(shared_db_session)
        
        # Step 1: Validate command dictionaries
        valid_commands = []
        validation_errors = []
        
        print(f"   Validating {len(commands) if commands else 0} commands")
        
        if not commands:
            # No commands to execute - create a failed batch result
            failed_result = OrderResult.error("No commands generated - parsing may have failed")
            results = [failed_result]
            
            batch_outcome = analyze_batch_outcome(results)
            first_error_code = get_first_error_code(results)
            summary_events = build_summary_events(results)
            response_payload = build_response_payload(
                batch_outcome=batch_outcome,
                summary_events=summary_events,
                first_error_code=first_error_code,
                intent_type="UNKNOWN"
            )
            
            command_batch_result = CommandBatchResult(
                results=results,
                total_commands=0,
                successful_commands=0,
                failed_commands=1,
                warnings_count=0,
                errors_by_category={},
                errors_by_code={},
                summary_message="No commands generated",
                command_family="UNKNOWN",
                batch_outcome=batch_outcome,
                first_error_code=first_error_code,
                response_payload=response_payload
            )
            
            return {
                "success": False,
                "command_batch_result": command_batch_result,
                "response_text": "I'm sorry, I didn't understand. Could you please try again?",
                "validation_errors": ["No commands generated"]
            }
        
        try:
            # Validate each command
            for cmd_dict in commands:
                try:
                    print(f"   Validating command: {cmd_dict}")
                    # Validate command data structure
                    is_valid, validator_errors = CommandDataValidator.validate(cmd_dict)
                    
                    if not is_valid:
                        error_summary = CommandDataValidator.get_validation_summary(validator_errors)
                        print(f"   Validation failed: {error_summary}")
                        validation_errors.append(f"Command validation failed: {error_summary}")
                        continue
                    else:
                        print(f"   Validation passed")
                    
                    # Create command object using factory
                    print(f"   Creating command for intent: {cmd_dict.get('intent')}")
                    command = CommandFactory.create_command(
                        intent_data=cmd_dict,
                        restaurant_id=command_context.restaurant_id,
                        order_id=command_context.get_order_id()
                    )
                    print(f"   Command created: {command is not None}")
                    if command:
                        print(f"   Command type: {type(command).__name__}")
                        valid_commands.append(command)
                    else:
                        print(f"   Command creation failed for intent: {cmd_dict.get('intent', 'UNKNOWN')}")
                        validation_errors.append(f"Unsupported intent: {cmd_dict.get('intent', 'UNKNOWN')}")
                        
                except Exception as e:
                    validation_errors.append(f"Invalid command dictionary: {str(e)}")
                    continue
            
            # Step 2: Execute valid commands within a transaction
            if valid_commands:
                print(f"   Executing {len(valid_commands)} valid commands")
                command_invoker = CommandInvoker()
                
                # Execute commands within Unit of Work transaction
                try:
                    async with uow:
                        batch_result = await command_invoker.execute_multiple_commands(valid_commands, command_context)
                        print(f"   Batch result created: {batch_result}")
                        print(f"   Command batch result set")
                except Exception as uow_error:
                    print(f"   UoW transaction failed: {uow_error}")
                    self.logger.error(f"UoW transaction failed: {uow_error}")
                    raise
                
                # Generate response text based on results
                if batch_result.has_successes and not batch_result.has_failures:
                    response_text = batch_result.summary_message
                elif batch_result.has_successes and batch_result.has_failures:
                    response_text = f"{batch_result.summary_message}. Some items couldn't be added."
                else:
                    response_text = "I'm sorry, I couldn't process your order. Please try again."
                
                return {
                    "success": True,
                    "command_batch_result": batch_result,
                    "response_text": response_text,
                    "validation_errors": validation_errors
                }
            else:
                # No valid commands to execute
                return {
                    "success": False,
                    "command_batch_result": None,
                    "response_text": "I'm sorry, I couldn't understand what you wanted to order.",
                    "validation_errors": validation_errors
                }
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "command_batch_result": None,
                "response_text": "I'm sorry, there was an error processing your order.",
                "validation_errors": [f"Command execution failed: {str(e)}"]
            }
    
    def should_continue_after_execution(self, execution_result: Dict[str, Any]) -> str:
        """
        Determine which step to go to next after command execution.
        
        Args:
            execution_result: Command execution result
            
        Returns:
            Next step name: "final_response_aggregator"
        """
        # Always route to final response aggregator for all cases
        return "final_response_aggregator"
