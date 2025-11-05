"""
Encryption Service for handling data encryption and decryption.
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..core.config import get_settings

class EncryptionService:
    """Service for handling data encryption and decryption."""

    def __init__(self):
        self.settings = get_settings()
        self.key = self._get_key()

    def _get_key(self) -> bytes:
        """Get the encryption key."""
        password = self.settings.encryption_key.encode()
        salt = self.settings.encryption_salt.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        f = Fernet(self.key)
        return f.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        f = Fernet(self.key)
        return f.decrypt(encrypted_data.encode()).decode()

_service = None

def get_encryption_service() -> "EncryptionService":
    """Get the encryption service."""
    global _service
    if _service is None:
        _service = EncryptionService()
    return _service
