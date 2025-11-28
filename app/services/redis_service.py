import redis
import pickle
from typing import Optional, Any
from datetime import datetime
from app.core.config import settings


class RedisService:
    """
    Redis caching service for user authentication and token management.

    This service provides high-performance caching for user data and handles
    token blacklisting and password change tracking for security purposes.

    Attributes:
        redis_client: Redis connection client or None if connection failed.

    Features:
        - User data caching with automatic TTL
        - Token blacklisting for immediate revocation
        - Password change timestamp tracking
        - Graceful degradation if Redis unavailable
    """

    def __init__(self):
        """
        Initialize Redis connection.

        Attempts to connect to Redis server. If connection fails, the service
        will operate in degraded mode (all operations return None/False).
        """
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
            # Test connection
            self.redis_client.ping()
            print("✓ Redis connection established successfully")
        except redis.ConnectionError as e:
            print(f"✗ Redis connection failed: {e}")
            self.redis_client = None
        except Exception as e:
            print(f"✗ Unexpected Redis error: {e}")
            self.redis_client = None

    def _is_available(self) -> bool:
        """
        Check if Redis connection is available and working.

        Returns:
            bool: True if Redis is available, False otherwise.

        Note:
            This method is used internally before each Redis operation
            to ensure graceful degradation when Redis is unavailable.
        """
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False

    def _get_user_cache_key(self, email: str) -> str:
        """
        Generate Redis key for user cache.

        Args:
            email (str): User's email address.

        Returns:
            str: Redis key in format "user:{email}".
        """
        return f"user:{email}"

    def _get_token_blacklist_key(self, token: str) -> str:
        """
        Generate Redis key for token blacklist.

        Args:
            token (str): JWT token to blacklist.

        Returns:
            str: Redis key in format "blacklist:token:{token}".
        """
        return f"blacklist:token:{token}"

    def _get_user_password_change_key(self, email: str) -> str:
        """
        Generate Redis key for password change timestamp.

        Args:
            email (str): User's email address.

        Returns:
            str: Redis key in format "password_changed:{email}".
        """
        return f"password_changed:{email}"

    def get_user(self, email: str) -> Optional[Any]:
        """
        Retrieve user data from Redis cache.

        Args:
            email (str): User's email address to lookup.

        Returns:
            Optional[Any]: Cached user object if found, None otherwise.

        Note:
            - Uses pickle for serialization/deserialization
            - Returns None if Redis unavailable or cache miss
            - Logs cache HIT/MISS for monitoring

        Example:
            >>> user = redis_service.get_user("user@example.com")
            >>> if user:
            ...     print(f"Found cached user: {user.email}")
        """
        if not self._is_available():
            return None

        try:
            key = self._get_user_cache_key(email)
            cached_data = self.redis_client.get(key)

            if cached_data:
                user = pickle.loads(cached_data)
                print(f"✓ Cache HIT for user: {email}")
                return user

            print(f"✗ Cache MISS for user: {email}")
            return None
        except Exception as e:
            print(f"Error retrieving user from cache: {e}")
            return None

    def set_user(self, email: str, user: Any, ttl: Optional[int] = None) -> bool:
        """
        Cache user data in Redis with automatic expiration.

        Args:
            email (str): User's email address as cache key.
            user (Any): User object to cache (will be pickled).
            ttl (Optional[int]): Time-to-live in seconds. Defaults to settings.redis_cache_ttl (900s).

        Returns:
            bool: True if caching successful, False otherwise.

        Note:
            - Uses pickle for serialization
            - Default TTL is 15 minutes (900 seconds)
            - Automatic expiration prevents stale data
            - Returns False if Redis unavailable

        Example:
            >>> redis_service.set_user("user@example.com", user_obj, ttl=600)
            True
        """
        if not self._is_available():
            return False

        try:
            key = self._get_user_cache_key(email)
            ttl = ttl or settings.redis_cache_ttl

            serialized_user = pickle.dumps(user)
            self.redis_client.setex(key, ttl, serialized_user)

            print(f"✓ User cached: {email} (TTL: {ttl}s)")
            return True
        except Exception as e:
            print(f"Error caching user: {e}")
            return False

    def delete_user(self, email: str) -> bool:
        """
        Remove user data from Redis cache.

        Args:
            email (str): User's email address to remove from cache.

        Returns:
            bool: True if cache entry was deleted, False otherwise.

        Note:
            - Should be called when user data changes (logout, profile update, etc.)
            - Returns False if Redis unavailable or key doesn't exist
            - Ensures cache consistency

        Example:
            >>> redis_service.delete_user("user@example.com")
            True
        """
        if not self._is_available():
            return False

        try:
            key = self._get_user_cache_key(email)
            deleted = self.redis_client.delete(key)

            if deleted:
                print(f"✓ User cache invalidated: {email}")
            return bool(deleted)
        except Exception as e:
            print(f"Error deleting user from cache: {e}")
            return False

    def blacklist_token(self, token: str, ttl: int) -> bool:
        """
        Add a JWT token to the blacklist for immediate revocation.

        Args:
            token (str): The JWT token to blacklist.
            ttl (int): Time-to-live in seconds (should match token's remaining lifetime).

        Returns:
            bool: True if token was blacklisted successfully, False otherwise.

        Note:
            - Used for logout or forced token revocation
            - TTL should match token's expiration to avoid memory waste
            - Token will be rejected by get_current_user if blacklisted
            - Returns False if Redis unavailable

        Example:
            >>> # Blacklist token with 1800 seconds (30 minutes) remaining
            >>> redis_service.blacklist_token(access_token, ttl=1800)
            True
        """
        if not self._is_available():
            return False

        try:
            key = self._get_token_blacklist_key(token)
            self.redis_client.setex(key, ttl, "1")
            print(f"✓ Token blacklisted (TTL: {ttl}s)")
            return True
        except Exception as e:
            print(f"Error blacklisting token: {e}")
            return False

    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a JWT token has been blacklisted.

        Args:
            token (str): The JWT token to check.

        Returns:
            bool: True if token is blacklisted, False otherwise.

        Note:
            - Returns False if Redis unavailable (fail-open for availability)
            - Used by authentication middleware to reject revoked tokens
            - Provides immediate token revocation capability

        Example:
            >>> if redis_service.is_token_blacklisted(token):
            ...     raise HTTPException(401, "Token has been revoked")
        """
        if not self._is_available():
            return False

        try:
            key = self._get_token_blacklist_key(token)
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Error checking token blacklist: {e}")
            return False

    def set_password_change_timestamp(self, email: str) -> bool:
        """
        Record the timestamp when a user's password was changed.

        Args:
            email (str): User's email address.

        Returns:
            bool: True if timestamp was stored successfully, False otherwise.

        Note:
            - Used to invalidate all access tokens issued before password change
            - Timestamp stored in ISO format (YYYY-MM-DDTHH:MM:SS.mmmmmm)
            - No expiration - persists until manually deleted or Redis cleared
            - Critical for security after password reset

        Example:
            >>> # After successful password reset
            >>> redis_service.set_password_change_timestamp("user@example.com")
            True
        """
        if not self._is_available():
            return False

        try:
            key = self._get_user_password_change_key(email)
            timestamp = datetime.utcnow().isoformat()
            self.redis_client.set(key, timestamp)
            print(f"✓ Password change timestamp set for: {email}")
            return True
        except Exception as e:
            print(f"Error setting password change timestamp: {e}")
            return False

    def get_password_change_timestamp(self, email: str) -> Optional[str]:
        """
        Retrieve the timestamp of a user's last password change.

        Args:
            email (str): User's email address.

        Returns:
            Optional[str]: ISO format timestamp string if found, None otherwise.

        Note:
            - Returns None if no password change recorded or Redis unavailable
            - Used by authentication to validate tokens against password changes
            - Timestamp format: ISO 8601 (YYYY-MM-DDTHH:MM:SS.mmmmmm)

        Example:
            >>> timestamp = redis_service.get_password_change_timestamp("user@example.com")
            >>> if timestamp:
            ...     print(f"Password last changed at: {timestamp}")
            Password last changed at: 2024-11-28T10:30:00.123456
        """
        if not self._is_available():
            return None

        try:
            key = self._get_user_password_change_key(email)
            timestamp = self.redis_client.get(key)
            if timestamp:
                return timestamp.decode('utf-8') if isinstance(timestamp, bytes) else timestamp
            return None
        except Exception as e:
            print(f"Error getting password change timestamp: {e}")
            return None

    def clear_all_cache(self) -> bool:
        """
        Clear all cached data from Redis database.

        Returns:
            bool: True if cache was cleared successfully, False otherwise.

        Warning:
            This removes ALL data from the current Redis database.
            Use with caution, especially in production environments.

        Note:
            - Clears all keys in the currently selected Redis database
            - Affects all cached users, tokens, and timestamps
            - Useful for testing or emergency cache invalidation
            - Does NOT affect other Redis databases (if using multiple)

        Example:
            >>> # Clear all cache (use carefully!)
            >>> redis_service.clear_all_cache()
            ✓ All cache cleared
            True
        """
        if not self._is_available():
            return False

        try:
            self.redis_client.flushdb()
            print("✓ All cache cleared")
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False


# Singleton instance
redis_service = RedisService()
