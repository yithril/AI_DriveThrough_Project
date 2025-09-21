"""
Command invoker for executing AI commands
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..dto.order_result import OrderResult, CommandBatchResult, ErrorCode


class CommandInvoker:
    """
    Invoker class that executes commands and manages command history
    Provides a clean interface for the AI to execute operations
    """
    
    def __init__(self):
        """
        Initialize command invoker
        
        Services are now provided via CommandContext, not constructor parameters.
        """
        self.command_history: List[Dict[str, Any]] = []
    
    async def execute_command(self, command: BaseCommand, context: CommandContext) -> OrderResult:
        """
        Execute a command and track it in history
        
        Args:
            command: Command to execute
            context: Command context with services already populated
            
        Returns:
            OrderResult: Result of command execution
        """
        try:
            # Execute the command with context
            result = await command.execute(context, context.db_session)
            
            # Track command in history
            self.command_history.append({
                "command": command.to_dict(),
                "result": result.to_dict(),
                "timestamp": self._get_timestamp()
            })
            
            # Limit history size (keep last 50 commands)
            if len(self.command_history) > 50:
                self.command_history = self.command_history[-50:]
            
            return result
            
        except Exception as e:
            # Track failed commands too
            error_result = OrderResult.system_error(
                f"Command execution failed: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
            self.command_history.append({
                "command": command.to_dict(),
                "result": error_result.to_dict(),
                "timestamp": self._get_timestamp(),
                "error": str(e)
            })
            
            return error_result
    
    async def execute_multiple_commands(self, commands: List[BaseCommand], context: CommandContext) -> CommandBatchResult:
        """
        Execute multiple commands in sequence
        
        Args:
            commands: List of commands to execute
            
        Returns:
            CommandBatchResult: Aggregated results with follow-up recommendations
        """
        results = []
        command_names = []
        
        for index, command in enumerate(commands):
            try:
                # Execute command with index context for better error reporting
                result = await self.execute_command(command, context)
                results.append(result)
                command_names.append(command.command_name)
            except Exception as e:
                # Wrap each command execution in try/except so one failure doesn't crash the loop
                error_result = OrderResult.system_error(
                    f"Command execution failed: {str(e)}",
                    error_code=ErrorCode.INTERNAL_ERROR
                )
                results.append(error_result)
                command_names.append(command.command_name)
        
        # Create aggregated batch result - command executor will enrich it
        # For now, create with placeholder router fields that will be updated
        from app.agents.utils.batch_analysis import analyze_batch_outcome, get_first_error_code
        from app.agents.utils.response_builder import build_summary_events, build_response_payload
        
        # Analyze the batch results
        batch_outcome = analyze_batch_outcome(results)
        first_error_code = get_first_error_code(results)
        summary_events = build_summary_events(results)
        
        # Determine command family from command names
        command_family = "UNKNOWN"
        if command_names:
            command_family = command_names[0].upper()
        
        # Build response payload
        response_payload = build_response_payload(
            batch_outcome=batch_outcome,
            summary_events=summary_events,
            first_error_code=first_error_code,
            intent_type=command_family
        )
        
        return CommandBatchResult.from_results(
            results=results,
            command_family=command_family,
            batch_outcome=batch_outcome,
            first_error_code=first_error_code,
            response_payload=response_payload,
            command_names=command_names
        )
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get command execution history
        
        Args:
            limit: Maximum number of commands to return
            
        Returns:
            List[Dict]: Command history
        """
        if limit:
            return self.command_history[-limit:]
        return self.command_history.copy()
    
    def clear_history(self) -> None:
        """Clear command history"""
        self.command_history.clear()
    
    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the result of the last executed command
        
        Returns:
            Dict or None: Last command result
        """
        if self.command_history:
            return self.command_history[-1]["result"]
        return None
    
    def get_successful_commands(self) -> List[Dict[str, Any]]:
        """
        Get only successful commands from history
        
        Returns:
            List[Dict]: Successful commands
        """
        return [
            entry for entry in self.command_history
            if entry["result"]["is_success"]
        ]
    
    def get_failed_commands(self) -> List[Dict[str, Any]]:
        """
        Get only failed commands from history
        
        Returns:
            List[Dict]: Failed commands
        """
        return [
            entry for entry in self.command_history
            if entry["result"]["is_error"]
        ]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get command execution statistics
        
        Returns:
            Dict: Statistics about command execution
        """
        if not self.command_history:
            return {
                "total_commands": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "success_rate": 0.0
            }
        
        total = len(self.command_history)
        successful = len(self.get_successful_commands())
        failed = len(self.get_failed_commands())
        success_rate = (successful / total) * 100 if total > 0 else 0.0
        
        return {
            "total_commands": total,
            "successful_commands": successful,
            "failed_commands": failed,
            "success_rate": round(success_rate, 2)
        }
