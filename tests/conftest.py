"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
from faker import Faker
from app.core.config import Settings

fake = Faker()


class TestSettings(Settings):
    """Settings for tests."""

    # Use file-based SQLite for integration tests (persists during test session)
    # This ensures data is available across all fixtures in a test
    database_url: str = "sqlite:///./test_contacts.db"

    secret_key: str = "test_secret_key_for_testing_only_min_32_chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Disable external services for tests
    redis_url: str = "redis://localhost:6379/15"  # Use different DB for tests

    # Email settings (mocked in tests)
    mail_username: str = "test@example.com"
    mail_password: str = "test_password"
    mail_from: str = "test@example.com"
    mail_port: int = 1025
    mail_server: str = "localhost"

    # Cloudinary settings (mocked in tests)
    cloudinary_cloud_name: str = "test_cloud"
    cloudinary_api_key: str = "test_key"
    cloudinary_api_secret: str = "test_secret"

    class Config:
        env_file = ".testenv"


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Settings for tests."""
    return TestSettings()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Set anyio backend to asyncio."""
    print("\n--> execute 'anyio_backend' fixture")
    return "asyncio"
