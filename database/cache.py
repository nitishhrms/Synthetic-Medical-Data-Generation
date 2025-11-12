"""
Redis cache manager for Clinical Trials Platform
Provides caching, rate limiting, and performance optimization
"""
import redis.asyncio as redis
import json
from typing import Optional, Any
import hashlib
import os


class RedisCache:
    """Redis cache manager for clinical trials"""

    def __init__(self):
        self.client = None

    async def connect(self):
        """Connect to Redis"""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))

            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5
            )
            await self.client.ping()
            print("✅ Redis connected")
        except Exception as e:
            print(f"⚠️  Redis not available: {e}")
            print("   Continuing without cache (degraded performance)")
            self.client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            print("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None

    async def setex(self, key: str, ttl: int, value: str):
        """Set value with expiration"""
        if not self.client:
            return
        try:
            await self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis SETEX error: {e}")

    async def delete(self, pattern: str):
        """Delete keys matching pattern"""
        if not self.client:
            return
        try:
            # Handle wildcard patterns
            if '*' in pattern:
                keys = []
                async for key in self.client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self.client.delete(*keys)
            else:
                await self.client.delete(pattern)
        except Exception as e:
            print(f"Redis DELETE error: {e}")

    async def cache_query_result(self, query: str, params: tuple, result: Any, ttl: int = 300):
        """Cache database query results"""
        if not self.client:
            return

        # Create cache key from query + params
        cache_key = f"query:{hashlib.md5((query + str(params)).encode()).hexdigest()}"

        try:
            await self.client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
        except Exception as e:
            print(f"Redis cache_query_result error: {e}")

    async def get_cached_query(self, query: str, params: tuple) -> Optional[Any]:
        """Get cached query result"""
        if not self.client:
            return None

        cache_key = f"query:{hashlib.md5((query + str(params)).encode()).hexdigest()}"

        try:
            cached = await self.client.get(cache_key)
            return json.loads(cached) if cached else None
        except Exception as e:
            print(f"Redis get_cached_query error: {e}")
            return None

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.client:
            return 0
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return 0

    async def rate_limit_check(self, user_id: str, limit: int = 100, window: int = 60) -> bool:
        """
        Check rate limiting

        Args:
            user_id: User identifier
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            True if under limit, False if exceeded
        """
        if not self.client:
            return True  # Allow if Redis is down

        key = f"rate_limit:{user_id}"
        try:
            current = await self.client.incr(key)
            if current == 1:
                await self.client.expire(key, window)
            return current <= limit
        except Exception as e:
            print(f"Redis rate_limit_check error: {e}")
            return True

    async def cache_patient_data(self, patient_id: str, data: dict, ttl: int = 300):
        """Cache patient data"""
        await self.setex(f"patient:{patient_id}", ttl, json.dumps(data, default=str))

    async def get_patient_cache(self, patient_id: str) -> Optional[dict]:
        """Get cached patient data"""
        cached = await self.get(f"patient:{patient_id}")
        return json.loads(cached) if cached else None

    async def invalidate_patient_cache(self, patient_id: str):
        """Invalidate patient cache"""
        await self.delete(f"patient:{patient_id}")
        await self.delete(f"vitals:{patient_id}:*")

    async def set_session(self, session_id: str, data: dict, ttl: int = 3600):
        """Store session data"""
        await self.setex(f"session:{session_id}", ttl, json.dumps(data))

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        cached = await self.get(f"session:{session_id}")
        return json.loads(cached) if cached else None

    async def health_check(self) -> dict:
        """Check Redis health"""
        if not self.client:
            return {"status": "unavailable", "error": "Not connected"}

        try:
            await self.client.ping()
            info = await self.client.info()
            return {
                "status": "healthy",
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown'),
                "uptime_in_seconds": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global Redis instance
cache = RedisCache()
