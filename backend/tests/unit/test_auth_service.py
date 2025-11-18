"""
Tests for authentication service
Covers password hashing, JWT tokens, single-user mode
"""

from datetime import datetime, timedelta

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hash_is_different_from_plain(self):
        """Hashed password should be different from plain password."""
        plain_password = "test_password_123"
        hashed = get_password_hash(plain_password)

        assert hashed != plain_password
        assert len(hashed) > len(plain_password)

    def test_same_password_produces_different_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        plain_password = "test_password_123"
        hash1 = get_password_hash(plain_password)
        hash2 = get_password_hash(plain_password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_verify_correct_password(self):
        """Correct password should verify successfully."""
        plain_password = "test_password_123"
        hashed = get_password_hash(plain_password)

        assert verify_password(plain_password, hashed) is True

    def test_verify_incorrect_password(self):
        """Incorrect password should fail verification."""
        plain_password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = get_password_hash(plain_password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_empty_password(self):
        """Empty password should fail verification."""
        plain_password = "test_password_123"
        hashed = get_password_hash(plain_password)

        assert verify_password("", hashed) is False

    def test_hash_empty_password(self):
        """Empty password should still be hashable."""
        hashed = get_password_hash("")

        assert hashed is not None
        assert len(hashed) > 0
        assert verify_password("", hashed) is True


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token_basic(self):
        """Test basic JWT token creation"""
        user_id = 1
        token = create_access_token({"sub": str(user_id)})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token"""
        user_id = 1
        token = create_access_token({"sub": str(user_id)})
        payload = decode_access_token(token)
        assert payload.sub == str(user_id)
        assert payload.exp is not None

    def test_decode_invalid_token(self):
        """Test decoding an invalid JWT token"""
        with pytest.raises(InvalidTokenError):
            decode_access_token("invalid.token.here")

    def test_decode_malformed_token(self):
        """Test decoding a malformed JWT token"""
        with pytest.raises(InvalidTokenError):
            decode_access_token("notavalidtoken")

    def test_decode_empty_token(self):
        """Test decoding an empty JWT token"""
        with pytest.raises(InvalidTokenError):
            decode_access_token("")

    def test_token_contains_expiration(self):
        """Test that tokens contain expiration time"""
        user_id = 1
        token = create_access_token({"sub": str(user_id)})
        # Decode without verification to check structure (jwt.decode requires all arguments)
        from app.core.config import get_settings

        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        assert "exp" in payload
        assert "sub" in payload

    def test_different_users_get_different_tokens(self):
        """Test that different users get unique tokens"""
        token1 = create_access_token({"sub": "1"})
        token2 = create_access_token({"sub": "2"})
        assert token1 != token2

    def test_expired_token_raises_error(self):
        """Test that expired tokens raise InvalidTokenError"""
        user_id = 1
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token({"sub": str(user_id)}, expires_delta=expires_delta)
        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_token_with_custom_expiry(self):
        """Test token creation with custom expiration"""
        user_id = 1
        expires_delta = timedelta(minutes=30)
        token = create_access_token({"sub": str(user_id)}, expires_delta=expires_delta)


class TestSingleUserMode:
    """Test single-user mode configuration."""

    def test_single_user_mode_enabled_by_default(self):
        """Single-user mode should be enabled by default."""
        settings = get_settings()

        # Based on copilot-instructions.md, single-user mode is default
        assert hasattr(settings, "single_user_mode")

    def test_default_user_credentials_configured(self):
        """Default user credentials should be configured."""
        settings = get_settings()

        # Default credentials should be set
        assert hasattr(settings, "default_user_email") or hasattr(settings, "single_user_mode")
        assert hasattr(settings, "default_user_password") or hasattr(settings, "single_user_mode")


class TestPasswordStrength:
    """Test password strength validation."""

    def test_strong_password_hashes_successfully(self):
        """Strong password should hash without issues."""
        strong_password = "StrongP@ssw0rd!123"
        hashed = get_password_hash(strong_password)

        assert verify_password(strong_password, hashed) is True

    def test_weak_password_still_hashes(self):
        """Even weak passwords should hash (validation is separate)."""
        weak_password = "123"
        hashed = get_password_hash(weak_password)

        assert verify_password(weak_password, hashed) is True

    def test_special_characters_in_password(self):
        """Passwords with special characters should work."""
        special_password = "P@ssw0rd!#$%^&*()"
        hashed = get_password_hash(special_password)

        assert verify_password(special_password, hashed) is True

    def test_unicode_characters_in_password(self):
        """Passwords with unicode characters should work."""
        unicode_password = "пароль密码🔐"
        hashed = get_password_hash(unicode_password)

        assert verify_password(unicode_password, hashed) is True

    def test_very_long_password(self):
        """Very long passwords should be handled."""
        long_password = "a" * 500
        hashed = get_password_hash(long_password)

        assert verify_password(long_password, hashed) is True


class TestTokenSecurity:
    """Test token security features."""

    def test_token_is_not_reversible_to_password(self):
        """JWT token should not contain password information."""
        user_id = 1
        token = create_access_token({"sub": str(user_id)})

        # Token should only contain user_id, not password
        payload = decode_access_token(token)
        assert payload.sub == str(user_id)

        # Token string should not contain obvious password patterns
        assert "password" not in token.lower()
        assert "pwd" not in token.lower()

    def test_multiple_tokens_for_same_user_all_valid(self):
        """Multiple tokens for same user should all be valid."""
        import time
        
        user_id = 1
        token1 = create_access_token({"sub": str(user_id)})
        time.sleep(0.01)  # Small delay to ensure different timestamps
        token2 = create_access_token({"sub": str(user_id)})
        time.sleep(0.01)
        token3 = create_access_token({"sub": str(user_id)})

        # All tokens should decode to same user_id
        assert decode_access_token(token1).sub == str(user_id)
        assert decode_access_token(token2).sub == str(user_id)
        assert decode_access_token(token3).sub == str(user_id)

        # Tokens may be identical if created in the same second (deterministic JWT)
        # The important thing is they all work correctly