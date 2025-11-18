"""
Enhanced Redis Client for Security Service
Extends db_utils.CacheConnection with security-specific operations
"""
import os
import json
import time
from typing import Optional, Dict, List, Any
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class SecurityRedisClient:
    """
    Enhanced Redis client for security service operations:
    - Session management (token revocation, active sessions)
    - Rate limiting (sliding window counters)
    - Permission caching
    - MFA temporary codes
    """

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.enabled = True

    async def connect(self):
        """Initialize Redis connection with security service configuration"""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Security Redis client connected to {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Security features disabled.")
            self.enabled = False
            self.client = None
            raise

    async def disconnect(self):
        """Close Redis connection gracefully"""
        if self.client:
            await self.client.aclose()
            logger.info("Security Redis client disconnected")

    # ==================== Session Management ====================

    async def blacklist_token(self, token: str, expiry_seconds: int):
        """
        Add token to blacklist (for logout/revocation)

        Args:
            token: JWT token to blacklist
            expiry_seconds: How long to keep in blacklist (should match token expiry)
        """
        if not self.enabled or not self.client:
            return False
        try:
            key = f"blacklist:token:{token}"
            await self.client.setex(key, expiry_seconds, "1")
            logger.info(f"Token blacklisted for {expiry_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"blacklist:token:{token}"
            exists = await self.client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False

    async def store_refresh_token(self, user_id: str, refresh_token: str, expiry_seconds: int):
        """
        Store refresh token for user

        Args:
            user_id: User identifier
            refresh_token: Refresh token value
            expiry_seconds: Refresh token TTL (default: 7 days)
        """
        if not self.enabled or not self.client:
            return False
        try:
            key = f"refresh:user:{user_id}"
            # Store as hash to support multiple devices in future
            await self.client.hset(key, refresh_token, int(time.time()))
            await self.client.expire(key, expiry_seconds)
            logger.info(f"Refresh token stored for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")
            return False

    async def verify_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Verify refresh token exists for user"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"refresh:user:{user_id}"
            exists = await self.client.hexists(key, refresh_token)
            return bool(exists)
        except Exception as e:
            logger.error(f"Error verifying refresh token: {e}")
            return False

    async def revoke_refresh_token(self, user_id: str, refresh_token: str):
        """Revoke a specific refresh token"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"refresh:user:{user_id}"
            await self.client.hdel(key, refresh_token)
            logger.info(f"Refresh token revoked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False

    async def revoke_all_refresh_tokens(self, user_id: str):
        """Revoke all refresh tokens for user (force logout all devices)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"refresh:user:{user_id}"
            await self.client.delete(key)
            logger.info(f"All refresh tokens revoked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke all refresh tokens: {e}")
            return False

    async def get_active_sessions(self, user_id: str) -> int:
        """Get count of active sessions for user"""
        if not self.enabled or not self.client:
            return 0
        try:
            key = f"refresh:user:{user_id}"
            count = await self.client.hlen(key)
            return count
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return 0

    # ==================== Rate Limiting (Sliding Window) ====================

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using sliding window algorithm with Redis sorted sets

        Args:
            identifier: Unique identifier (e.g., "ip:192.168.1.1" or "user:123")
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            (allowed, current_count, retry_after_seconds)
        """
        if not self.enabled or not self.client:
            return True, 0, 0

        try:
            key = f"ratelimit:{identifier}"
            now = time.time()
            window_start = now - window_seconds

            # Use Redis pipeline for atomic operations
            pipe = self.client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count entries in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(now): now})

            # Set expiry on key
            pipe.expire(key, window_seconds)

            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]  # zcard result

            if current_count < limit:
                logger.debug(f"Rate limit OK for {identifier}: {current_count}/{limit}")
                return True, current_count + 1, 0
            else:
                # Get oldest entry to calculate retry_after
                oldest = await self.client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int((oldest_time + window_seconds) - now)
                else:
                    retry_after = window_seconds

                logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{limit}")
                return False, current_count, max(retry_after, 1)

        except Exception as e:
            logger.error(f"Rate limit check error: {e}. Allowing request.")
            return True, 0, 0

    async def reset_rate_limit(self, identifier: str):
        """Reset rate limit for identifier (admin override)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"ratelimit:{identifier}"
            await self.client.delete(key)
            logger.info(f"Rate limit reset for {identifier}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    # ==================== Account Lockout ====================

    async def record_failed_login(self, identifier: str, lockout_duration: int = 1800) -> int:
        """
        Record failed login attempt

        Args:
            identifier: Username or IP address
            lockout_duration: How long to track failures (default: 30 min)

        Returns:
            Current count of failed attempts
        """
        if not self.enabled or not self.client:
            return 0
        try:
            key = f"failed_login:{identifier}"
            count = await self.client.incr(key)
            if count == 1:
                # First failure, set expiration
                await self.client.expire(key, lockout_duration)
            logger.debug(f"Failed login recorded for {identifier}: count={count}")
            return count
        except Exception as e:
            logger.error(f"Error recording failed login: {e}")
            return 0

    async def get_failed_login_count(self, identifier: str) -> int:
        """Get count of failed login attempts"""
        if not self.enabled or not self.client:
            return 0
        try:
            key = f"failed_login:{identifier}"
            count = await self.client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting failed login count: {e}")
            return 0

    async def reset_failed_logins(self, identifier: str):
        """Reset failed login counter (after successful login)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"failed_login:{identifier}"
            await self.client.delete(key)
            logger.debug(f"Failed login counter reset for {identifier}")
            return True
        except Exception as e:
            logger.error(f"Error resetting failed logins: {e}")
            return False

    async def lock_account(self, user_id: str, duration_seconds: int = 1800):
        """
        Lock user account

        Args:
            user_id: User identifier
            duration_seconds: Lock duration (default: 30 min)
        """
        if not self.enabled or not self.client:
            return False
        try:
            key = f"account_locked:{user_id}"
            await self.client.setex(key, duration_seconds, "1")
            logger.warning(f"Account locked for user {user_id} for {duration_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Error locking account: {e}")
            return False

    async def is_account_locked(self, user_id: str) -> tuple[bool, int]:
        """
        Check if account is locked

        Returns:
            (is_locked, seconds_remaining)
        """
        if not self.enabled or not self.client:
            return False, 0
        try:
            key = f"account_locked:{user_id}"
            ttl = await self.client.ttl(key)
            if ttl > 0:
                return True, ttl
            return False, 0
        except Exception as e:
            logger.error(f"Error checking account lock: {e}")
            return False, 0

    async def unlock_account(self, user_id: str):
        """Manually unlock account (admin action)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"account_locked:{user_id}"
            await self.client.delete(key)
            logger.info(f"Account unlocked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error unlocking account: {e}")
            return False

    # ==================== Permission Caching ====================

    async def cache_permissions(self, user_id: str, permissions: List[str], ttl: int = 300):
        """Cache user permissions (5 min default)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"permissions:user:{user_id}"
            await self.client.setex(key, ttl, json.dumps(permissions))
            logger.debug(f"Permissions cached for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching permissions: {e}")
            return False

    async def get_cached_permissions(self, user_id: str) -> Optional[List[str]]:
        """Get cached permissions"""
        if not self.enabled or not self.client:
            return None
        try:
            key = f"permissions:user:{user_id}"
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached permissions: {e}")
            return None

    async def invalidate_permissions_cache(self, user_id: str):
        """Invalidate permission cache (after role change)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"permissions:user:{user_id}"
            await self.client.delete(key)
            logger.info(f"Permission cache invalidated for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating permission cache: {e}")
            return False

    # ==================== MFA Temporary Storage ====================

    async def store_mfa_setup_secret(self, user_id: str, secret: str, ttl: int = 600):
        """Store MFA secret temporarily during setup (10 min default)"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"mfa_setup:{user_id}"
            await self.client.setex(key, ttl, secret)
            logger.debug(f"MFA setup secret stored for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing MFA setup secret: {e}")
            return False

    async def get_mfa_setup_secret(self, user_id: str) -> Optional[str]:
        """Get MFA setup secret"""
        if not self.enabled or not self.client:
            return None
        try:
            key = f"mfa_setup:{user_id}"
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting MFA setup secret: {e}")
            return None

    async def delete_mfa_setup_secret(self, user_id: str):
        """Delete MFA setup secret after confirmation"""
        if not self.enabled or not self.client:
            return False
        try:
            key = f"mfa_setup:{user_id}"
            await self.client.delete(key)
            logger.debug(f"MFA setup secret deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting MFA setup secret: {e}")
            return False

    # ==================== Health Check ====================

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health and return stats"""
        if not self.enabled or not self.client:
            return {"status": "disabled", "connected": False}

        try:
            await self.client.ping()
            info = await self.client.info()
            return {
                "status": "healthy",
                "connected": True,
                "version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_days": info.get("uptime_in_days", 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "connected": False, "error": str(e)}


# Global instance
security_redis = SecurityRedisClient()
