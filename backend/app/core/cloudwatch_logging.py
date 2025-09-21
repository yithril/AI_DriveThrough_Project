"""
CloudWatch logging configuration for production deployment
"""

import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from .config import settings


class CloudWatchHandler(logging.Handler):
    """
    Custom logging handler that sends logs to AWS CloudWatch
    """
    
    def __init__(self, log_group: str, log_stream: str, region: str = "us-east-1"):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.region = region
        
        # Initialize CloudWatch Logs client
        try:
            self.cloudwatch = boto3.client('logs', region_name=region)
            self._ensure_log_group_exists()
            self._ensure_log_stream_exists()
        except ClientError as e:
            # Fallback to console logging if CloudWatch fails
            print(f"Warning: Failed to initialize CloudWatch logging: {e}")
            self.cloudwatch = None
    
    def _ensure_log_group_exists(self):
        """Ensure the log group exists"""
        try:
            self.cloudwatch.describe_log_groups(logGroupNamePrefix=self.log_group)
        except ClientError:
            # Create log group if it doesn't exist
            try:
                self.cloudwatch.create_log_group(logGroupName=self.log_group)
                print(f"Created CloudWatch log group: {self.log_group}")
            except ClientError as e:
                print(f"Failed to create log group {self.log_group}: {e}")
    
    def _ensure_log_stream_exists(self):
        """Ensure the log stream exists"""
        try:
            self.cloudwatch.describe_log_streams(
                logGroupName=self.log_group,
                logStreamNamePrefix=self.log_stream
            )
        except ClientError:
            # Create log stream if it doesn't exist
            try:
                self.cloudwatch.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
                print(f"Created CloudWatch log stream: {self.log_stream}")
            except ClientError as e:
                print(f"Failed to create log stream {self.log_stream}: {e}")
    
    def emit(self, record):
        """Send log record to CloudWatch"""
        if not self.cloudwatch:
            return
        
        try:
            # Format the log message
            log_message = self.format(record)
            
            # Send to CloudWatch
            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'timestamp': int(record.created * 1000),  # CloudWatch expects milliseconds
                        'message': log_message
                    }
                ]
            )
        except ClientError as e:
            # Don't raise exceptions in logging handlers
            print(f"Failed to send log to CloudWatch: {e}")


def setup_cloudwatch_logging(
    log_group: str = "ai-drivethru",
    log_stream: Optional[str] = None,
    region: str = "us-east-1"
) -> logging.Logger:
    """
    Set up CloudWatch logging for production
    
    Args:
        log_group: CloudWatch log group name
        log_stream: CloudWatch log stream name (auto-generated if None)
        region: AWS region
        
    Returns:
        logging.Logger: Configured logger
    """
    import socket
    import datetime
    
    # Generate log stream name if not provided
    if not log_stream:
        hostname = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        log_stream = f"{hostname}-{timestamp}"
    
    # Create CloudWatch handler
    cloudwatch_handler = CloudWatchHandler(log_group, log_stream, region)
    cloudwatch_handler.setLevel(logging.INFO)
    cloudwatch_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(cloudwatch_handler)
    
    # Set up component loggers
    setup_component_loggers()
    
    return root_logger


def setup_component_loggers():
    """Set up loggers for different application components with CloudWatch"""
    
    # Audio Pipeline logging (most important for monitoring)
    audio_logger = logging.getLogger("app.services.audio_pipeline_service")
    audio_logger.setLevel(logging.INFO)
    
    # Session management logging
    session_logger = logging.getLogger("app.services.order_session_service")
    session_logger.setLevel(logging.INFO)
    
    # API logging
    api_logger = logging.getLogger("app.api")
    api_logger.setLevel(logging.INFO)
    
    # Workflow logging
    workflow_logger = logging.getLogger("app.agents")
    workflow_logger.setLevel(logging.INFO)
    
    # Error logging
    error_logger = logging.getLogger("errors")
    error_logger.setLevel(logging.ERROR)


def log_performance_metrics(operation: str, duration: float, metadata: dict = None):
    """
    Log performance metrics to CloudWatch for monitoring
    
    Args:
        operation: Operation name (e.g., "audio_processing", "workflow_execution")
        duration: Duration in seconds
        metadata: Additional metadata to include
    """
    logger = logging.getLogger("performance")
    
    # Create structured log message for CloudWatch
    log_data = {
        "operation": operation,
        "duration": duration,
        "timestamp": logging.time.time(),
        "metadata": metadata or {}
    }
    
    logger.info(f"PERFORMANCE_METRIC: {log_data}")


def log_business_metrics(event: str, session_id: str, restaurant_id: int, metadata: dict = None):
    """
    Log business metrics to CloudWatch for analytics
    
    Args:
        event: Business event (e.g., "session_started", "order_completed")
        session_id: Session ID
        restaurant_id: Restaurant ID
        metadata: Additional metadata
    """
    logger = logging.getLogger("business_metrics")
    
    # Create structured log message for CloudWatch
    log_data = {
        "event": event,
        "session_id": session_id,
        "restaurant_id": restaurant_id,
        "timestamp": logging.time.time(),
        "metadata": metadata or {}
    }
    
    logger.info(f"BUSINESS_METRIC: {log_data}")


# Production logging setup
def setup_production_logging():
    """
    Set up production logging with CloudWatch integration
    Call this in your main.py or startup code
    """
    import os
    
    # Check if we're in production (AWS environment)
    if os.getenv("AWS_REGION") or os.getenv("ENVIRONMENT") == "production":
        return setup_cloudwatch_logging(
            log_group=os.getenv("CLOUDWATCH_LOG_GROUP", "ai-drivethru"),
            region=os.getenv("AWS_REGION", "us-east-1")
        )
    else:
        # Use local logging for development
        from .logging import setup_logging
        return setup_logging()
