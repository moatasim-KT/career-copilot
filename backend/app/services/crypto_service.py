"""
Cryptographic service for data encryption and decryption
"""

import os
import base64
import hashlib
from typing import Union, Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json

from app.core.config import settings


class CryptoService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self._fernet_key = None
        self._aes_key = None
        self._salt = None
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize encryption keys from configuration"""
        # Get encryption key from environment or generate one
        encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
        
        if not encryption_key:
            # Generate a new key if none exists (for development)
            encryption_key = Fernet.generate_key().decode()
            print(f"Generated new encryption key: {encryption_key}")
            print("Please set ENCRYPTION_KEY in your environment variables")
        
        # Create Fernet cipher for symmetric encryption
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self._fernet_key = Fernet(encryption_key)
        
        # Create AES key for file encryption
        self._salt = getattr(settings, 'ENCRYPTION_SALT', b'career_copilot_salt')
        if isinstance(self._salt, str):
            self._salt = self._salt.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
            backend=default_backend()
        )
        self._aes_key = kdf.derive(encryption_key)
    
    def encrypt_text(self, plaintext: str) -> str:
        """Encrypt text data using Fernet (symmetric encryption)"""
        if not plaintext:
            return plaintext
        
        try:
            encrypted_data = self._fernet_key.encrypt(plaintext.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt text: {str(e)}")
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt text data using Fernet"""
        if not encrypted_text:
            return encrypted_text
        
        try:
            encrypted_data = base64.b64decode(encrypted_text.encode())
            decrypted_data = self._fernet_key.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt text: {str(e)}")
    
    def encrypt_json(self, data: Dict[Any, Any]) -> str:
        """Encrypt JSON data"""
        if not data:
            return ""
        
        try:
            json_string = json.dumps(data, sort_keys=True)
            return self.encrypt_text(json_string)
        except Exception as e:
            raise ValueError(f"Failed to encrypt JSON: {str(e)}")
    
    def decrypt_json(self, encrypted_json: str) -> Dict[Any, Any]:
        """Decrypt JSON data"""
        if not encrypted_json:
            return {}
        
        try:
            json_string = self.decrypt_text(encrypted_json)
            return json.loads(json_string)
        except Exception as e:
            raise ValueError(f"Failed to decrypt JSON: {str(e)}")
    
    def encrypt_file(self, file_data: bytes) -> bytes:
        """Encrypt file data using AES encryption"""
        if not file_data:
            return file_data
        
        try:
            # Generate a random IV for each file
            iv = os.urandom(16)
            
            # Create AES cipher
            cipher = Cipher(
                algorithms.AES(self._aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad data to be multiple of 16 bytes
            padding_length = 16 - (len(file_data) % 16)
            padded_data = file_data + bytes([padding_length] * padding_length)
            
            # Encrypt data
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Prepend IV to encrypted data
            return iv + encrypted_data
        except Exception as e:
            raise ValueError(f"Failed to encrypt file: {str(e)}")
    
    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """Decrypt file data using AES encryption"""
        if not encrypted_data or len(encrypted_data) < 16:
            return encrypted_data
        
        try:
            # Extract IV from the beginning
            iv = encrypted_data[:16]
            encrypted_file_data = encrypted_data[16:]
            
            # Create AES cipher
            cipher = Cipher(
                algorithms.AES(self._aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt data
            padded_data = decryptor.update(encrypted_file_data) + decryptor.finalize()
            
            # Remove padding
            padding_length = padded_data[-1]
            return padded_data[:-padding_length]
        except Exception as e:
            raise ValueError(f"Failed to decrypt file: {str(e)}")
    
    def hash_data(self, data: str) -> str:
        """Create a hash of data for integrity checking"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_hash(self, data: str, expected_hash: str) -> bool:
        """Verify data integrity using hash"""
        return self.hash_data(data) == expected_hash
    
    def encrypt_user_profile(self, profile_data: Dict[Any, Any]) -> str:
        """Encrypt user profile data"""
        # Only encrypt sensitive fields
        sensitive_fields = ['email', 'phone', 'address', 'ssn', 'personal_notes']
        
        encrypted_profile = profile_data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_profile and encrypted_profile[field]:
                encrypted_profile[field] = self.encrypt_text(str(encrypted_profile[field]))
        
        return json.dumps(encrypted_profile)
    
    def decrypt_user_profile(self, encrypted_profile: str) -> Dict[Any, Any]:
        """Decrypt user profile data"""
        if not encrypted_profile:
            return {}
        
        try:
            profile_data = json.loads(encrypted_profile)
            sensitive_fields = ['email', 'phone', 'address', 'ssn', 'personal_notes']
            
            for field in sensitive_fields:
                if field in profile_data and profile_data[field]:
                    try:
                        profile_data[field] = self.decrypt_text(profile_data[field])
                    except ValueError:
                        # Field might not be encrypted (backward compatibility)
                        pass
            
            return profile_data
        except Exception as e:
            raise ValueError(f"Failed to decrypt user profile: {str(e)}")
    
    def is_encrypted(self, data: str) -> bool:
        """Check if data appears to be encrypted"""
        try:
            # Try to decode as base64 - encrypted data should be base64 encoded
            base64.b64decode(data)
            # If it decodes successfully and looks like encrypted data, it probably is
            return len(data) > 50 and data.isalnum() or '+' in data or '/' in data or '=' in data
        except Exception:
            return False


# Global crypto service instance
crypto_service = CryptoService()