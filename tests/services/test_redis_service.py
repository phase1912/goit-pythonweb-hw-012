"""
Unit tests for RedisService.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from app.services.redis_service import RedisService
from app.domain.user import User


class TestRedisService:
    """Test cases for RedisService."""

    @patch('app.services.redis_service.redis.from_url')
    def test_init_success(self, mock_redis):
        """Test successful Redis initialization."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        service = RedisService()

        assert service.redis_client is not None
        mock_client.ping.assert_called_once()

    @patch('app.services.redis_service.redis.from_url')
    def test_init_connection_error(self, mock_redis):
        """Test Redis initialization with connection error."""
        mock_redis.side_effect = Exception("Connection failed")

        service = RedisService()

        assert service.redis_client is None

    def test_is_available_true(self):
        """Test Redis availability check when available."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.ping.return_value = True

        assert service._is_available() is True

    def test_is_available_false_no_client(self):
        """Test Redis availability check when client is None."""
        service = RedisService()
        service.redis_client = None

        assert service._is_available() is False

    def test_is_available_false_ping_fails(self):
        """Test Redis availability check when ping fails."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.ping.side_effect = Exception("Ping failed")

        assert service._is_available() is False

    def test_get_user_cache_key(self):
        """Test user cache key generation."""
        service = RedisService()

        key = service._get_user_cache_key("user@example.com")

        assert key == "user:user@example.com"

    def test_get_token_blacklist_key(self):
        """Test token blacklist key generation."""
        service = RedisService()

        key = service._get_token_blacklist_key("token123")

        assert key == "blacklist:token:token123"

    def test_get_user_password_change_key(self):
        """Test password change key generation."""
        service = RedisService()

        key = service._get_user_password_change_key("user@example.com")

        assert key == "password_changed:user@example.com"

    @patch('app.services.redis_service.pickle')
    def test_get_user_cache_hit(self, mock_pickle):
        """Test retrieving user from cache (cache hit)."""
        service = RedisService()
        service.redis_client = Mock()

        mock_user = Mock()
        mock_user.email = "user@example.com"
        service.redis_client.get.return_value = b'cached_data'
        mock_pickle.loads.return_value = mock_user

        result = service.get_user("user@example.com")

        assert result is not None
        assert result.email == "user@example.com"
        service.redis_client.get.assert_called_once_with("user:user@example.com")

    def test_get_user_cache_miss(self):
        """Test retrieving user from cache (cache miss)."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.get.return_value = None

        result = service.get_user("user@example.com")

        assert result is None

    def test_get_user_unavailable(self):
        """Test retrieving user when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.get_user("user@example.com")

        assert result is None

    @patch('app.services.redis_service.pickle')
    def test_set_user_success(self, mock_pickle):
        """Test caching user successfully."""
        service = RedisService()
        service.redis_client = Mock()
        mock_pickle.dumps.return_value = b'serialized_data'

        mock_user = Mock()
        result = service.set_user("user@example.com", mock_user, ttl=600)

        assert result is True
        service.redis_client.setex.assert_called_once()

    def test_set_user_unavailable(self):
        """Test caching user when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.set_user("user@example.com", Mock())

        assert result is False

    def test_delete_user_success(self):
        """Test deleting user from cache."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.delete.return_value = 1

        result = service.delete_user("user@example.com")

        assert result is True
        service.redis_client.delete.assert_called_once_with("user:user@example.com")

    def test_delete_user_not_found(self):
        """Test deleting user that doesn't exist in cache."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.delete.return_value = 0

        result = service.delete_user("user@example.com")

        assert result is False

    def test_delete_user_unavailable(self):
        """Test deleting user when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.delete_user("user@example.com")

        assert result is False

    def test_blacklist_token_success(self):
        """Test blacklisting a token."""
        service = RedisService()
        service.redis_client = Mock()

        result = service.blacklist_token("token123", ttl=1800)

        assert result is True
        service.redis_client.setex.assert_called_once_with(
            "blacklist:token:token123", 1800, "1"
        )

    def test_blacklist_token_unavailable(self):
        """Test blacklisting token when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.blacklist_token("token123", ttl=1800)

        assert result is False

    def test_is_token_blacklisted_true(self):
        """Test checking if token is blacklisted (yes)."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.exists.return_value = 1

        result = service.is_token_blacklisted("token123")

        assert result is True

    def test_is_token_blacklisted_false(self):
        """Test checking if token is blacklisted (no)."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.exists.return_value = 0

        result = service.is_token_blacklisted("token123")

        assert result is False

    def test_is_token_blacklisted_unavailable(self):
        """Test checking blacklist when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.is_token_blacklisted("token123")

        assert result is False

    @patch('app.services.redis_service.datetime')
    def test_set_password_change_timestamp(self, mock_datetime):
        """Test setting password change timestamp."""
        service = RedisService()
        service.redis_client = Mock()
        mock_datetime.utcnow.return_value.isoformat.return_value = "2024-11-28T10:30:00"

        result = service.set_password_change_timestamp("user@example.com")

        assert result is True
        service.redis_client.set.assert_called_once()

    def test_set_password_change_timestamp_unavailable(self):
        """Test setting timestamp when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.set_password_change_timestamp("user@example.com")

        assert result is False

    def test_get_password_change_timestamp_success(self):
        """Test retrieving password change timestamp."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.get.return_value = b"2024-11-28T10:30:00"

        result = service.get_password_change_timestamp("user@example.com")

        assert result == "2024-11-28T10:30:00"

    def test_get_password_change_timestamp_not_found(self):
        """Test retrieving timestamp when not found."""
        service = RedisService()
        service.redis_client = Mock()
        service.redis_client.get.return_value = None

        result = service.get_password_change_timestamp("user@example.com")

        assert result is None

    def test_get_password_change_timestamp_unavailable(self):
        """Test retrieving timestamp when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.get_password_change_timestamp("user@example.com")

        assert result is None

    def test_clear_all_cache_success(self):
        """Test clearing all cache."""
        service = RedisService()
        service.redis_client = Mock()

        result = service.clear_all_cache()

        assert result is True
        service.redis_client.flushdb.assert_called_once()

    def test_clear_all_cache_unavailable(self):
        """Test clearing cache when Redis unavailable."""
        service = RedisService()
        service.redis_client = None

        result = service.clear_all_cache()

        assert result is False

