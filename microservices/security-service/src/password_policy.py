"""
Password Policy Enforcement for HIPAA/SOC 2 Compliance

Implements strong password requirements:
- Minimum 12 characters
- Uppercase, lowercase, numbers, special characters
- Password history (prevent reuse)
- Password strength scoring
- Common password detection
"""
import re
import hashlib
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Password policy configuration
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGITS = True
REQUIRE_SPECIAL = True
PASSWORD_HISTORY_COUNT = 5  # Don't reuse last 5 passwords
PASSWORD_EXPIRY_DAYS = 90  # Force password change after 90 days

# Common weak passwords (subset - in production, use a larger list)
COMMON_PASSWORDS = {
    "password123",
    "Password123",
    "password123!",
    "Password123!",
    "Welcome123",
    "Welcome123!",
    "Admin123!",
    "Passw0rd!",
    "P@ssw0rd",
    "P@ssword123",
    "1qaz2wsx",
    "Qwerty123!",
    "Aa123456!",
    "letmein123",
    "changeme123",
}

# Special characters allowed
SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"


class PasswordStrengthResult:
    """Result of password strength check"""

    def __init__(self):
        self.valid = False
        self.score = 0  # 0-100
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.feedback: List[str] = []

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "valid": self.valid,
            "score": self.score,
            "strength": self.get_strength_label(),
            "errors": self.errors,
            "warnings": self.warnings,
            "feedback": self.feedback
        }

    def get_strength_label(self) -> str:
        """Get human-readable strength label"""
        if self.score >= 80:
            return "strong"
        elif self.score >= 60:
            return "good"
        elif self.score >= 40:
            return "fair"
        else:
            return "weak"


def validate_password_policy(password: str) -> PasswordStrengthResult:
    """
    Validate password against policy requirements

    Args:
        password: Password to validate

    Returns:
        PasswordStrengthResult with validation details
    """
    result = PasswordStrengthResult()
    score = 0

    # Check length
    if len(password) < MIN_PASSWORD_LENGTH:
        result.errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    elif len(password) > MAX_PASSWORD_LENGTH:
        result.errors.append(f"Password must not exceed {MAX_PASSWORD_LENGTH} characters")
    else:
        score += 20
        if len(password) >= 16:
            score += 10
            result.feedback.append("Good length (16+ characters)")

    # Check uppercase
    if REQUIRE_UPPERCASE:
        if not re.search(r'[A-Z]', password):
            result.errors.append("Password must contain at least one uppercase letter")
        else:
            score += 15
            uppercase_count = len(re.findall(r'[A-Z]', password))
            if uppercase_count >= 2:
                score += 5

    # Check lowercase
    if REQUIRE_LOWERCASE:
        if not re.search(r'[a-z]', password):
            result.errors.append("Password must contain at least one lowercase letter")
        else:
            score += 15
            lowercase_count = len(re.findall(r'[a-z]', password))
            if lowercase_count >= 2:
                score += 5

    # Check digits
    if REQUIRE_DIGITS:
        if not re.search(r'\d', password):
            result.errors.append("Password must contain at least one number")
        else:
            score += 15
            digit_count = len(re.findall(r'\d', password))
            if digit_count >= 2:
                score += 5

    # Check special characters
    if REQUIRE_SPECIAL:
        if not re.search(f'[{re.escape(SPECIAL_CHARACTERS)}]', password):
            result.errors.append(f"Password must contain at least one special character ({SPECIAL_CHARACTERS})")
        else:
            score += 15
            special_count = len(re.findall(f'[{re.escape(SPECIAL_CHARACTERS)}]', password))
            if special_count >= 2:
                score += 5
                result.feedback.append("Good use of special characters")

    # Check for common/weak passwords
    if password.lower() in {p.lower() for p in COMMON_PASSWORDS}:
        result.errors.append("Password is too common and easily guessable")
        score = min(score, 30)  # Cap score at 30 for common passwords
    elif password in COMMON_PASSWORDS:
        result.errors.append("Password is too common")
        score = min(score, 40)

    # Check for sequential characters
    if has_sequential_characters(password):
        result.warnings.append("Password contains sequential characters (e.g., 'abc', '123')")
        score -= 10

    # Check for repeated characters
    if has_repeated_characters(password):
        result.warnings.append("Password contains repeated characters (e.g., 'aaa', '111')")
        score -= 10

    # Check character diversity
    unique_chars = len(set(password))
    diversity_ratio = unique_chars / len(password) if len(password) > 0 else 0
    if diversity_ratio >= 0.7:
        score += 10
        result.feedback.append("Good character diversity")
    elif diversity_ratio < 0.5:
        result.warnings.append("Low character diversity - consider using more unique characters")

    # Final score adjustment
    score = max(0, min(100, score))
    result.score = score

    # Set validity
    result.valid = len(result.errors) == 0 and score >= 60

    # Add overall feedback
    if result.valid:
        if score >= 80:
            result.feedback.append("Excellent password strength!")
        elif score >= 60:
            result.feedback.append("Good password strength")
    else:
        result.feedback.append("Password does not meet security requirements")

    return result


def has_sequential_characters(password: str, min_length: int = 3) -> bool:
    """Check for sequential characters like 'abc' or '123'"""
    for i in range(len(password) - min_length + 1):
        substr = password[i:i + min_length]
        if substr.isalpha():
            # Check alphabetical sequence
            if all(ord(substr[j]) == ord(substr[j - 1]) + 1 for j in range(1, len(substr))):
                return True
            # Check reverse alphabetical sequence
            if all(ord(substr[j]) == ord(substr[j - 1]) - 1 for j in range(1, len(substr))):
                return True
        elif substr.isdigit():
            # Check numerical sequence
            if all(int(substr[j]) == int(substr[j - 1]) + 1 for j in range(1, len(substr))):
                return True
            # Check reverse numerical sequence
            if all(int(substr[j]) == int(substr[j - 1]) - 1 for j in range(1, len(substr))):
                return True
    return False


def has_repeated_characters(password: str, min_repeats: int = 3) -> bool:
    """Check for repeated characters like 'aaa' or '111'"""
    for i in range(len(password) - min_repeats + 1):
        if len(set(password[i:i + min_repeats])) == 1:
            return True
    return False


def hash_password_for_history(password: str) -> str:
    """
    Hash password for storage in password history

    Uses SHA-256 (not bcrypt) since we only need to check equality,
    not verify against user-provided passwords
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_password_history(
    new_password: str,
    password_history: List[str],
    max_history: int = PASSWORD_HISTORY_COUNT
) -> Tuple[bool, str]:
    """
    Check if password has been used recently

    Args:
        new_password: New password to check
        password_history: List of hashed previous passwords
        max_history: Number of previous passwords to check

    Returns:
        (is_allowed, message) tuple
    """
    if not password_history:
        return True, "OK"

    new_password_hash = hash_password_for_history(new_password)

    # Check against recent password history
    recent_history = password_history[-max_history:] if len(password_history) > max_history else password_history

    if new_password_hash in recent_history:
        return False, f"Password has been used recently. Cannot reuse last {max_history} passwords."

    return True, "OK"


def is_password_expired(last_changed: datetime, expiry_days: int = PASSWORD_EXPIRY_DAYS) -> Tuple[bool, int]:
    """
    Check if password has expired

    Args:
        last_changed: When password was last changed
        expiry_days: Number of days until expiry

    Returns:
        (is_expired, days_until_expiry) tuple
    """
    if not last_changed:
        return False, expiry_days

    expiry_date = last_changed + timedelta(days=expiry_days)
    now = datetime.utcnow()

    if now >= expiry_date:
        days_overdue = (now - expiry_date).days
        return True, -days_overdue

    days_remaining = (expiry_date - now).days
    return False, days_remaining


def generate_password_strength_feedback(password: str) -> dict:
    """
    Generate detailed feedback for password strength

    Useful for password strength meters in UI

    Returns:
        Dictionary with detailed feedback
    """
    result = validate_password_policy(password)

    return {
        "valid": result.valid,
        "score": result.score,
        "strength": result.get_strength_label(),
        "requirements": {
            "min_length": {
                "required": MIN_PASSWORD_LENGTH,
                "current": len(password),
                "met": len(password) >= MIN_PASSWORD_LENGTH
            },
            "uppercase": {
                "required": REQUIRE_UPPERCASE,
                "current": len(re.findall(r'[A-Z]', password)),
                "met": bool(re.search(r'[A-Z]', password)) if REQUIRE_UPPERCASE else True
            },
            "lowercase": {
                "required": REQUIRE_LOWERCASE,
                "current": len(re.findall(r'[a-z]', password)),
                "met": bool(re.search(r'[a-z]', password)) if REQUIRE_LOWERCASE else True
            },
            "digits": {
                "required": REQUIRE_DIGITS,
                "current": len(re.findall(r'\d', password)),
                "met": bool(re.search(r'\d', password)) if REQUIRE_DIGITS else True
            },
            "special": {
                "required": REQUIRE_SPECIAL,
                "current": len(re.findall(f'[{re.escape(SPECIAL_CHARACTERS)}]', password)),
                "met": bool(re.search(f'[{re.escape(SPECIAL_CHARACTERS)}]', password)) if REQUIRE_SPECIAL else True
            }
        },
        "errors": result.errors,
        "warnings": result.warnings,
        "feedback": result.feedback
    }


def get_password_policy_description() -> dict:
    """
    Get password policy requirements for display to users

    Returns:
        Dictionary describing password policy
    """
    return {
        "min_length": MIN_PASSWORD_LENGTH,
        "max_length": MAX_PASSWORD_LENGTH,
        "requires_uppercase": REQUIRE_UPPERCASE,
        "requires_lowercase": REQUIRE_LOWERCASE,
        "requires_digits": REQUIRE_DIGITS,
        "requires_special": REQUIRE_SPECIAL,
        "special_characters_allowed": SPECIAL_CHARACTERS,
        "password_history_count": PASSWORD_HISTORY_COUNT,
        "password_expiry_days": PASSWORD_EXPIRY_DAYS,
        "description": (
            f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters long and contain "
            f"at least one uppercase letter, one lowercase letter, one number, and one special character "
            f"({SPECIAL_CHARACTERS}). Cannot reuse last {PASSWORD_HISTORY_COUNT} passwords. "
            f"Passwords expire after {PASSWORD_EXPIRY_DAYS} days."
        )
    }
