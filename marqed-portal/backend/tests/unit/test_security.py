"""
Unit tests for security utilities.
"""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing creates a valid hash."""
        password = "secure_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test verifying correct password returns True."""
        password = "my_secret_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password returns False."""
        password = "my_secret_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_same_password_different_hashes(self):
        """Test same password produces different hashes (salted)."""
        password = "test_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        # Both should still verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Tests for JWT token creation."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 50
        assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))

        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 50

    def test_tokens_are_different(self):
        """Test access and refresh tokens are different for same data."""
        data = {"sub": "user123"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        # Different tokens (different timestamps and potentially different secrets)
        assert access_token != refresh_token


class TestPasswordValidation:
    """Tests for password validation rules."""

    def test_empty_password_hash(self):
        """Test hashing empty password (should work, validation elsewhere)."""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True

    def test_unicode_password(self):
        """Test password with unicode characters."""
        password = "пароль_密码_🔐"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_long_password(self):
        """Test password with maximum length (bcrypt has 72 byte limit)."""
        password = "a" * 100  # Over bcrypt limit
        hashed = get_password_hash(password)

        # Note: bcrypt truncates to 72 bytes, so this still works
        assert verify_password(password, hashed) is True
