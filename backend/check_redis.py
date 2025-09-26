#!/usr/bin/env python3
"""
Quick script to check Redis for current session
"""
import asyncio
import json
from app.services.redis_service import RedisService

async def check_redis():
    redis = RedisService()
    
    print("🔍 Checking Redis for current session...")
    
    # Check if Redis is connected
    if not redis.connected:
        print("❌ Redis is not connected")
        return
    
    # Get current session
    current_session = await redis.get("current:session")
    print(f"Current session: {current_session}")
    
    if current_session:
        # Get session data
        session_data = await redis.get(f"session:{current_session}")
        if session_data:
            session_json = json.loads(session_data)
            print(f"Session data: {json.dumps(session_json, indent=2)}")
            
            # Check if session has order_id
            order_id = session_json.get('order_id')
            if order_id:
                print(f"Order ID: {order_id}")
                
                # Get order data
                order_data = await redis.get(f"order:{order_id}")
                if order_data:
                    order_json = json.loads(order_data)
                    print(f"Order data: {json.dumps(order_json, indent=2)}")
                else:
                    print("❌ No order data found")
            else:
                print("❌ No order_id in session")
        else:
            print("❌ No session data found")
    else:
        print("❌ No current session found")

if __name__ == "__main__":
    asyncio.run(check_redis())
