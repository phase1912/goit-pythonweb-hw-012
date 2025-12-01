"""
Pytest configuration for integration tests.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.base import BaseModel
from app.domain.user import User
from app.domain.contact import Contact
from app.domain.enums import UserRoles
from app.core.security import get_password_hash, create_access_token
from datetime import timedelta, date

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    BaseModel.metadata.create_all(bind=engine)
    yield engine
    BaseModel.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("testpassword123"),
        role=UserRoles.USER,
        is_confirmed=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    """Create a test admin user in the database."""
    admin = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("adminpassword123"),
        role=UserRoles.ADMIN,
        is_confirmed=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_contact(db_session, test_user):
    """Create a test contact in the database."""
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        date_of_birth=date(1990, 1, 15),
        additional_data="Test contact",
        user_id=test_user.id
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture(scope="function")
async def unauthenticated_client(db_session):
    """Create an unauthenticated async test client."""
    from main import app
    from app.db.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def authenticated_client(db_session, test_user, mock_redis_service):
    """Create an authenticated async test client."""
    from main import app
    from app.db.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Mock redis to return the test user
    mock_redis_service.get_user.return_value = test_user

    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=30)
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"}
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def admin_client(db_session, test_admin, mock_redis_service):
    """Create an admin authenticated async test client."""
    from main import app
    from app.db.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Mock redis to return the test admin
    mock_redis_service.get_user.return_value = test_admin

    access_token = create_access_token(
        data={"sub": test_admin.email},
        expires_delta=timedelta(minutes=30)
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"}
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_redis_service(monkeypatch):
    """Mock Redis service for all tests."""
    from unittest.mock import MagicMock

    mock_redis = MagicMock()
    mock_redis.set_user = MagicMock()
    mock_redis.get_user = MagicMock(return_value=None)
    mock_redis.delete_user = MagicMock()
    mock_redis.set_password_change_timestamp = MagicMock()
    mock_redis.get_password_change_timestamp = MagicMock(return_value=None)

    monkeypatch.setattr("app.services.redis_service.redis_service", mock_redis)
    monkeypatch.setattr("app.api.auth.redis_service", mock_redis)
    monkeypatch.setattr("app.core.security.redis_service", mock_redis)

    return mock_redis


@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    """Mock Email service for all tests."""
    from unittest.mock import MagicMock

    mock_send_verification = MagicMock()
    mock_send_reset = MagicMock()

    monkeypatch.setattr("app.api.auth.send_verification_email", mock_send_verification)
    monkeypatch.setattr("app.api.auth.send_password_reset_email", mock_send_reset)

    return {"send_verification": mock_send_verification, "send_reset": mock_send_reset}


@pytest.fixture(autouse=True)
def mock_cloudinary_service(monkeypatch):
    """Mock Cloudinary service for all tests."""
    from unittest.mock import MagicMock, AsyncMock

    mock_cloudinary = MagicMock()
    mock_cloudinary.upload_avatar = AsyncMock(return_value="https://example.com/avatar.jpg")

    monkeypatch.setattr("app.services.cloudinary_service.cloudinary_service", mock_cloudinary)
    monkeypatch.setattr("app.api.auth.cloudinary_service", mock_cloudinary)

    return mock_cloudinary

