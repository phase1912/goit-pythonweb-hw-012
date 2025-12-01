"""
Unit tests for core security module.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from jose import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_current_user,
    get_current_admin_user,
    require_role
)
from app.core.config import settings
from app.domain.enums import UserRoles


class TestPasswordFunctions:
    """Test cases for password hashing and verification."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"

        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        result = verify_password(wrong_password, hashed)

        assert result is False

    def test_password_hash_unique(self):
        """Test that same password generates different hashes (salt)."""
        password = "testpassword123"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestAccessToken:
    """Test cases for access token creation."""

    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiration."""
        data = {"sub": "user@example.com"}

        token = create_access_token(data)

        assert token is not None
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "user@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "user@example.com"}
        custom_expiry = timedelta(minutes=120)  # 2 hours

        token = create_access_token(data, expires_delta=custom_expiry)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "user@example.com"

        # Check expiry is approximately 120 minutes (2 hours) from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        time_diff = (exp_time - now).total_seconds()
        assert 7100 < time_diff < 17300  # Around 120 minutes (allowing some timing variance)

    def test_access_token_contains_iat(self):
        """Test that access token contains issued at timestamp."""
        data = {"sub": "user@example.com"}

        token = create_access_token(data)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert "iat" in payload
        assert isinstance(payload["iat"], int)


class TestRefreshToken:
    """Test cases for refresh token creation and decoding."""

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "user@example.com"}

        token = create_refresh_token(data)

        assert token is not None
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "user@example.com"
        assert payload["type"] == "refresh"

    def test_decode_refresh_token_valid(self):
        """Test decoding valid refresh token."""
        email = "user@example.com"
        token = create_refresh_token({"sub": email})

        decoded_email = decode_refresh_token(token)

        assert decoded_email == email

    def test_decode_refresh_token_invalid_type(self):
        """Test decoding token with wrong type."""
        token = create_access_token({"sub": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token(token)

        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in exc_info.value.detail

    def test_decode_refresh_token_expired(self):
        """Test decoding expired refresh token."""
        data = {"sub": "user@example.com"}
        expired_delta = timedelta(days=-1)
        token = create_refresh_token(data, expires_delta=expired_delta)

        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_refresh_token_invalid(self):
        """Test decoding invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token("invalid_token")

        assert exc_info.value.status_code == 401


class TestEmailVerificationToken:
    """Test cases for email verification tokens."""

    def test_create_email_verification_token(self):
        """Test creating email verification token."""
        email = "user@example.com"

        token = create_email_verification_token(email)

        assert token is not None
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == email
        assert payload["type"] == "email_verification"

    def test_verify_email_token_valid(self):
        """Test verifying valid email token."""
        email = "user@example.com"
        token = create_email_verification_token(email)

        verified_email = verify_email_token(token)

        assert verified_email == email

    def test_verify_email_token_wrong_type(self):
        """Test verifying token with wrong type."""
        token = create_access_token({"sub": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            verify_email_token(token)

        assert exc_info.value.status_code == 400
        assert "Invalid verification token" in exc_info.value.detail

    def test_verify_email_token_invalid(self):
        """Test verifying invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_email_token("invalid_token")

        assert exc_info.value.status_code == 400


class TestPasswordResetToken:
    """Test cases for password reset tokens."""

    def test_create_password_reset_token(self):
        """Test creating password reset token."""
        email = "user@example.com"

        token = create_password_reset_token(email)

        assert token is not None
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == email
        assert payload["type"] == "password_reset"

    def test_verify_password_reset_token_valid(self):
        """Test verifying valid password reset token."""
        email = "user@example.com"
        token = create_password_reset_token(email)

        verified_email = verify_password_reset_token(token)

        assert verified_email == email

    def test_verify_password_reset_token_wrong_type(self):
        """Test verifying token with wrong type."""
        token = create_access_token({"sub": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            verify_password_reset_token(token)

        assert exc_info.value.status_code == 400
        assert "Invalid password reset token" in exc_info.value.detail

    def test_verify_password_reset_token_expired(self):
        """Test verifying expired password reset token."""
        # Create token that expires in the past
        to_encode = {"sub": "user@example.com", "type": "password_reset"}
        expire = datetime.utcnow() - timedelta(hours=2)
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        with pytest.raises(HTTPException) as exc_info:
            verify_password_reset_token(expired_token)

        assert exc_info.value.status_code == 400


class TestGetCurrentUser:
    """Test cases for get_current_user dependency."""

    @patch('app.core.security.redis_service')
    def test_get_current_user_from_cache(self, mock_redis, db_session, test_user):
        """Test getting user from Redis cache."""
        token = create_access_token({"sub": test_user.email})
        mock_redis.is_token_blacklisted.return_value = False
        mock_redis.get_password_change_timestamp.return_value = None
        mock_redis.get_user.return_value = test_user

        user = get_current_user(token, db_session)

        assert user.email == test_user.email
        mock_redis.get_user.assert_called_once_with(test_user.email)

    @patch('app.core.security.redis_service')
    def test_get_current_user_from_database(self, mock_redis, db_session, test_user):
        """Test getting user from database when not in cache."""
        token = create_access_token({"sub": test_user.email})
        mock_redis.is_token_blacklisted.return_value = False
        mock_redis.get_password_change_timestamp.return_value = None
        mock_redis.get_user.return_value = None

        user = get_current_user(token, db_session)

        assert user.email == test_user.email
        mock_redis.set_user.assert_called_once()

    @patch('app.core.security.redis_service')
    def test_get_current_user_blacklisted_token(self, mock_redis, db_session):
        """Test that blacklisted token raises exception."""
        token = create_access_token({"sub": "user@example.com"})
        mock_redis.is_token_blacklisted.return_value = True

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token, db_session)

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail

    @patch('app.core.security.redis_service')
    def test_get_current_user_invalid_token(self, mock_redis, db_session):
        """Test that invalid token raises exception."""
        mock_redis.is_token_blacklisted.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            get_current_user("invalid_token", db_session)

        assert exc_info.value.status_code == 401

    @patch('app.core.security.redis_service')
    def test_get_current_user_not_found(self, mock_redis, db_session):
        """Test that non-existent user raises exception."""
        token = create_access_token({"sub": "nonexistent@example.com"})
        mock_redis.is_token_blacklisted.return_value = False
        mock_redis.get_password_change_timestamp.return_value = None
        mock_redis.get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token, db_session)

        assert exc_info.value.status_code == 401

    @patch('app.core.security.redis_service')
    def test_get_current_user_password_changed(self, mock_redis, db_session, test_user):
        """Test that token issued before password change is rejected."""
        # Create token with specific iat
        now = datetime.utcnow()
        token_data = {"sub": test_user.email}
        to_encode = token_data.copy()
        to_encode.update({
            "exp": now + timedelta(minutes=30),
            "iat": int((now - timedelta(hours=1)).timestamp()),  # Token from 1 hour ago
            "type": "access"
        })
        token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        # Password changed 30 minutes ago (after token was issued)
        password_changed = (now - timedelta(minutes=30)).isoformat()

        mock_redis.is_token_blacklisted.return_value = False
        mock_redis.get_password_change_timestamp.return_value = password_changed
        mock_redis.get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token, db_session)

        assert exc_info.value.status_code == 401
        assert "password change" in exc_info.value.detail.lower()


class TestGetCurrentAdminUser:
    """Test cases for get_current_admin_user dependency."""

    def test_get_current_admin_user_success(self, test_admin):
        """Test getting admin user when user is admin."""
        admin_user = get_current_admin_user(test_admin)

        assert admin_user.role == UserRoles.ADMIN

    def test_get_current_admin_user_not_admin(self, test_user):
        """Test that non-admin user is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_admin_user(test_user)

        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail


class TestRequireRole:
    """Test cases for require_role dependency factory."""

    def test_require_role_correct_role(self, test_user):
        """Test that user with correct role is allowed."""
        role_checker = require_role(UserRoles.USER)

        user = role_checker(test_user)

        assert user.email == test_user.email

    def test_require_role_incorrect_role(self, test_user):
        """Test that user with incorrect role is rejected."""
        role_checker = require_role(UserRoles.ADMIN)

        with pytest.raises(HTTPException) as exc_info:
            role_checker(test_user)

        assert exc_info.value.status_code == 403
        assert "ADMIN" in exc_info.value.detail

    def test_require_role_admin_success(self, test_admin):
        """Test that admin role check works."""
        role_checker = require_role(UserRoles.ADMIN)

        user = role_checker(test_admin)

        assert user.role == UserRoles.ADMIN

