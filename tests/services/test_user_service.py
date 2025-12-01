"""
Unit tests for UserService.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService, UserAlreadyExistsError
from app.schemas.user import UserCreate
from app.domain.enums import UserRoles


class TestUserService:
    """Test cases for UserService."""

    def test_create_user_success(self, db_session):
        """Test successfully creating a new user."""
        service = UserService(db_session)
        user_data = UserCreate(
            email="newuser@example.com",
            password="password123",
            first_name="New",
            last_name="User"
        )

        user = service.create_user(user_data)

        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.role == UserRoles.USER
        assert user.is_confirmed is False

    def test_create_user_duplicate_email(self, db_session, test_user):
        """Test creating user with duplicate email raises error."""
        service = UserService(db_session)
        user_data = UserCreate(
            email=test_user.email,  # Duplicate
            password="password123"
        )

        with pytest.raises(UserAlreadyExistsError):
            service.create_user(user_data)

    def test_get_user_by_email(self, db_session, test_user):
        """Test retrieving user by email."""
        service = UserService(db_session)

        user = service.get_user_by_email(test_user.email)

        assert user is not None
        assert user.email == test_user.email

    def test_get_user_by_email_not_found(self, db_session):
        """Test retrieving non-existent user by email."""
        service = UserService(db_session)

        user = service.get_user_by_email("nonexistent@example.com")

        assert user is None

    def test_authenticate_user_success(self, db_session, test_user):
        """Test successfully authenticating a user."""
        service = UserService(db_session)

        user = service.authenticate_user(test_user.email, "testpassword123")

        assert user is not None
        assert user.email == test_user.email

    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Test authenticating with wrong password."""
        service = UserService(db_session)

        user = service.authenticate_user(test_user.email, "wrongpassword")

        assert user is None

    def test_authenticate_user_not_found(self, db_session):
        """Test authenticating non-existent user."""
        service = UserService(db_session)

        user = service.authenticate_user("nonexistent@example.com", "password")

        assert user is None

    def test_save_refresh_token(self, db_session, test_user):
        """Test saving user's refresh token."""
        service = UserService(db_session)
        token = "new_refresh_token_12345"

        updated_user = service.save_refresh_token(test_user.id, token)

        assert updated_user is not None
        assert updated_user.refresh_token == token

    def test_verify_refresh_token_valid(self, db_session, test_user):
        """Test verifying valid refresh token."""
        service = UserService(db_session)
        token = "valid_token"
        service.save_refresh_token(test_user.id, token)

        is_valid = service.verify_refresh_token(test_user.email, token)

        assert is_valid is True

    def test_verify_refresh_token_invalid(self, db_session, test_user):
        """Test verifying invalid refresh token."""
        service = UserService(db_session)
        service.save_refresh_token(test_user.id, "correct_token")

        is_valid = service.verify_refresh_token(test_user.email, "wrong_token")

        assert is_valid is False

    def test_revoke_refresh_token(self, db_session, test_user):
        """Test revoking user's refresh token."""
        service = UserService(db_session)
        service.save_refresh_token(test_user.id, "some_token")

        service.revoke_refresh_token(test_user.id)

        db_session.refresh(test_user)
        assert test_user.refresh_token is None

    def test_confirm_email(self, db_session, test_user):
        """Test confirming user's email."""
        service = UserService(db_session)
        test_user.is_confirmed = False
        db_session.commit()

        confirmed_user = service.confirm_email(test_user.email)

        assert confirmed_user is not None
        assert confirmed_user.is_confirmed is True

    def test_confirm_email_not_found(self, db_session):
        """Test confirming email for non-existent user."""
        service = UserService(db_session)

        result = service.confirm_email("nonexistent@example.com")

        assert result is None

    def test_update_avatar(self, db_session, test_user):
        """Test updating user's avatar URL."""
        service = UserService(db_session)
        avatar_url = "https://example.com/avatar.jpg"

        updated_user = service.update_avatar(test_user.id, avatar_url)

        assert updated_user is not None
        assert updated_user.avatar == avatar_url

    def test_update_avatar_not_found(self, db_session):
        """Test updating avatar for non-existent user."""
        service = UserService(db_session)

        result = service.update_avatar(99999, "https://example.com/avatar.jpg")

        assert result is None

    def test_reset_password(self, db_session, test_user):
        """Test resetting user's password."""
        service = UserService(db_session)
        old_password = test_user.hashed_password

        updated_user = service.reset_password(test_user.email, "newpassword123")

        assert updated_user is not None
        assert updated_user.hashed_password != old_password
        assert updated_user.refresh_token is None

    def test_reset_password_not_found(self, db_session):
        """Test resetting password for non-existent user."""
        service = UserService(db_session)

        result = service.reset_password("nonexistent@example.com", "newpass")

        assert result is None

