"""
Command invoker for executing AI commands
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from .command_context import CommandContext
from ..services.order_session_interface import OrderSessionInterface
from ..services.order_service import OrderService
from ..dto.order_result import OrderResult


class CommandInvoker:
    """
    Invoker class that executes commands and manages command history
    Provides a clean interface for the AI to execute operations
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        order_session_service: OrderSessionInterface,
        order_service: OrderService,
        restaurant_id: int
    ):
        """
        Initialize command invoker
        
        Args:
            db: Database session for command execution
            order_session_service: Order session service from DI container
            order_service: Order service from DI container
            restaurant_id: Restaurant ID for this invoker's context
        """
        self.db = db
        self.order_session_service = order_session_service
        self.order_service = order_service
        self.restaurant_id = restaurant_id
        self.command_history: List[Dict[str, Any]] = []
    
    async def execute_command(self, command: BaseCommand) -> OrderResult:
        """
        Execute a command and track it in history
        
        Args:
            command: Command to execute
            
        Returns:
            OrderResult: Result of command execution
        """
        try:
            # Create command context scoped to the command's order/session
            context = CommandContext(
                order_session_service=self.order_session_service,
                order_service=self.order_service,
                restaurant_id=self.restaurant_id,
                order_id=command.order_id,
                session_id=None  # Could be set based on current session if needed
            )
            
            # Execute the command with context
            result = await command.execute(context, self.db)
            
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
            error_result = OrderResult.error(f"Command execution failed: {str(e)}")
            self.command_history.append({
                "command": command.to_dict(),
                "result": error_result.to_dict(),
                "timestamp": self._get_timestamp(),
                "error": str(e)
            })
            
            return error_result
    
    async def execute_multiple_commands(self, commands: List[BaseCommand]) -> List[OrderResult]:
        """
        Execute multiple commands in sequence
        
        Args:
            commands: List of commands to execute
            
        Returns:
            List[OrderResult]: Results of command executions
        """
        results = []
        
        for command in commands:
            result = await self.execute_command(command)
            results.append(result)
            
            # Stop execution if any command fails (optional behavior)
            # You might want to continue or stop based on your needs
            if result.is_error:
                break
        
        return results
    
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
