"""
Command Executor Node

Executes commands and validates results.
Runs all commands in batch and aggregates results.
"""

import logging
from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.commands.command_invoker import CommandInvoker
from app.commands.command_factory import CommandFactory
from app.commands.command_context import CommandContext

logger = logging.getLogger(__name__)


async def command_executor_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    Execute generated commands and collect results.
    
    Args:
        state: Current conversation workflow state
        context: LangGraph context with injected dependencies
        
    Returns:
        Updated state with command execution results
    """
    print(f"\n🔍 DEBUG - COMMAND EXECUTOR NODE:")
    print(f"   State has commands: {state.commands is not None}")
    print(f"   Commands count: {len(state.commands) if state.commands else 0}")
    if state.commands:
        print(f"   Commands: {state.commands}")
    
    # Get service factory from config
    service_factory = config.get("configurable", {}).get("service_factory") if config else None
    if not service_factory:
        logger.error("Service factory not available")
        state.response_text = "I'm sorry, I'm having trouble processing your request. Please try again."
        return state
    
    # Import services (no longer need to import Container)
    from app.commands.command_invoker import CommandInvoker
    from app.commands.command_factory import CommandFactory
    
    try:
        # Create command context with basic info
        # In this system, the session ID is the order ID
        command_context = CommandContext(
            session_id=state.session_id,
            restaurant_id=state.restaurant_id,
            order_id=state.session_id  # Session ID is the order ID
        )
        
        # Get shared database session from context
        shared_db_session = config.get("configurable", {}).get("shared_db_session")
        if not shared_db_session:
            logger.error("Shared database session not available")
            state.response_text = "I'm sorry, I'm having trouble processing your request. Please try again."
            return state
        
        # Create services with shared database session
        order_service = service_factory.create_order_service(shared_db_session)
        order_session_service = service_factory.create_order_session_service()
        customization_validator = service_factory.create_customization_validator(shared_db_session)
        
        # Populate command context
        command_context.set_order_service(order_service)
        command_context.set_order_session_service(order_session_service)
        command_context.set_customization_validator(customization_validator)
        command_context.set_db_session(shared_db_session)
        
        # Create UnitOfWork for this command batch execution
        # All commands in the batch will share the same transaction
        from app.core.unit_of_work import UnitOfWork
        
        # Create UnitOfWork with shared database session
        uow = UnitOfWork(shared_db_session)
        
        # Step 1: Validate command dictionaries
        valid_commands = []
        validation_errors = []
        
        print(f"   Validating {len(state.commands) if state.commands else 0} commands")
        
        if not state.commands:
            # No commands to execute - create a failed batch result
            from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
            from app.agents.utils.response_builder import build_summary_events, build_response_payload
            from app.dto.order_result import OrderResult, OrderResultStatus
            from app.agents.utils.command_batch_result import CommandBatchResult
            
            # Create a failed result indicating parsing failed
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
            
            state.command_batch_result = CommandBatchResult(
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
            state.response_text = "I'm sorry, I didn't understand. Could you please try again?"
            return state
        
        # Import validator
        from app.commands.command_data_validator import CommandDataValidator
        
        for cmd_dict in state.commands:
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
                    state.command_batch_result = batch_result
                    print(f"   Command batch result set in state")
            except Exception as uow_error:
                print(f"   UoW transaction failed: {uow_error}")
                logger.error(f"UoW transaction failed: {uow_error}")
                raise
            
            # Generate response text based on results
            if batch_result.has_successes and not batch_result.has_failures:
                state.response_text = batch_result.summary_message
            elif batch_result.has_successes and batch_result.has_failures:
                state.response_text = f"{batch_result.summary_message}. Some items couldn't be added."
            else:
                state.response_text = "I'm sorry, I couldn't process your order. Please try again."
        else:
            # No valid commands to execute
            state.command_batch_result = None
            # Note: order_state_changed is now set by final_response_aggregator_node
            state.response_text = "I'm sorry, I couldn't understand what you wanted to order."
        
        # Step 3: Store validation errors
        if validation_errors:
            for error in validation_errors:
                state.add_error(error)
                
    except Exception as e:
        state.add_error(f"Command execution failed: {str(e)}")
        state.command_batch_result = None
        # Note: order_state_changed is now set by final_response_aggregator_node
        state.response_text = "I'm sorry, there was an error processing your order."
    
    
    return state


def should_continue_after_command_executor(state: ConversationWorkflowState) -> str:
    """
    Determine which node to go to next after command execution.
    
    Args:
        state: Current conversation workflow state
        
    Returns:
        Next node name: "follow_up_agent" or "voice_generator"
    """
    # Route based on command execution results
    if state.command_batch_result:
        # Route to final response aggregator for all cases
        return "final_response_aggregator"
    elif state.has_errors():
        return "final_response_aggregator"  # Validation errors, may need clarification
    else:
        return "final_response_aggregator"  # Default to final response aggregator
