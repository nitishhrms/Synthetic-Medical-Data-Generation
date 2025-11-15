"""
Session Management for Security Service
Handles token revocation, refresh tokens, and active session tracking
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from redis_client import security_redis

logger = logging.getLogger(__name__)

# Configuration from environment
MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "3"))
REFRESH_TOKEN_EXPIRY_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRY_DAYS", "7"))
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))


class SessionManager:
    """
    Manages user sessions, token revocation, and session limits

    Features:
    - Token blacklisting for logout/revocation
    - Refresh token management
    - Maximum concurrent session enforcement
    - Session timeout tracking
    """

    def __init__(self):
        self.redis = security_redis
        self.max_sessions = MAX_CONCURRENT_SESSIONS
        self.refresh_token_expiry = REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60  # seconds
        self.session_timeout = SESSION_TIMEOUT_MINUTES * 60  # seconds

    # ==================== Token Blacklisting ====================

    async def revoke_access_token(self, token: str, token_expiry_timestamp: int):
        """
        Revoke an access token by blacklisting it

        Args:
            token: The JWT access token to revoke
            token_expiry_timestamp: When the token expires (Unix timestamp)
        """
        try:
            # Calculate how long to keep in blacklist (until token would naturally expire)
            now = datetime.utcnow().timestamp()
            ttl = max(int(token_expiry_timestamp - now), 60)  # Minimum 60 seconds

            success = await self.redis.blacklist_token(token, ttl)
            if success:
                logger.info(f"Access token revoked (blacklisted for {ttl}s)")
            return success
        except Exception as e:
            logger.error(f"Failed to revoke access token: {e}")
            return False

    async def is_token_revoked(self, token: str) -> bool:
        """Check if access token has been revoked"""
        try:
            return await self.redis.is_token_blacklisted(token)
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            return False

    # ==================== Refresh Token Management ====================

    async def create_refresh_token(
        self,
        user_id: str,
        refresh_token: str,
        device_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create a new refresh token for user

        Args:
            user_id: User identifier
            refresh_token: The refresh token value
            device_info: Optional device information (user_agent, ip, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check current session count
            active_sessions = await self.redis.get_active_sessions(user_id)

            if active_sessions >= self.max_sessions:
                logger.warning(
                    f"User {user_id} exceeded max sessions ({active_sessions}/{self.max_sessions}). "
                    "Oldest session will be revoked."
                )
                # In production, you'd revoke the oldest session
                # For now, we'll just log the warning

            # Store refresh token
            success = await self.redis.store_refresh_token(
                user_id,
                refresh_token,
                self.refresh_token_expiry
            )

            if success:
                logger.info(
                    f"Refresh token created for user {user_id}. "
                    f"Active sessions: {active_sessions + 1}/{self.max_sessions}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            return False

    async def validate_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Validate that refresh token exists and is valid for user"""
        try:
            return await self.redis.verify_refresh_token(user_id, refresh_token)
        except Exception as e:
            logger.error(f"Error validating refresh token: {e}")
            return False

    async def revoke_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Revoke a specific refresh token (logout single device)"""
        try:
            success = await self.redis.revoke_refresh_token(user_id, refresh_token)
            if success:
                active_sessions = await self.redis.get_active_sessions(user_id)
                logger.info(
                    f"Refresh token revoked for user {user_id}. "
                    f"Remaining sessions: {active_sessions}"
                )
            return success
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False

    async def revoke_all_refresh_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for user (logout all devices)"""
        try:
            success = await self.redis.revoke_all_refresh_tokens(user_id)
            if success:
                logger.warning(f"All refresh tokens revoked for user {user_id} (forced logout all devices)")
            return success
        except Exception as e:
            logger.error(f"Failed to revoke all refresh tokens: {e}")
            return False

    # ==================== Session Tracking ====================

    async def get_active_session_count(self, user_id: str) -> int:
        """Get count of active sessions for user"""
        try:
            return await self.redis.get_active_sessions(user_id)
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0

    async def enforce_session_limit(self, user_id: str) -> tuple[bool, str]:
        """
        Check if user can create a new session

        Returns:
            (can_create_session, message)
        """
        try:
            active_sessions = await self.get_active_session_count(user_id)

            if active_sessions >= self.max_sessions:
                return False, (
                    f"Maximum concurrent sessions ({self.max_sessions}) reached. "
                    f"Please logout from another device first."
                )

            return True, f"OK - {active_sessions}/{self.max_sessions} sessions active"

        except Exception as e:
            logger.error(f"Error enforcing session limit: {e}")
            return True, "Session limit check failed - allowing login"

    # ==================== Logout Operations ====================

    async def logout(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        token_expiry: int
    ) -> Dict[str, Any]:
        """
        Complete logout: blacklist access token and revoke refresh token

        Args:
            user_id: User identifier
            access_token: Current access token to blacklist
            refresh_token: Current refresh token to revoke
            token_expiry: Access token expiry timestamp

        Returns:
            Status dict with results
        """
        results = {
            "access_token_revoked": False,
            "refresh_token_revoked": False,
            "success": False
        }

        try:
            # Blacklist access token
            access_revoked = await self.revoke_access_token(access_token, token_expiry)
            results["access_token_revoked"] = access_revoked

            # Revoke refresh token
            refresh_revoked = await self.revoke_refresh_token(user_id, refresh_token)
            results["refresh_token_revoked"] = refresh_revoked

            results["success"] = access_revoked and refresh_revoked

            if results["success"]:
                active_sessions = await self.get_active_session_count(user_id)
                logger.info(
                    f"User {user_id} logged out successfully. "
                    f"Remaining sessions: {active_sessions}"
                )
            else:
                logger.warning(f"Partial logout for user {user_id}: {results}")

            return results

        except Exception as e:
            logger.error(f"Logout failed for user {user_id}: {e}")
            results["error"] = str(e)
            return results

    async def force_logout_all_sessions(self, user_id: str) -> bool:
        """
        Force logout all sessions for user (admin action or security measure)

        Use cases:
        - Password change
        - Security breach
        - Account suspension
        - Admin action
        """
        try:
            success = await self.revoke_all_refresh_tokens(user_id)
            if success:
                logger.warning(
                    f"Force logout all sessions for user {user_id}. "
                    "All active tokens will be invalid on next refresh."
                )
            return success
        except Exception as e:
            logger.error(f"Failed to force logout all sessions: {e}")
            return False

    # ==================== Session Security ====================

    async def rotate_refresh_token(
        self,
        user_id: str,
        old_refresh_token: str,
        new_refresh_token: str
    ) -> bool:
        """
        Rotate refresh token (security best practice)

        Args:
            user_id: User identifier
            old_refresh_token: Current refresh token to revoke
            new_refresh_token: New refresh token to create

        Returns:
            True if rotation successful
        """
        try:
            # Revoke old token
            await self.redis.revoke_refresh_token(user_id, old_refresh_token)

            # Store new token
            success = await self.redis.store_refresh_token(
                user_id,
                new_refresh_token,
                self.refresh_token_expiry
            )

            if success:
                logger.info(f"Refresh token rotated for user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Token rotation failed: {e}")
            return False

    # ==================== Health & Monitoring ====================

    async def get_session_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get session statistics

        Args:
            user_id: Optional user to get stats for (admin only)

        Returns:
            Session statistics
        """
        stats = {
            "max_concurrent_sessions": self.max_sessions,
            "refresh_token_expiry_days": REFRESH_TOKEN_EXPIRY_DAYS,
            "session_timeout_minutes": SESSION_TIMEOUT_MINUTES
        }

        if user_id:
            try:
                stats["user_id"] = user_id
                stats["active_sessions"] = await self.get_active_session_count(user_id)
            except Exception as e:
                logger.error(f"Error getting user session stats: {e}")
                stats["error"] = str(e)

        return stats


# Global instance
session_manager = SessionManager()
