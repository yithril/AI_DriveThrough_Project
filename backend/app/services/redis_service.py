"""
Generic Redis service for basic operations and queue simulation
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
import redis.asyncio as redis
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """
    Generic Redis service for basic operations and queue simulation
    
    Provides Redis CRUD operations and drive-thru lane management
    """
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = None
        self.connected = False
    
    async def is_connected(self) -> bool:
        """
        Check if Redis is connected and try to reconnect if needed
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected or not self.redis_client:
            return await self.connect()
        
        try:
            # Test the connection
            await self.redis_client.ping()
            return True
        except Exception:
            # Connection lost, try to reconnect
            logger.warning("Redis connection lost, attempting to reconnect")
            return await self.connect()

    async def connect(self) -> bool:
        """
        Establish Redis connection with proper timeouts and settings
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                client_name="ai-drivethru-backend"
            )
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("Redis connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            self.redis_client = None
            return False
    
    # Basic Redis operations
    async def get(self, key: str) -> Optional[str]:
        """
        Get value by key
        
        Args:
            key: Redis key
            
        Returns:
            str: Value if exists, None otherwise
        """
        if not self.connected:
            return None
        
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 1800) -> bool:
        """
        Set key-value pair with TTL
        
        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if key existed and was deleted, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False
    
    async def set_ttl(self, key: str, seconds: int) -> bool:
        """
        Set TTL for existing key
        
        Args:
            key: Redis key
            seconds: TTL in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            result = await self.redis_client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error(f"Redis EXPIRE failed for key {key}: {e}")
            return False
    
    # Queue simulation operations
    async def get_current_order(self, lane_id: str) -> Optional[str]:
        """
        Get current active order for a drive-thru lane
        
        Args:
            lane_id: Drive-thru lane identifier
            
        Returns:
            str: Order ID if exists, None otherwise
        """
        key = f"lane:{lane_id}:current_order"
        return await self.get(key)
    
    async def set_current_order(self, lane_id: str, order_id: str, ttl: int = 1800) -> bool:
        """
        Set current active order for a drive-thru lane
        
        Args:
            lane_id: Drive-thru lane identifier
            order_id: Order ID to set as current
            ttl: Time to live in seconds (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"lane:{lane_id}:current_order"
        return await self.set(key, order_id, ttl)
    
    async def clear_lane(self, lane_id: str) -> bool:
        """
        Clear current order from a drive-thru lane
        
        Args:
            lane_id: Drive-thru lane identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"lane:{lane_id}:current_order"
        return await self.delete(key)
    
    # Order-specific operations
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order data from Redis
        
        Args:
            order_id: Order ID
            
        Returns:
            dict: Order data if exists, None otherwise
        """
        key = f"order:{order_id}"
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON for order {order_id}")
                return None
        return None
    
    async def set_order(self, order_id: str, order_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Set order data in Redis
        
        Args:
            order_id: Order ID
            order_data: Order data dictionary
            ttl: Time to live in seconds (default 30 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"order:{order_id}"
        try:
            value = json.dumps(order_data)
            return await self.set(key, value, ttl)
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode order {order_id}: {e}")
            return False
    
    async def delete_order(self, order_id: str) -> bool:
        """
        Delete order from Redis
        
        Args:
            order_id: Order ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"order:{order_id}"
        return await self.delete(key)
    
    # Utility methods
    async def get_all_lanes(self) -> List[str]:
        """
        Get all active lanes (for monitoring/debugging)
        
        Returns:
            list: List of lane IDs with active orders
        """
        if not self.connected:
            return []
        
        try:
            pattern = "lane:*:current_order"
            keys = await self.redis_client.keys(pattern)
            return [key.split(":")[1] for key in keys]
        except Exception as e:
            logger.error(f"Failed to get lanes: {e}")
            return []
    
    async def ensure_connection(self) -> bool:
        """
        Ensure Redis connection is available (lazy reconnect)
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected or not self.redis_client:
            logger.warning("Redis not connected, attempting to reconnect")
            return await self.connect()
        
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}, attempting reconnect")
            self.connected = False
            self.redis_client = None
            return await self.connect()
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            try:
                await self.redis_client.aclose()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.redis_client = None
                self.connected = False
