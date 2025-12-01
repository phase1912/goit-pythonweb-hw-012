"""
Unit tests for UserRepository.
"""
import pytest
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.domain.enums import UserRoles


class TestUserRepository:
    """Test cases for UserRepository."""

    def test_create_user(self, db_session):
        """Test creating a new user."""
        repository = UserRepository(db_session)
        user_data = UserCreate(
            email="newuser@example.com",
            password="password123",
            first_name="New",
            last_name="User"
        )

        user = repository.create(user_data)

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.hashed_password != "password123"  # Should be hashed
        assert user.role == UserRoles.USER  # Default role
        assert user.is_confirmed is False  # Default not confirmed

    def test_get_by_id(self, db_session, test_user):
        """Test retrieving user by ID."""
        repository = UserRepository(db_session)

        user = repository.get_by_id(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_by_id_not_found(self, db_session):
        """Test retrieving non-existent user by ID."""
        repository = UserRepository(db_session)

        user = repository.get_by_id(99999)

        assert user is None

    def test_get_by_email(self, db_session, test_user):
        """Test retrieving user by email."""
        repository = UserRepository(db_session)

        user = repository.get_by_email(test_user.email)

        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    def test_get_by_email_not_found(self, db_session):
        """Test retrieving non-existent user by email."""
        repository = UserRepository(db_session)

        user = repository.get_by_email("nonexistent@example.com")

        assert user is None

    def test_exists_by_email(self, db_session, test_user):
        """Test checking if user exists by email."""
        repository = UserRepository(db_session)

        exists = repository.exists_by_email(test_user.email)

        assert exists is True

    def test_exists_by_email_not_found(self, db_session):
        """Test checking non-existent user by email."""
        repository = UserRepository(db_session)

        exists = repository.exists_by_email("nonexistent@example.com")

        assert exists is False

    def test_update_refresh_token(self, db_session, test_user):
        """Test updating user's refresh token."""
        repository = UserRepository(db_session)
        refresh_token = "new_refresh_token_12345"

        updated_user = repository.update_refresh_token(test_user.id, refresh_token)

        assert updated_user is not None
        assert updated_user.refresh_token == refresh_token

    def test_verify_refresh_token_valid(self, db_session, test_user):
        """Test verifying valid refresh token."""
        repository = UserRepository(db_session)
        refresh_token = "test_refresh_token"
        repository.update_refresh_token(test_user.id, refresh_token)

        is_valid = repository.verify_refresh_token(test_user.email, refresh_token)

        assert is_valid is True

    def test_verify_refresh_token_invalid(self, db_session, test_user):
        """Test verifying invalid refresh token."""
        repository = UserRepository(db_session)
        repository.update_refresh_token(test_user.id, "correct_token")

        is_valid = repository.verify_refresh_token(test_user.email, "wrong_token")

        assert is_valid is False

    def test_verify_refresh_token_no_token(self, db_session, test_user):
        """Test verifying refresh token when user has no token."""
        repository = UserRepository(db_session)

        is_valid = repository.verify_refresh_token(test_user.email, "any_token")

        assert is_valid is False

    def test_verify_refresh_token_user_not_found(self, db_session):
        """Test verifying refresh token for non-existent user."""
        repository = UserRepository(db_session)

        is_valid = repository.verify_refresh_token("nonexistent@example.com", "token")

        assert is_valid is False

    def test_clear_refresh_token(self, db_session, test_user):
        """Test clearing user's refresh token."""
        repository = UserRepository(db_session)
        repository.update_refresh_token(test_user.id, "some_token")

        repository.clear_refresh_token(test_user.id)

        db_session.refresh(test_user)
        assert test_user.refresh_token is None

    def test_confirm_email(self, db_session, test_user):
        """Test confirming user's email."""
        repository = UserRepository(db_session)
        test_user.is_confirmed = False
        db_session.commit()

        confirmed_user = repository.confirm_email(test_user.email)

        assert confirmed_user is not None
        assert confirmed_user.is_confirmed is True

    def test_confirm_email_not_found(self, db_session):
        """Test confirming email for non-existent user."""
        repository = UserRepository(db_session)

        result = repository.confirm_email("nonexistent@example.com")

        assert result is None

    def test_update_avatar(self, db_session, test_user):
        """Test updating user's avatar URL."""
        repository = UserRepository(db_session)
        avatar_url = "https://example.com/avatar.jpg"

        updated_user = repository.update_avatar(test_user.id, avatar_url)

        assert updated_user is not None
        assert updated_user.avatar == avatar_url

    def test_update_avatar_user_not_found(self, db_session):
        """Test updating avatar for non-existent user."""
        repository = UserRepository(db_session)

        result = repository.update_avatar(99999, "https://example.com/avatar.jpg")

        assert result is None

    def test_reset_password(self, db_session, test_user):
        """Test resetting user's password."""
        repository = UserRepository(db_session)
        old_password = test_user.hashed_password
        new_password = "newpassword123"

        updated_user = repository.reset_password(test_user.email, new_password)

        assert updated_user is not None
        assert updated_user.hashed_password != old_password
        assert updated_user.hashed_password != new_password  # Should be hashed
        assert updated_user.refresh_token is None  # Should be cleared

    def test_reset_password_user_not_found(self, db_session):
        """Test resetting password for non-existent user."""
        repository = UserRepository(db_session)

        result = repository.reset_password("nonexistent@example.com", "newpass")

        assert result is None

