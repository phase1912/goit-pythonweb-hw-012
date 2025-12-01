"""
Unit tests for ContactService.
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.services.contact_service import (
    ContactService,
    ContactAlreadyExistsError,
    ContactNotFoundError
)
from app.schemas.contact import ContactCreate, ContactUpdate
from app.domain.contact import Contact


class TestContactService:
    """Test cases for ContactService."""

    def test_create_contact_success(self, db_session, test_user):
        """Test successfully creating a contact."""
        from datetime import date
        service = ContactService(db_session)
        contact_data = ContactCreate(
            first_name="Alice",
            last_name="Johnson",
            email="alice@example.com",
            phone_number="+1111111111",
            date_of_birth=date(1990, 1, 1)
        )

        contact = service.create_contact(contact_data, test_user.id)

        assert contact is not None
        assert contact.email == "alice@example.com"
        assert contact.user_id == test_user.id

    def test_create_contact_duplicate_email(self, db_session, test_contact, test_user):
        """Test creating contact with duplicate email raises error."""
        from datetime import date
        service = ContactService(db_session)
        contact_data = ContactCreate(
            first_name="Duplicate",
            last_name="User",
            email=test_contact.email,  # Duplicate
            phone_number="+2222222222",
            date_of_birth=date(1990, 1, 1)
        )

        with pytest.raises(ContactAlreadyExistsError):
            service.create_contact(contact_data, test_user.id)

    def test_get_contact_success(self, db_session, test_contact, test_user):
        """Test retrieving an existing contact."""
        service = ContactService(db_session)

        contact = service.get_contact(test_contact.id, test_user.id)

        assert contact is not None
        assert contact.id == test_contact.id

    def test_get_contact_not_found(self, db_session, test_user):
        """Test retrieving non-existent contact raises error."""
        service = ContactService(db_session)

        with pytest.raises(ContactNotFoundError):
            service.get_contact(99999, test_user.id)

    def test_get_contact_by_email(self, db_session, test_contact, test_user):
        """Test retrieving contact by email."""
        service = ContactService(db_session)

        contact = service.get_contact_by_email(test_contact.email, test_user.id)

        assert contact is not None
        assert contact.email == test_contact.email

    def test_get_contact_by_email_not_found(self, db_session, test_user):
        """Test retrieving contact by non-existent email."""
        service = ContactService(db_session)

        contact = service.get_contact_by_email("nonexistent@example.com", test_user.id)

        assert contact is None

    def test_get_all_contacts(self, db_session, multiple_contacts, test_user):
        """Test retrieving all contacts with pagination."""
        service = ContactService(db_session)

        contacts, total = service.get_all_contacts(test_user.id, skip=0, limit=10)

        assert len(contacts) == 5
        assert total == 5

    def test_search_contacts(self, db_session, test_contact, test_user):
        """Test searching contacts."""
        service = ContactService(db_session)

        contacts, total = service.search_contacts("John", test_user.id, skip=0, limit=10)

        assert total >= 1

    def test_search_contacts_empty_query(self, db_session, multiple_contacts, test_user):
        """Test searching with empty query returns all contacts."""
        service = ContactService(db_session)

        contacts, total = service.search_contacts("", test_user.id, skip=0, limit=10)

        assert len(contacts) == 5  # Should return all

    def test_get_upcoming_birthdays(self, db_session, test_user):
        """Test getting contacts with upcoming birthdays."""
        service = ContactService(db_session)

        contacts = service.get_upcoming_birthdays(test_user.id, days=7)

        assert isinstance(contacts, list)

    def test_get_upcoming_birthdays_invalid_days(self, db_session, test_user):
        """Test getting birthdays with invalid days parameter."""
        service = ContactService(db_session)

        with pytest.raises(ValueError):
            service.get_upcoming_birthdays(test_user.id, days=0)

        with pytest.raises(ValueError):
            service.get_upcoming_birthdays(test_user.id, days=400)

    def test_update_contact_success(self, db_session, test_contact, test_user):
        """Test successfully updating a contact."""
        service = ContactService(db_session)
        update_data = ContactUpdate(
            first_name="Updated",
            phone_number="+9999999999"
        )

        updated = service.update_contact(test_contact.id, test_user.id, update_data)

        assert updated is not None
        assert updated.first_name == "Updated"
        assert updated.phone_number == "+9999999999"

    def test_update_contact_not_found(self, db_session, test_user):
        """Test updating non-existent contact raises error."""
        service = ContactService(db_session)
        update_data = ContactUpdate(first_name="Updated")

        with pytest.raises(ContactNotFoundError):
            service.update_contact(99999, test_user.id, update_data)

    def test_update_contact_duplicate_email(self, db_session, test_user):
        """Test updating contact with duplicate email raises error."""
        from datetime import date
        service = ContactService(db_session)

        # Create two contacts
        contact1_data = ContactCreate(
            first_name="Alice",
            last_name="First",
            email="contact1@example.com",
            phone_number="+1111111111",
            date_of_birth=date(1990, 1, 1)
        )
        contact2_data = ContactCreate(
            first_name="Bob",
            last_name="Second",
            email="contact2@example.com",
            phone_number="+2222222222",
            date_of_birth=date(1991, 1, 1)
        )

        contact1 = service.create_contact(contact1_data, test_user.id)
        contact2 = service.create_contact(contact2_data, test_user.id)

        # Try to update contact2 with contact1's email
        update_data = ContactUpdate(email="contact1@example.com")

        with pytest.raises(ContactAlreadyExistsError):
            service.update_contact(contact2.id, test_user.id, update_data)

    def test_update_contact_same_email(self, db_session, test_contact, test_user):
        """Test updating contact with same email (should succeed)."""
        service = ContactService(db_session)
        update_data = ContactUpdate(
            email=test_contact.email,  # Same email
            first_name="Newname"
        )

        updated = service.update_contact(test_contact.id, test_user.id, update_data)

        assert updated is not None
        assert updated.first_name == "Newname"

    def test_delete_contact_success(self, db_session, test_contact, test_user):
        """Test successfully deleting a contact."""
        service = ContactService(db_session)

        result = service.delete_contact(test_contact.id, test_user.id)

        assert result is True

    def test_delete_contact_not_found(self, db_session, test_user):
        """Test deleting non-existent contact raises error."""
        service = ContactService(db_session)

        with pytest.raises(ContactNotFoundError):
            service.delete_contact(99999, test_user.id)

