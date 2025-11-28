import redis
import pickle
from typing import Optional, Any
from datetime import datetime
from app.core.config import settings


class RedisService:
    def __init__(self):
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
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False

    def _get_user_cache_key(self, email: str) -> str:
        return f"user:{email}"

    def _get_token_blacklist_key(self, token: str) -> str:
        return f"blacklist:token:{token}"

    def _get_user_password_change_key(self, email: str) -> str:
        return f"password_changed:{email}"

    def get_user(self, email: str) -> Optional[Any]:
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
        if not self._is_available():
            return False

        try:
            key = self._get_token_blacklist_key(token)
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Error checking token blacklist: {e}")
            return False

    def set_password_change_timestamp(self, email: str) -> bool:
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
