"""
Pytest configuration for unit tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.domain.base import BaseModel
from app.domain.user import User
from app.domain.contact import Contact
from app.domain.enums import UserRoles
from app.core.security import get_password_hash
from tests.conftest import fake


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine for unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    BaseModel.metadata.create_all(bind=engine)
    yield engine
    BaseModel.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session for unit tests."""
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


@pytest.fixture
def multiple_contacts(db_session, test_user):
    """Create multiple test contacts in the database."""
    contacts = []
    for i in range(5):
        contact = Contact(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            phone_number=fake.phone_number()[:15],
            date_of_birth=fake.date_of_birth(minimum_age=20, maximum_age=80),
            user_id=test_user.id
        )
        db_session.add(contact)
        contacts.append(contact)

    db_session.commit()
    for contact in contacts:
        db_session.refresh(contact)

    return contacts

