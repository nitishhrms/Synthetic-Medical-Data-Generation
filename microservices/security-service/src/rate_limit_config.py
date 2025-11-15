"""
Rate Limit Configuration for Security Service
Defines rate limits per endpoint and user role
"""
import os
from typing import Dict, Tuple
from enum import Enum

# Global rate limit toggle
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"


class UserRole(str, Enum):
    """User role enumeration"""
    VIEWER = "viewer"
    RESEARCHER = "researcher"
    DATA_ANALYST = "data_analyst"
    ADMIN = "admin"
    AUDITOR = "auditor"
    ANONYMOUS = "anonymous"  # Not logged in


class RateLimitConfig:
    """
    Rate limit configuration for different endpoints and user roles

    Format: (requests, window_seconds)
    Example: (100, 60) = 100 requests per 60 seconds
    """

    # ==================== Authentication Endpoints ====================

    # Login rate limits (IP-based + username-based)
    LOGIN_BY_IP: Tuple[int, int] = (5, 900)  # 5 attempts per 15 minutes per IP
    LOGIN_BY_USERNAME: Tuple[int, int] = (5, 900)  # 5 attempts per 15 minutes per username

    # Registration (IP-based to prevent spam)
    REGISTER_BY_IP: Tuple[int, int] = (3, 3600)  # 3 registrations per hour per IP

    # Token refresh
    TOKEN_REFRESH: Tuple[int, int] = (10, 300)  # 10 refreshes per 5 minutes

    # Password reset requests
    PASSWORD_RESET_BY_IP: Tuple[int, int] = (3, 3600)  # 3 requests per hour
    PASSWORD_RESET_BY_EMAIL: Tuple[int, int] = (3, 3600)  # 3 requests per hour per email

    # MFA verification attempts
    MFA_VERIFY: Tuple[int, int] = (5, 300)  # 5 attempts per 5 minutes

    # ==================== General API Endpoints ====================

    # API rate limits per user role (requests per minute)
    API_LIMITS_PER_ROLE: Dict[str, Tuple[int, int]] = {
        UserRole.ANONYMOUS: (20, 60),  # 20 requests per minute (unauthenticated)
        UserRole.VIEWER: (100, 60),  # 100 requests per minute
        UserRole.RESEARCHER: (500, 60),  # 500 requests per minute
        UserRole.DATA_ANALYST: (1000, 60),  # 1000 requests per minute
        UserRole.AUDITOR: (200, 60),  # 200 requests per minute
        UserRole.ADMIN: (0, 0),  # Unlimited (0 means no limit)
    }

    # ==================== Data Generation Endpoints ====================

    # Data generation (expensive operations)
    GENERATE_DATA_PER_HOUR: Dict[str, Tuple[int, int]] = {
        UserRole.RESEARCHER: (10, 3600),  # 10 generations per hour
        UserRole.DATA_ANALYST: (20, 3600),  # 20 generations per hour
        UserRole.ADMIN: (0, 0),  # Unlimited
    }

    # Bulk data operations
    BULK_IMPORT: Tuple[int, int] = (5, 3600)  # 5 bulk imports per hour
    BULK_EXPORT: Tuple[int, int] = (10, 3600)  # 10 exports per hour

    # ==================== Download Endpoints ====================

    # File downloads
    DOWNLOAD_PER_HOUR: Dict[str, Tuple[int, int]] = {
        UserRole.VIEWER: (10, 3600),  # 10 downloads per hour
        UserRole.RESEARCHER: (50, 3600),  # 50 downloads per hour
        UserRole.DATA_ANALYST: (100, 3600),  # 100 downloads per hour
        UserRole.ADMIN: (0, 0),  # Unlimited
    }

    # ==================== Analytics Endpoints ====================

    # Statistical analysis (compute-intensive)
    ANALYTICS_COMPUTE: Dict[str, Tuple[int, int]] = {
        UserRole.RESEARCHER: (20, 3600),  # 20 analyses per hour
        UserRole.DATA_ANALYST: (50, 3600),  # 50 analyses per hour
        UserRole.ADMIN: (0, 0),  # Unlimited
    }

    # ==================== EDC Endpoints ====================

    # Data entry (per user)
    DATA_ENTRY: Tuple[int, int] = (100, 60)  # 100 entries per minute

    # Query/search operations
    SEARCH_QUERIES: Tuple[int, int] = (30, 60)  # 30 searches per minute

    # ==================== Security-Sensitive Operations ====================

    # PHI decryption (highly sensitive)
    PHI_DECRYPT: Tuple[int, int] = (10, 3600)  # 10 decryptions per hour

    # PHI detection scans
    PHI_DETECTION: Tuple[int, int] = (50, 60)  # 50 scans per minute

    # Audit log access (read-only but sensitive)
    AUDIT_LOG_ACCESS: Tuple[int, int] = (20, 60)  # 20 queries per minute

    # User management operations (admin only)
    USER_MANAGEMENT: Tuple[int, int] = (30, 60)  # 30 operations per minute

    # Permission changes (critical security operation)
    PERMISSION_CHANGES: Tuple[int, int] = (10, 3600)  # 10 changes per hour

    # ==================== Helper Methods ====================

    @classmethod
    def get_api_limit_for_role(cls, role: str) -> Tuple[int, int]:
        """
        Get API rate limit for user role

        Args:
            role: User role string

        Returns:
            (requests, window_seconds) tuple
        """
        role_enum = UserRole(role) if role in [r.value for r in UserRole] else UserRole.ANONYMOUS
        return cls.API_LIMITS_PER_ROLE.get(role_enum, cls.API_LIMITS_PER_ROLE[UserRole.ANONYMOUS])

    @classmethod
    def get_generation_limit_for_role(cls, role: str) -> Tuple[int, int]:
        """Get data generation limit for user role"""
        role_enum = UserRole(role) if role in [r.value for r in UserRole] else UserRole.RESEARCHER
        return cls.GENERATE_DATA_PER_HOUR.get(role_enum, (0, 0))  # Default: no access

    @classmethod
    def get_download_limit_for_role(cls, role: str) -> Tuple[int, int]:
        """Get download limit for user role"""
        role_enum = UserRole(role) if role in [r.value for r in UserRole] else UserRole.VIEWER
        return cls.DOWNLOAD_PER_HOUR.get(role_enum, (10, 3600))  # Default: viewer limits

    @classmethod
    def get_analytics_limit_for_role(cls, role: str) -> Tuple[int, int]:
        """Get analytics limit for user role"""
        role_enum = UserRole(role) if role in [r.value for r in UserRole] else UserRole.RESEARCHER
        return cls.ANALYTICS_COMPUTE.get(role_enum, (0, 0))  # Default: no access

    @classmethod
    def is_rate_limit_enabled(cls) -> bool:
        """Check if rate limiting is globally enabled"""
        return RATE_LIMIT_ENABLED

    @classmethod
    def is_unlimited(cls, limit_tuple: Tuple[int, int]) -> bool:
        """Check if a limit tuple represents unlimited access"""
        return limit_tuple[0] == 0 and limit_tuple[1] == 0


# ==================== Endpoint-Specific Configuration ====================

# Map endpoint paths to rate limit configs
ENDPOINT_RATE_LIMITS: Dict[str, Tuple[int, int]] = {
    # Authentication
    "/auth/login": RateLimitConfig.LOGIN_BY_IP,
    "/auth/register": RateLimitConfig.REGISTER_BY_IP,
    "/auth/refresh": RateLimitConfig.TOKEN_REFRESH,
    "/auth/mfa/verify": RateLimitConfig.MFA_VERIFY,

    # Data entry
    "/vitals": RateLimitConfig.DATA_ENTRY,
    "/subjects": RateLimitConfig.DATA_ENTRY,

    # Downloads
    "/export/csv": (50, 3600),  # 50 CSV exports per hour
    "/export/sdtm": (20, 3600),  # 20 SDTM exports per hour

    # Security-sensitive
    "/encryption/decrypt": RateLimitConfig.PHI_DECRYPT,
    "/phi/detect": RateLimitConfig.PHI_DETECTION,
    "/audit/logs": RateLimitConfig.AUDIT_LOG_ACCESS,

    # Bulk operations
    "/import/synthetic": RateLimitConfig.BULK_IMPORT,
    "/import/bulk": RateLimitConfig.BULK_IMPORT,
}


def get_rate_limit_for_endpoint(endpoint: str, user_role: str = "anonymous") -> Tuple[int, int]:
    """
    Get rate limit configuration for a specific endpoint and user role

    Args:
        endpoint: API endpoint path
        user_role: User's role

    Returns:
        (requests, window_seconds) tuple
    """
    # Check for endpoint-specific limit first
    if endpoint in ENDPOINT_RATE_LIMITS:
        return ENDPOINT_RATE_LIMITS[endpoint]

    # Check for role-specific limits based on endpoint type
    if "/generate/" in endpoint:
        return RateLimitConfig.get_generation_limit_for_role(user_role)
    elif "/stats/" in endpoint or "/analytics/" in endpoint:
        return RateLimitConfig.get_analytics_limit_for_role(user_role)
    elif "/download/" in endpoint or "/export/" in endpoint:
        return RateLimitConfig.get_download_limit_for_role(user_role)

    # Default: use role-based API limit
    return RateLimitConfig.get_api_limit_for_role(user_role)


def get_rate_limit_message(limit: int, window: int) -> str:
    """
    Generate human-readable rate limit message

    Args:
        limit: Number of requests allowed
        window: Time window in seconds

    Returns:
        Formatted string describing the rate limit
    """
    if limit == 0:
        return "No rate limit (unlimited)"

    if window >= 3600:
        hours = window / 3600
        return f"{limit} requests per {hours:.0f} hour{'s' if hours != 1 else ''}"
    elif window >= 60:
        minutes = window / 60
        return f"{limit} requests per {minutes:.0f} minute{'s' if minutes != 1 else ''}"
    else:
        return f"{limit} requests per {window} seconds"
