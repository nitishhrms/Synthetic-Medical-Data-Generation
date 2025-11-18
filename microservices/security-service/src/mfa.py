"""
Multi-Factor Authentication (MFA) using TOTP
Time-based One-Time Password (TOTP) implementation with QR code generation
"""
import pyotp
import qrcode
import io
import base64
import os
import secrets
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from redis_client import security_redis
from encryption import encrypt_phi, decrypt_phi

logger = logging.getLogger(__name__)

# MFA Configuration
MFA_ISSUER_NAME = os.getenv("MFA_ISSUER_NAME", "Synthetic Medical Data Platform")
TOTP_INTERVAL = 30  # 30-second time window
TOTP_DIGITS = 6  # 6-digit codes
BACKUP_CODES_COUNT = 10  # Number of backup codes to generate


class MFAManager:
    """
    Multi-Factor Authentication Manager

    Features:
    - TOTP (Time-based One-Time Password) generation
    - QR code generation for authenticator apps
    - Backup codes for account recovery
    - Encrypted secret storage
    - Rate limiting for verification attempts
    """

    def __init__(self):
        self.redis = security_redis
        self.issuer_name = MFA_ISSUER_NAME

    # ==================== MFA Setup ====================

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret

        Returns:
            Base32-encoded secret string
        """
        return pyotp.random_base32()

    def generate_provisioning_uri(self, username: str, secret: str) -> str:
        """
        Generate provisioning URI for authenticator apps

        Args:
            username: User's username or email
            secret: TOTP secret

        Returns:
            otpauth:// URI for QR code
        """
        totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
        return totp.provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )

    def generate_qr_code(self, provisioning_uri: str) -> str:
        """
        Generate QR code image from provisioning URI

        Args:
            provisioning_uri: otpauth:// URI

        Returns:
            Base64-encoded PNG image
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise

    def generate_backup_codes(self, count: int = BACKUP_CODES_COUNT) -> List[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes (8 characters each, alphanumeric)
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes

    async def setup_mfa(self, user_id: str, username: str) -> dict:
        """
        Initialize MFA setup for user

        Args:
            user_id: User identifier
            username: Username for QR code label

        Returns:
            Dictionary with secret, QR code, and backup codes
        """
        try:
            # Generate secret
            secret = self.generate_secret()

            # Store secret temporarily in Redis (10 min expiry) until user confirms
            await self.redis.store_mfa_setup_secret(user_id, secret, ttl=600)

            # Generate provisioning URI
            provisioning_uri = self.generate_provisioning_uri(username, secret)

            # Generate QR code
            qr_code = self.generate_qr_code(provisioning_uri)

            # Generate backup codes
            backup_codes = self.generate_backup_codes()

            logger.info(f"MFA setup initiated for user {user_id}")

            return {
                "secret": secret,  # Show once for manual entry
                "qr_code": qr_code,
                "provisioning_uri": provisioning_uri,
                "backup_codes": backup_codes,
                "issuer": self.issuer_name,
                "interval": TOTP_INTERVAL,
                "digits": TOTP_DIGITS
            }

        except Exception as e:
            logger.error(f"MFA setup failed for user {user_id}: {e}")
            raise

    async def confirm_mfa_setup(
        self,
        user_id: str,
        verification_code: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Confirm MFA setup by verifying a code

        Args:
            user_id: User identifier
            verification_code: 6-digit TOTP code from authenticator

        Returns:
            (success, encrypted_secret) tuple
        """
        try:
            # Get temporary secret from Redis
            secret = await self.redis.get_mfa_setup_secret(user_id)

            if not secret:
                return False, None

            # Verify the code
            totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
            is_valid = totp.verify(verification_code, valid_window=1)

            if is_valid:
                # Encrypt secret for database storage
                encrypted_secret = encrypt_phi(secret)

                # Delete temporary secret from Redis
                await self.redis.delete_mfa_setup_secret(user_id)

                logger.info(f"MFA setup confirmed for user {user_id}")
                return True, encrypted_secret
            else:
                logger.warning(f"Invalid MFA verification code for user {user_id} during setup")
                return False, None

        except Exception as e:
            logger.error(f"MFA confirmation failed for user {user_id}: {e}")
            return False, None

    # ==================== MFA Verification ====================

    def verify_totp(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP code

        Args:
            secret: User's TOTP secret (decrypted)
            code: 6-digit code from authenticator
            valid_window: Number of time windows to check (1 = ±30 seconds)

        Returns:
            True if code is valid
        """
        try:
            totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
            return totp.verify(code, valid_window=valid_window)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False

    def verify_backup_code(
        self,
        code: str,
        backup_codes_encrypted: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code and invalidate it

        Args:
            code: Backup code to verify
            backup_codes_encrypted: Encrypted JSON string of remaining backup codes

        Returns:
            (is_valid, updated_backup_codes_encrypted) tuple
        """
        try:
            # Decrypt backup codes
            import json
            backup_codes_json = decrypt_phi(backup_codes_encrypted)
            backup_codes = json.loads(backup_codes_json)

            # Normalize code (remove spaces, hyphens, convert to uppercase)
            normalized_code = code.replace(' ', '').replace('-', '').upper()

            # Check if code exists
            for stored_code in backup_codes:
                normalized_stored = stored_code.replace(' ', '').replace('-', '').upper()
                if normalized_code == normalized_stored:
                    # Remove used code
                    backup_codes.remove(stored_code)

                    # Re-encrypt updated list
                    updated_json = json.dumps(backup_codes)
                    updated_encrypted = encrypt_phi(updated_json)

                    logger.info(f"Backup code used successfully. {len(backup_codes)} codes remaining.")
                    return True, updated_encrypted

            logger.warning("Invalid backup code provided")
            return False, None

        except Exception as e:
            logger.error(f"Backup code verification error: {e}")
            return False, None

    async def verify_mfa_with_rate_limit(
        self,
        user_id: str,
        code: str,
        encrypted_secret: str
    ) -> Tuple[bool, str]:
        """
        Verify MFA code with rate limiting

        Args:
            user_id: User identifier
            code: MFA code to verify
            encrypted_secret: User's encrypted TOTP secret

        Returns:
            (is_valid, message) tuple
        """
        try:
            # Check rate limit (5 attempts per 5 minutes)
            allowed, count, retry_after, _ = await self.redis.check_rate_limit(
                f"mfa_verify:{user_id}",
                limit=5,
                window_seconds=300
            )

            if not allowed:
                return False, f"Too many MFA verification attempts. Try again in {retry_after} seconds."

            # Decrypt secret
            secret = decrypt_phi(encrypted_secret)

            # Verify TOTP
            is_valid = self.verify_totp(secret, code)

            if is_valid:
                logger.info(f"MFA verification successful for user {user_id}")
                # Reset rate limit counter on successful verification
                await self.redis.reset_rate_limit(f"mfa_verify:{user_id}")
                return True, "MFA verification successful"
            else:
                logger.warning(f"Invalid MFA code for user {user_id}. Attempt {count}/5")
                return False, f"Invalid MFA code. {5 - count} attempts remaining."

        except Exception as e:
            logger.error(f"MFA verification error for user {user_id}: {e}")
            return False, "MFA verification failed due to server error"

    # ==================== MFA Management ====================

    def encrypt_backup_codes(self, backup_codes: List[str]) -> str:
        """
        Encrypt backup codes for database storage

        Args:
            backup_codes: List of backup codes

        Returns:
            Encrypted JSON string
        """
        import json
        backup_codes_json = json.dumps(backup_codes)
        return encrypt_phi(backup_codes_json)

    def decrypt_backup_codes(self, encrypted_backup_codes: str) -> List[str]:
        """
        Decrypt backup codes from database

        Args:
            encrypted_backup_codes: Encrypted JSON string

        Returns:
            List of backup codes
        """
        import json
        backup_codes_json = decrypt_phi(encrypted_backup_codes)
        return json.loads(backup_codes_json)

    async def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """
        Generate new backup codes (invalidate old ones)

        Args:
            user_id: User identifier

        Returns:
            New list of backup codes
        """
        backup_codes = self.generate_backup_codes()
        logger.info(f"Backup codes regenerated for user {user_id}")
        return backup_codes

    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for user (admin action or user request)

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        logger.warning(f"MFA disabled for user {user_id}")
        return True

    # ==================== Helper Methods ====================

    def get_current_totp(self, secret: str) -> str:
        """
        Get current TOTP code (for testing/debugging only)

        Args:
            secret: TOTP secret

        Returns:
            Current 6-digit code
        """
        totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
        return totp.now()

    def get_remaining_time(self) -> int:
        """
        Get seconds remaining in current time window

        Returns:
            Seconds until next code
        """
        import time
        return TOTP_INTERVAL - int(time.time()) % TOTP_INTERVAL

    def get_mfa_stats(self, user_id: Optional[str] = None) -> dict:
        """
        Get MFA statistics

        Returns:
            Dictionary with MFA configuration info
        """
        stats = {
            "issuer": self.issuer_name,
            "totp_interval": TOTP_INTERVAL,
            "totp_digits": TOTP_DIGITS,
            "backup_codes_count": BACKUP_CODES_COUNT
        }

        if user_id:
            stats["user_id"] = user_id
            stats["remaining_time_window"] = self.get_remaining_time()

        return stats


# Global instance
mfa_manager = MFAManager()
