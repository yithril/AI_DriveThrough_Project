"""
Command Executor Node

Executes commands and validates results.
Runs all commands in batch and aggregates results.
"""

from typing import Dict, Any
from app.agents.state import ConversationWorkflowState
from app.commands.command_invoker import CommandInvoker
from app.commands.command_factory import CommandFactory
from app.commands.command_context import CommandContext
# Removed FollowUpAction import - no longer needed
# Removed circular import - Container will be injected via workflow


async def command_executor_node(state: ConversationWorkflowState, config = None) -> ConversationWorkflowState:
    """
    Execute generated commands and collect results.
    
    Args:
        state: Current conversation workflow state
        context: LangGraph context with injected dependencies
        
    Returns:
        Updated state with command execution results
    """
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
        command_context = CommandContext(
            session_id=state.session_id,
            restaurant_id=state.restaurant_id,
            #What is this order id?
            order_id=state.order_state.order_id if hasattr(state.order_state, 'order_id') else None
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
        
        # Create UnitOfWork for this command batch execution
        # All commands in the batch will share the same transaction
        from app.core.unit_of_work import UnitOfWork
        
        # Create UnitOfWork with shared database session
        uow = UnitOfWork(shared_db_session)
        
        # Step 1: Validate command dictionaries
        valid_commands = []
        validation_errors = []
        
        if not state.commands:
            # No commands to execute
            state.command_batch_result = None
            state.response_text = "No commands to execute"
            return state
        
        # Import validator
        from app.commands.command_data_validator import CommandDataValidator
        
        for cmd_dict in state.commands:
            try:
                # Validate command data structure
                is_valid, validator_errors = CommandDataValidator.validate(cmd_dict)
                
                if not is_valid:
                    error_summary = CommandDataValidator.get_validation_summary(validator_errors)
                    validation_errors.append(f"Command validation failed: {error_summary}")
                    continue
                
                # Create command object using factory
                command = CommandFactory.create_command(
                    intent_data=cmd_dict,
                    restaurant_id=command_context.restaurant_id,
                    order_id=command_context.get_order_id()
                )
                if command:
                    valid_commands.append(command)
                else:
                    validation_errors.append(f"Unsupported intent: {cmd_dict.get('intent', 'UNKNOWN')}")
                    
            except Exception as e:
                validation_errors.append(f"Invalid command dictionary: {str(e)}")
                continue
        
        # Step 2: Execute valid commands within a transaction
        if valid_commands:
            command_invoker = CommandInvoker()
            
            # Execute commands within Unit of Work transaction
            async with uow:
                batch_result = await command_invoker.execute_multiple_commands(valid_commands, command_context)
                
                # CommandInvoker already creates the batch result with router-friendly fields
                # No additional enrichment needed
                
                state.command_batch_result = batch_result
                # Note: order_state_changed is now set by response_router_node
            
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
            # Note: order_state_changed is now set by response_router_node
            state.response_text = "I'm sorry, I couldn't understand what you wanted to order."
        
        # Step 3: Store validation errors
        if validation_errors:
            for error in validation_errors:
                state.add_error(error)
                
    except Exception as e:
        state.add_error(f"Command execution failed: {str(e)}")
        state.command_batch_result = None
        # Note: order_state_changed is now set by response_router_node
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
        # Check if we need follow-up based on the batch outcome
        if state.command_batch_result.batch_outcome == "PARTIAL_SUCCESS_ASK":
            return "clarification_agent"  # Need to ask for clarification
        elif state.command_batch_result.batch_outcome == "ALL_SUCCESS":
            return "response_router"  # All successful, route to response router
        elif state.command_batch_result.batch_outcome == "ALL_FAILED":
            return "clarification_agent"  # All failed, need clarification
        elif state.command_batch_result.failed_commands > 0:
            return "clarification_agent"  # Some commands failed, may need clarification
        else:
            return "response_router"  # Default to response router
    elif state.has_errors():
        return "clarification_agent"  # Validation errors, may need clarification
    else:
        return "response_router"  # Default to response router
