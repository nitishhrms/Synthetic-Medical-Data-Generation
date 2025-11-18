"""
Token Refresh Management
Handles refresh token generation, validation, and rotation
"""
import os
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from jose import jwt

from session_manager import session_manager
import auth

logger = logging.getLogger(__name__)

# Configuration
REFRESH_TOKEN_EXPIRY_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRY_DAYS", "7"))
REFRESH_TOKEN_LENGTH = 64  # 64 bytes = 128 hex characters
ROTATE_ON_REFRESH = True  # Security best practice: rotate refresh token on each use


class TokenRefreshManager:
    """
    Manages refresh token lifecycle

    Features:
    - Secure refresh token generation
    - Token rotation on use (prevents token replay)
    - Redis-backed storage
    - Expiry management
    - Device tracking (future enhancement)
    """

    def __init__(self):
        self.session_manager = session_manager
        self.expiry_days = REFRESH_TOKEN_EXPIRY_DAYS
        self.rotate_on_use = ROTATE_ON_REFRESH

    # ==================== Token Generation ====================

    def generate_refresh_token(self) -> str:
        """
        Generate a cryptographically secure random refresh token

        Returns:
            Secure random token (128 hex characters)
        """
        return secrets.token_urlsafe(REFRESH_TOKEN_LENGTH)

    def generate_access_token(self, user: Dict) -> Tuple[str, int]:
        """
        Generate a new access token (JWT)

        Args:
            user: User dictionary with id, username, roles

        Returns:
            (access_token, expiry_timestamp) tuple
        """
        access_token = auth.create_access_token(user)

        # Calculate expiry timestamp
        expiry_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        expiry_timestamp = int((datetime.utcnow() + timedelta(minutes=expiry_minutes)).timestamp())

        return access_token, expiry_timestamp

    # ==================== Token Issuance ====================

    async def issue_tokens(
        self,
        user: Dict,
        device_info: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Issue both access and refresh tokens

        Args:
            user: User dictionary with id, username, roles, etc.
            device_info: Optional device information (user_agent, ip)

        Returns:
            Dictionary with tokens and metadata
        """
        try:
            user_id = str(user.get("user_id") or user.get("id"))

            # Generate access token
            access_token, access_expiry = self.generate_access_token(user)

            # Generate refresh token
            refresh_token = self.generate_refresh_token()

            # Store refresh token in Redis
            success = await self.session_manager.create_refresh_token(
                user_id,
                refresh_token,
                device_info
            )

            if not success:
                logger.error(f"Failed to store refresh token for user {user_id}")
                raise Exception("Failed to create session")

            logger.info(f"Tokens issued for user {user_id}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "access_token_expires_in": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) * 60,
                "access_token_expires_at": access_expiry,
                "refresh_token_expires_in": self.expiry_days * 24 * 60 * 60,
                "issued_at": int(datetime.utcnow().timestamp())
            }

        except Exception as e:
            logger.error(f"Token issuance failed: {e}")
            raise

    # ==================== Token Refresh ====================

    async def refresh_access_token(
        self,
        refresh_token: str,
        user_id: str,
        user_data: Dict
    ) -> Tuple[bool, Optional[Dict], str]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Current refresh token
            user_id: User identifier
            user_data: User data for new access token

        Returns:
            (success, new_tokens_dict, message) tuple
        """
        try:
            # Validate refresh token exists in Redis
            is_valid = await self.session_manager.validate_refresh_token(user_id, refresh_token)

            if not is_valid:
                logger.warning(f"Invalid refresh token for user {user_id}")
                return False, None, "Invalid or expired refresh token"

            # Generate new access token
            new_access_token, access_expiry = self.generate_access_token(user_data)

            result = {
                "access_token": new_access_token,
                "token_type": "bearer",
                "access_token_expires_in": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) * 60,
                "access_token_expires_at": access_expiry,
                "refreshed_at": int(datetime.utcnow().timestamp())
            }

            # Token rotation (security best practice)
            if self.rotate_on_use:
                new_refresh_token = self.generate_refresh_token()

                # Rotate refresh token in Redis
                rotation_success = await self.session_manager.rotate_refresh_token(
                    user_id,
                    refresh_token,
                    new_refresh_token
                )

                if rotation_success:
                    result["refresh_token"] = new_refresh_token
                    result["refresh_token_rotated"] = True
                    logger.info(f"Refresh token rotated for user {user_id}")
                else:
                    logger.warning(f"Refresh token rotation failed for user {user_id}")
                    result["refresh_token_rotated"] = False
            else:
                result["refresh_token_rotated"] = False

            logger.info(f"Access token refreshed for user {user_id}")
            return True, result, "Token refresh successful"

        except Exception as e:
            logger.error(f"Token refresh failed for user {user_id}: {e}")
            return False, None, f"Token refresh failed: {str(e)}"

    # ==================== Token Validation ====================

    async def validate_refresh_token(
        self,
        refresh_token: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Validate refresh token without refreshing

        Args:
            refresh_token: Refresh token to validate
            user_id: User identifier

        Returns:
            (is_valid, message) tuple
        """
        try:
            is_valid = await self.session_manager.validate_refresh_token(user_id, refresh_token)

            if is_valid:
                return True, "Refresh token is valid"
            else:
                return False, "Invalid or expired refresh token"

        except Exception as e:
            logger.error(f"Refresh token validation error: {e}")
            return False, str(e)

    # ==================== Token Revocation ====================

    async def revoke_refresh_token(
        self,
        refresh_token: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Revoke a specific refresh token (single device logout)

        Args:
            refresh_token: Refresh token to revoke
            user_id: User identifier

        Returns:
            (success, message) tuple
        """
        try:
            success = await self.session_manager.revoke_refresh_token(user_id, refresh_token)

            if success:
                return True, "Refresh token revoked successfully"
            else:
                return False, "Failed to revoke refresh token"

        except Exception as e:
            logger.error(f"Refresh token revocation error: {e}")
            return False, str(e)

    async def revoke_all_refresh_tokens(
        self,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Revoke all refresh tokens for user (all devices logout)

        Args:
            user_id: User identifier

        Returns:
            (success, message) tuple
        """
        try:
            success = await self.session_manager.revoke_all_refresh_tokens(user_id)

            if success:
                return True, "All refresh tokens revoked successfully"
            else:
                return False, "Failed to revoke refresh tokens"

        except Exception as e:
            logger.error(f"Bulk refresh token revocation error: {e}")
            return False, str(e)

    # ==================== Token Extraction ====================

    def extract_user_from_access_token(self, access_token: str) -> Optional[Dict]:
        """
        Extract user information from access token

        Args:
            access_token: JWT access token

        Returns:
            User dict or None if invalid
        """
        try:
            payload = auth.verify_token(access_token)
            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "roles": payload.get("roles", [])
            }
        except Exception as e:
            logger.error(f"Failed to extract user from token: {e}")
            return None

    # ==================== Security Checks ====================

    async def check_session_limit(
        self,
        user_id: str
    ) -> Tuple[bool, int, str]:
        """
        Check if user has reached maximum concurrent sessions

        Args:
            user_id: User identifier

        Returns:
            (can_create, current_count, message) tuple
        """
        try:
            active_sessions = await self.session_manager.get_active_session_count(user_id)
            max_sessions = self.session_manager.max_sessions

            if active_sessions >= max_sessions:
                return False, active_sessions, (
                    f"Maximum concurrent sessions ({max_sessions}) reached. "
                    "Please logout from another device."
                )

            return True, active_sessions, f"OK - {active_sessions}/{max_sessions} sessions"

        except Exception as e:
            logger.error(f"Session limit check error: {e}")
            return True, 0, "Session limit check failed - allowing login"

    async def force_password_change_logout(
        self,
        user_id: str
    ) -> bool:
        """
        Force logout all sessions (for password change)

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        try:
            success = await self.session_manager.force_logout_all_sessions(user_id)

            if success:
                logger.warning(f"All sessions terminated for user {user_id} due to password change")

            return success

        except Exception as e:
            logger.error(f"Force logout error: {e}")
            return False

    # ==================== Monitoring ====================

    async def get_token_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        Get token statistics

        Args:
            user_id: Optional user ID to get specific stats

        Returns:
            Statistics dictionary
        """
        stats = {
            "refresh_token_expiry_days": self.expiry_days,
            "access_token_expiry_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            "rotation_enabled": self.rotate_on_use
        }

        if user_id:
            try:
                active_sessions = await self.session_manager.get_active_session_count(user_id)
                max_sessions = self.session_manager.max_sessions

                stats["user_id"] = user_id
                stats["active_sessions"] = active_sessions
                stats["max_sessions"] = max_sessions
                stats["sessions_available"] = max(0, max_sessions - active_sessions)

            except Exception as e:
                logger.error(f"Error getting user token stats: {e}")
                stats["error"] = str(e)

        return stats


# Global instance
token_refresh_manager = TokenRefreshManager()
