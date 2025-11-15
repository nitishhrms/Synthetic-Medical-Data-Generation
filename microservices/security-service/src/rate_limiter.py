"""
Enterprise Rate Limiter with Sliding Window Algorithm
Uses Redis sorted sets for distributed rate limiting
"""
import logging
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time

from redis_client import security_redis
from rate_limit_config import (
    RateLimitConfig,
    get_rate_limit_for_endpoint,
    get_rate_limit_message,
    RATE_LIMIT_ENABLED
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Enterprise-grade rate limiter using Redis sliding window algorithm

    Features:
    - Distributed rate limiting (works across multiple instances)
    - Sliding window algorithm (more accurate than fixed window)
    - Per-user and per-IP limits
    - Per-endpoint customization
    - Role-based limits
    - Graceful degradation if Redis unavailable
    """

    def __init__(self):
        self.redis = security_redis
        self.enabled = RATE_LIMIT_ENABLED

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        identifier_type: str = "generic"
    ) -> Tuple[bool, int, int, str]:
        """
        Check rate limit for identifier

        Args:
            identifier: Unique identifier (e.g., "user:123", "ip:192.168.1.1")
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            identifier_type: Type of identifier for logging (user, ip, endpoint)

        Returns:
            (allowed, current_count, retry_after, message)
        """
        if not self.enabled:
            return True, 0, 0, "Rate limiting disabled"

        # Unlimited access (admin or disabled)
        if limit == 0:
            return True, 0, 0, "Unlimited access"

        try:
            allowed, current_count, retry_after = await self.redis.check_rate_limit(
                identifier,
                limit,
                window_seconds
            )

            if allowed:
                message = f"OK - {current_count}/{limit} requests used"
                logger.debug(f"Rate limit check passed for {identifier_type}:{identifier}: {message}")
                return True, current_count, 0, message
            else:
                message = f"Rate limit exceeded - {current_count}/{limit} requests. Retry after {retry_after}s"
                logger.warning(f"Rate limit exceeded for {identifier_type}:{identifier}: {message}")
                return False, current_count, retry_after, message

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}. Allowing request (fail-open).")
            return True, 0, 0, "Rate limit check failed - allowing request"

    async def check_endpoint_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> Tuple[bool, dict]:
        """
        Check rate limit for an endpoint request

        Checks multiple limits:
        1. IP-based limit (for DDoS protection)
        2. User-based limit (if authenticated)
        3. Endpoint-specific limit

        Args:
            request: FastAPI request object
            user_id: Authenticated user ID (optional)
            user_role: User's role (optional)

        Returns:
            (allowed, details_dict)
        """
        if not self.enabled:
            return True, {"rate_limiting": "disabled"}

        endpoint = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Get rate limit configuration for this endpoint and role
        limit, window = get_rate_limit_for_endpoint(
            endpoint,
            user_role or "anonymous"
        )

        details = {
            "endpoint": endpoint,
            "limit": limit,
            "window_seconds": window,
            "limit_description": get_rate_limit_message(limit, window)
        }

        # Check 1: IP-based rate limit (prevent DDoS)
        ip_allowed, ip_count, ip_retry, ip_message = await self.check_rate_limit(
            f"ip:{client_ip}:{endpoint}",
            limit,
            window,
            "ip"
        )

        details["ip_limit"] = {
            "allowed": ip_allowed,
            "count": ip_count,
            "retry_after": ip_retry,
            "message": ip_message
        }

        if not ip_allowed:
            return False, details

        # Check 2: User-based rate limit (if authenticated)
        if user_id:
            user_allowed, user_count, user_retry, user_message = await self.check_rate_limit(
                f"user:{user_id}:{endpoint}",
                limit,
                window,
                "user"
            )

            details["user_limit"] = {
                "allowed": user_allowed,
                "count": user_count,
                "retry_after": user_retry,
                "message": user_message
            }

            if not user_allowed:
                return False, details

        return True, details

    async def check_login_rate_limit(
        self,
        username: str,
        ip_address: str
    ) -> Tuple[bool, dict]:
        """
        Special rate limiting for login attempts (dual: IP + username)

        Args:
            username: Login username
            ip_address: Client IP address

        Returns:
            (allowed, details_dict)
        """
        if not self.enabled:
            return True, {"rate_limiting": "disabled"}

        ip_limit, ip_window = RateLimitConfig.LOGIN_BY_IP
        user_limit, user_window = RateLimitConfig.LOGIN_BY_USERNAME

        details = {
            "ip_limit": get_rate_limit_message(ip_limit, ip_window),
            "username_limit": get_rate_limit_message(user_limit, user_window)
        }

        # Check IP-based login limit
        ip_allowed, ip_count, ip_retry, ip_message = await self.check_rate_limit(
            f"login:ip:{ip_address}",
            ip_limit,
            ip_window,
            "login_ip"
        )

        details["ip_check"] = {
            "allowed": ip_allowed,
            "count": ip_count,
            "retry_after": ip_retry,
            "message": ip_message
        }

        if not ip_allowed:
            return False, details

        # Check username-based login limit
        user_allowed, user_count, user_retry, user_message = await self.check_rate_limit(
            f"login:user:{username}",
            user_limit,
            user_window,
            "login_user"
        )

        details["username_check"] = {
            "allowed": user_allowed,
            "count": user_count,
            "retry_after": user_retry,
            "message": user_message
        }

        if not user_allowed:
            return False, details

        return True, details

    async def reset_rate_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for identifier (admin action)

        Args:
            identifier: Rate limit identifier to reset

        Returns:
            True if successful
        """
        try:
            success = await self.redis.reset_rate_limit(identifier)
            if success:
                logger.info(f"Rate limit reset for {identifier} (admin action)")
            return success
        except Exception as e:
            logger.error(f"Failed to reset rate limit for {identifier}: {e}")
            return False


# Global instance
rate_limiter = RateLimiter()


# ==================== FastAPI Dependency ====================

async def rate_limit_dependency(request: Request):
    """
    FastAPI dependency for rate limiting

    Usage in endpoint:
        @app.get("/some-endpoint", dependencies=[Depends(rate_limit_dependency)])
        async def some_endpoint():
            return {"message": "Hello"}
    """
    if not RATE_LIMIT_ENABLED:
        return

    # Try to get user info from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", None)

    allowed, details = await rate_limiter.check_endpoint_rate_limit(
        request,
        user_id,
        user_role
    )

    if not allowed:
        # Calculate retry-after header
        retry_after = 0
        if "ip_limit" in details and not details["ip_limit"]["allowed"]:
            retry_after = details["ip_limit"]["retry_after"]
        elif "user_limit" in details and not details["user_limit"]["allowed"]:
            retry_after = details["user_limit"]["retry_after"]

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after_seconds": retry_after,
                "limit_info": details
            },
            headers={"Retry-After": str(retry_after)} if retry_after > 0 else {}
        )


# ==================== Decorator for Rate Limiting ====================

def rate_limit(limit: int, window: int, identifier_key: str = "user_id"):
    """
    Decorator for custom rate limiting on specific endpoints

    Args:
        limit: Max requests allowed
        window: Time window in seconds
        identifier_key: Key in request.state to use as identifier

    Usage:
        @app.post("/expensive-operation")
        @rate_limit(limit=10, window=3600, identifier_key="user_id")
        async def expensive_operation(request: Request):
            return {"status": "ok"}
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if not RATE_LIMIT_ENABLED:
                return await func(request, *args, **kwargs)

            # Get identifier from request state
            identifier = getattr(request.state, identifier_key, None)
            if not identifier:
                # Fall back to IP if no user identifier
                identifier = f"ip:{request.client.host if request.client else 'unknown'}"
            else:
                identifier = f"{identifier_key}:{identifier}"

            # Check rate limit
            allowed, current_count, retry_after, message = await rate_limiter.check_rate_limit(
                identifier,
                limit,
                window,
                "custom"
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": message,
                        "current_count": current_count,
                        "limit": limit,
                        "retry_after_seconds": retry_after,
                        "limit_description": get_rate_limit_message(limit, window)
                    },
                    headers={"Retry-After": str(retry_after)}
                )

            # Execute original function
            return await func(request, *args, **kwargs)

        return wrapper
    return decorator


# ==================== Rate Limit Response Headers ====================

async def add_rate_limit_headers(request: Request, call_next):
    """
    Middleware to add rate limit info to response headers

    Headers added:
    - X-RateLimit-Limit: Max requests allowed
    - X-RateLimit-Remaining: Requests remaining
    - X-RateLimit-Reset: Unix timestamp when limit resets
    """
    response = await call_next(request)

    if not RATE_LIMIT_ENABLED:
        return response

    # Get user info
    user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", None)
    endpoint = request.url.path

    try:
        # Get rate limit for endpoint
        limit, window = get_rate_limit_for_endpoint(endpoint, user_role or "anonymous")

        if limit > 0:  # Only add headers if rate limit exists
            # Calculate reset timestamp
            reset_time = int(time.time()) + window

            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Window"] = str(window)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

            # Note: We don't calculate "remaining" here to avoid extra Redis calls
            # Client can infer from 429 responses

    except Exception as e:
        logger.debug(f"Failed to add rate limit headers: {e}")

    return response
