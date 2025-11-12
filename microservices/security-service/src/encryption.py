"""
PHI Encryption/Decryption for HIPAA Compliance
Uses Fernet (AES-128 in CBC mode) for authenticated encryption
Note: In production, consider using envelope encryption with AWS KMS, HashiCorp Vault, or Azure Key Vault
"""
from cryptography.fernet import Fernet
import os
import base64
import warnings

# Load encryption key from environment variable
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # In production, this should NEVER happen - fail fast
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise ValueError(
            "CRITICAL: ENCRYPTION_KEY environment variable not set in production! "
            "This is a security risk. Use a key management service (AWS KMS, Vault, etc.)"
        )
    else:
        # Generate a warning in development
        warnings.warn(
            "ENCRYPTION_KEY not set. Generating temporary key for development. "
            "This will NOT work in production!",
            UserWarning
        )
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        
# Validate that default key is not being used in production
DEFAULT_KEY = "your-secret-key-change-in-production"
if ENCRYPTION_KEY == DEFAULT_KEY:
    raise ValueError(
        "CRITICAL: Default encryption key detected! "
        "You MUST set a secure ENCRYPTION_KEY environment variable. "
        "Never use the default key in production."
    )

# Ensure the key is bytes
try:
    key_bytes = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
    # Validate key format (Fernet keys are 44 base64 characters)
    if len(key_bytes) != 44:
        raise ValueError("Invalid Fernet key length. Key must be 44 base64 characters.")
    # Validate key by initializing Fernet
    cipher = Fernet(key_bytes)
except ValueError as e:
    raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")
except Exception as e:
    raise ValueError(f"Failed to initialize encryption: {e}")

def encrypt_phi(data: str) -> str:
    """
    Encrypt Protected Health Information
    
    HIPAA Requirement: Encryption at rest for PHI
    Uses Fernet (symmetric encryption) for simplicity
    In production, consider using envelope encryption with KMS
    """
    if not data:
        return ""
    
    encrypted_bytes = cipher.encrypt(data.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

def decrypt_phi(encrypted_data: str) -> str:
    """
    Decrypt PHI data
    
    HIPAA Requirement: Decryption requires proper authorization
    """
    if not encrypted_data:
        return ""
    
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def generate_encryption_key() -> str:
    """Generate a new encryption key (for key rotation)"""
    return Fernet.generate_key().decode()
