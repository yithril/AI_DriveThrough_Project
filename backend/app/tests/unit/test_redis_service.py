"""
Unit tests for RedisService
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.redis_service import RedisService


class TestRedisService:
    """Test RedisService functionality"""
    
    @pytest.fixture
    def redis_service(self):
        """Create RedisService instance for testing"""
        return RedisService()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, redis_service):
        """Test successful Redis connection"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_redis.return_value = mock_client
            
            result = await redis_service.connect()
            
            assert result is True
            assert redis_service.connected is True
            assert redis_service.redis_client == mock_client
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, redis_service):
        """Test Redis connection failure"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            result = await redis_service.connect()
            
            assert result is False
            assert redis_service.connected is False
    
    @pytest.mark.asyncio
    async def test_basic_operations(self, redis_service):
        """Test basic Redis operations"""
        # Mock connected Redis client
        mock_client = AsyncMock()
        redis_service.redis_client = mock_client
        redis_service.connected = True
        
        # Test GET
        mock_client.get = AsyncMock(return_value="test_value")
        result = await redis_service.get("test_key")
        assert result == "test_value"
        
        # Test SET
        mock_client.setex = AsyncMock(return_value=True)
        result = await redis_service.set("test_key", "test_value", 3600)
        assert result is True
        
        # Test DELETE
        mock_client.delete = AsyncMock(return_value=1)
        result = await redis_service.delete("test_key")
        assert result is True
        
        # Test EXISTS
        mock_client.exists = AsyncMock(return_value=1)
        result = await redis_service.exists("test_key")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_queue_operations(self, redis_service):
        """Test queue simulation operations"""
        # Mock connected Redis client
        mock_client = AsyncMock()
        redis_service.redis_client = mock_client
        redis_service.connected = True
        
        # Test get_current_order
        mock_client.get = AsyncMock(return_value="order_123")
        result = await redis_service.get_current_order("lane_1")
        assert result == "order_123"
        
        # Test set_current_order
        mock_client.setex = AsyncMock(return_value=True)
        result = await redis_service.set_current_order("lane_1", "order_123", 1800)
        assert result is True
        
        # Test clear_lane
        mock_client.delete = AsyncMock(return_value=1)
        result = await redis_service.clear_lane("lane_1")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_order_operations(self, redis_service):
        """Test order-specific operations"""
        # Mock connected Redis client
        mock_client = AsyncMock()
        redis_service.redis_client = mock_client
        redis_service.connected = True
        
        # Test get_order
        order_data = {"id": "order_123", "status": "pending"}
        mock_client.get = AsyncMock(return_value='{"id": "order_123", "status": "pending"}')
        result = await redis_service.get_order("order_123")
        assert result == order_data
        
        # Test set_order
        mock_client.setex = AsyncMock(return_value=True)
        result = await redis_service.set_order("order_123", order_data, 1800)
        assert result is True
        
        # Test delete_order
        mock_client.delete = AsyncMock(return_value=1)
        result = await redis_service.delete_order("order_123")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_disconnect(self, redis_service):
        """Test Redis disconnection"""
        mock_client = AsyncMock()
        redis_service.redis_client = mock_client
        redis_service.connected = True
        
        await redis_service.disconnect()
        
        mock_client.close.assert_called_once()
        assert redis_service.connected is False
    
    @pytest.mark.asyncio
    async def test_operations_when_disconnected(self, redis_service):
        """Test that operations return None/False when disconnected"""
        redis_service.connected = False
        
        # All operations should return None/False when disconnected
        assert await redis_service.get("test_key") is None
        assert await redis_service.set("test_key", "value") is False
        assert await redis_service.delete("test_key") is False
        assert await redis_service.exists("test_key") is False
        assert await redis_service.get_current_order("lane_1") is None
        assert await redis_service.set_current_order("lane_1", "order_123") is False
        assert await redis_service.clear_lane("lane_1") is False
