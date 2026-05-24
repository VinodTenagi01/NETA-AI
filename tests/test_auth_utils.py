"""
Unit tests for authentication utilities.
"""
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.security_auth.utils import (
    calculate_lock_duration,
    create_access_token,
    create_refresh_token,
    hash_password,
    is_account_locked,
    is_token_expired,
    validate_password_strength,
    verify_password,
    verify_token,
)
from uuid import UUID


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Hashed password should be different from plain
        assert hashed != password
        # Hashed password should be a string
        assert isinstance(hashed, str)
        # Hashed password should be long (bcrypt format)
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test password verification is case sensitive."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password("testpassword123!", hashed) is False

    def test_password_hashing_different_each_time(self):
        """Test same password produces different hashes (bcrypt salt)."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (different salts)
        assert hash1 != hash2
        # But both should verify against same password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordValidation:
    """Tests for password strength validation."""

    def test_validate_password_strong(self):
        """Test validation of strong password."""
        is_valid, error = validate_password_strength("StrongPass123!")
        assert is_valid is True
        assert error is None

    def test_validate_password_too_short(self):
        """Test password too short fails validation."""
        is_valid, error = validate_password_strength("Short1!")
        assert is_valid is False
        assert "8 characters" in error

    def test_validate_password_no_uppercase(self):
        """Test password without uppercase fails validation."""
        is_valid, error = validate_password_strength("nouppercase123!")
        assert is_valid is False
        assert "uppercase" in error

    def test_validate_password_no_lowercase(self):
        """Test password without lowercase fails validation."""
        is_valid, error = validate_password_strength("NOLOWERCASE123!")
        assert is_valid is False
        assert "lowercase" in error

    def test_validate_password_no_digit(self):
        """Test password without digit fails validation."""
        is_valid, error = validate_password_strength("NoDigitPassword!")
        assert is_valid is False
        assert "digit" in error

    def test_validate_password_no_special_char(self):
        """Test password without special character fails validation."""
        is_valid, error = validate_password_strength("NoSpecialChar123")
        assert is_valid is False
        assert "special character" in error

    def test_validate_password_minimum_length(self):
        """Test password at minimum length (8 chars)."""
        is_valid, error = validate_password_strength("Min8Pw1!")
        assert is_valid is True
        assert error is None


class TestJWTTokens:
    """Tests for JWT token generation and validation."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        email = "test@example.com"
        role = "super_admin"

        token = create_access_token(user_id, email, role)

        # Token should be a string
        assert isinstance(token, str)
        # Token should have 3 parts (header.payload.signature)
        assert token.count(".") == 2

    def test_verify_token_valid(self):
        """Test verifying valid token."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        email = "test@example.com"
        role = "campaign_manager"

        token = create_access_token(user_id, email, role)
        token_data = verify_token(token, token_type="access")

        assert token_data.user_id == str(user_id)
        assert token_data.email == email
        assert token_data.role == role
        assert token_data.type == "access"

    def test_verify_token_invalid_signature(self):
        """Test verifying token with invalid signature fails."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        token = create_access_token(user_id, "test@example.com", "super_admin")

        # Tamper with token
        parts = token.split(".")
        tampered_token = parts[0] + ".tampered." + parts[2]

        with pytest.raises(JWTError):
            verify_token(tampered_token, token_type="access")

    def test_verify_token_wrong_type(self):
        """Test verifying token with wrong type fails."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        access_token = create_access_token(user_id, "test@example.com", "super_admin")

        # Try to verify as refresh token
        with pytest.raises(JWTError):
            verify_token(access_token, token_type="refresh")

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        token = create_refresh_token(user_id)

        # Token should be valid and decodable
        assert isinstance(token, str)
        token_data = verify_token(token, token_type="refresh")
        assert token_data.user_id == str(user_id)
        assert token_data.type == "refresh"

    def test_access_token_expiration_default(self):
        """Test access token has default expiration (15 minutes)."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        token = create_access_token(user_id, "test@example.com", "super_admin")
        token_data = verify_token(token)

        # Check expiration is roughly 15 minutes in future
        now = datetime.now(timezone.utc).timestamp()
        exp_time = token_data.exp
        duration = (exp_time - now)

        # Should be approximately 15 minutes (900 seconds), allow 5 second variance
        assert 895 < duration < 905

    def test_refresh_token_expiration_default(self):
        """Test refresh token has default expiration (7 days)."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        token = create_refresh_token(user_id)
        token_data = verify_token(token, token_type="refresh")

        # Check expiration is roughly 7 days in future
        now = datetime.now(timezone.utc).timestamp()
        exp_time = token_data.exp
        duration = (exp_time - now)

        # Should be approximately 7 days (604800 seconds), allow 5 second variance
        expected = 7 * 24 * 60 * 60
        assert (expected - 5) < duration < (expected + 5)

    def test_token_expiration_check(self):
        """Test checking if token is expired."""
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Create fresh token
        fresh_token = create_access_token(user_id, "test@example.com", "super_admin")
        fresh_data = verify_token(fresh_token)
        assert is_token_expired(fresh_data) is False

        # Create expired token (already in past)
        expired_token = create_access_token(
            user_id,
            "test@example.com",
            "super_admin",
            expires_delta=timedelta(seconds=-10),  # Expired 10 seconds ago
        )
        expired_data = verify_token(expired_token)
        assert is_token_expired(expired_data) is True


class TestAccountLocking:
    """Tests for account locking utilities."""

    def test_is_account_locked_none(self):
        """Test account not locked when locked_until is None."""
        assert is_account_locked(None) is False

    def test_is_account_locked_future_time(self):
        """Test account locked when locked_until is in future."""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        assert is_account_locked(future_time) is True

    def test_is_account_locked_past_time(self):
        """Test account not locked when locked_until is in past."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        assert is_account_locked(past_time) is False

    def test_calculate_lock_duration_1_2_attempts(self):
        """Test lock duration for 1-2 failed attempts (5 minutes)."""
        duration1 = calculate_lock_duration(1)
        duration2 = calculate_lock_duration(2)

        assert duration1 == timedelta(minutes=5)
        assert duration2 == timedelta(minutes=5)

    def test_calculate_lock_duration_3_4_attempts(self):
        """Test lock duration for 3-4 failed attempts (15 minutes)."""
        duration3 = calculate_lock_duration(3)
        duration4 = calculate_lock_duration(4)

        assert duration3 == timedelta(minutes=15)
        assert duration4 == timedelta(minutes=15)

    def test_calculate_lock_duration_5_plus_attempts(self):
        """Test lock duration for 5+ failed attempts (1 hour)."""
        duration5 = calculate_lock_duration(5)
        duration10 = calculate_lock_duration(10)

        assert duration5 == timedelta(hours=1)
        assert duration10 == timedelta(hours=1)
