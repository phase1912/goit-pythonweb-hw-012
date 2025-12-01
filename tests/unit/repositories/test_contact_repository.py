"""
Unit tests for ContactRepository.
"""
import pytest
from datetime import date, timedelta
from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactUpdate
from app.domain.contact import Contact


class TestContactRepository:
    """Test cases for ContactRepository."""

    def test_create_contact(self, db_session, test_user):
        """Test creating a new contact."""
        repository = ContactRepository(db_session)
        contact_data = ContactCreate(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone_number="+1987654321",
            date_of_birth=date(1992, 5, 20)
        )

        contact = repository.create(contact_data, test_user.id)

        assert contact.id is not None
        assert contact.first_name == "Jane"
        assert contact.last_name == "Smith"
        assert contact.email == "jane.smith@example.com"
        assert contact.phone_number == "+1987654321"
        assert contact.user_id == test_user.id

    def test_get_by_id(self, db_session, test_contact, test_user):
        """Test retrieving contact by ID."""
        repository = ContactRepository(db_session)

        contact = repository.get_by_id(test_contact.id, test_user.id)

        assert contact is not None
        assert contact.id == test_contact.id
        assert contact.email == test_contact.email

    def test_get_by_id_wrong_user(self, db_session, test_contact, test_admin):
        """Test retrieving contact with wrong user ID (user isolation)."""
        repository = ContactRepository(db_session)

        contact = repository.get_by_id(test_contact.id, test_admin.id)

        assert contact is None

    def test_get_by_id_not_found(self, db_session, test_user):
        """Test retrieving non-existent contact."""
        repository = ContactRepository(db_session)

        contact = repository.get_by_id(99999, test_user.id)

        assert contact is None

    def test_get_by_email(self, db_session, test_contact, test_user):
        """Test retrieving contact by email."""
        repository = ContactRepository(db_session)

        contact = repository.get_by_email(test_contact.email, test_user.id)

        assert contact is not None
        assert contact.email == test_contact.email

    def test_get_by_email_not_found(self, db_session, test_user):
        """Test retrieving non-existent contact by email."""
        repository = ContactRepository(db_session)

        contact = repository.get_by_email("nonexistent@example.com", test_user.id)

        assert contact is None

    def test_exists_by_email(self, db_session, test_contact, test_user):
        """Test checking if contact exists by email."""
        repository = ContactRepository(db_session)

        exists = repository.exists_by_email(test_contact.email, test_user.id)

        assert exists is True

    def test_exists_by_email_not_found(self, db_session, test_user):
        """Test checking non-existent contact by email."""
        repository = ContactRepository(db_session)

        exists = repository.exists_by_email("nonexistent@example.com", test_user.id)

        assert exists is False

    def test_exists_by_email_exclude_self(self, db_session, test_contact, test_user):
        """Test checking email existence excluding current contact."""
        repository = ContactRepository(db_session)

        exists = repository.exists_by_email(
            test_contact.email,
            test_user.id,
            exclude_id=test_contact.id
        )

        assert exists is False

    def test_get_all(self, db_session, multiple_contacts, test_user):
        """Test retrieving all contacts for a user."""
        repository = ContactRepository(db_session)

        contacts, total = repository.get_all(test_user.id, skip=0, limit=10)

        assert len(contacts) == 5
        assert total == 5

    def test_get_all_pagination(self, db_session, multiple_contacts, test_user):
        """Test pagination when retrieving contacts."""
        repository = ContactRepository(db_session)

        contacts, total = repository.get_all(test_user.id, skip=2, limit=2)

        assert len(contacts) == 2
        assert total == 5

    def test_get_all_empty(self, db_session, test_user):
        """Test retrieving contacts when user has none."""
        repository = ContactRepository(db_session)

        contacts, total = repository.get_all(test_user.id, skip=0, limit=10)

        assert len(contacts) == 0
        assert total == 0

    def test_search_by_name(self, db_session, test_contact, test_user):
        """Test searching contacts by name."""
        repository = ContactRepository(db_session)

        contacts, total = repository.search("John", test_user.id, skip=0, limit=10)

        assert len(contacts) >= 1
        assert any(c.first_name == "John" for c in contacts)

    def test_search_by_email(self, db_session, test_contact, test_user):
        """Test searching contacts by email."""
        repository = ContactRepository(db_session)

        contacts, total = repository.search("john.doe", test_user.id, skip=0, limit=10)

        assert len(contacts) >= 1
        assert any("john.doe" in c.email.lower() for c in contacts)

    def test_search_no_results(self, db_session, test_user):
        """Test searching with no matching results."""
        repository = ContactRepository(db_session)

        contacts, total = repository.search("NonExistent", test_user.id, skip=0, limit=10)

        assert len(contacts) == 0
        assert total == 0

    def test_get_upcoming_birthdays(self, db_session, test_user):
        """Test retrieving contacts with upcoming birthdays."""
        repository = ContactRepository(db_session)

        # Create contact with birthday in next 3 days
        today = date.today()
        upcoming_date = today + timedelta(days=2)
        birthday_date = date(today.year - 30, upcoming_date.month, upcoming_date.day)

        contact_data = ContactCreate(
            first_name="Birthday",
            last_name="Person",
            email="birthday@example.com",
            phone_number="+1111111111",
            date_of_birth=birthday_date
        )
        repository.create(contact_data, test_user.id)

        contacts = repository.get_upcoming_birthdays(test_user.id, days=7)

        assert len(contacts) >= 1
        assert any(c.first_name == "Birthday" for c in contacts)

    def test_update_contact(self, db_session, test_contact, test_user):
        """Test updating a contact."""
        repository = ContactRepository(db_session)
        update_data = ContactUpdate(
            first_name="Updated",
            phone_number="+9999999999"
        )

        updated = repository.update(test_contact.id, test_user.id, update_data)

        assert updated is not None
        assert updated.first_name == "Updated"
        assert updated.phone_number == "+9999999999"
        assert updated.last_name == test_contact.last_name  # Unchanged

    def test_update_contact_not_found(self, db_session, test_user):
        """Test updating non-existent contact."""
        repository = ContactRepository(db_session)
        update_data = ContactUpdate(first_name="Updated")

        result = repository.update(99999, test_user.id, update_data)

        assert result is None

    def test_update_contact_wrong_user(self, db_session, test_contact, test_admin):
        """Test updating contact with wrong user (user isolation)."""
        repository = ContactRepository(db_session)
        update_data = ContactUpdate(first_name="Updated")

        result = repository.update(test_contact.id, test_admin.id, update_data)

        assert result is None

    def test_delete_contact(self, db_session, test_contact, test_user):
        """Test deleting a contact."""
        repository = ContactRepository(db_session)

        success = repository.delete(test_contact.id, test_user.id)

        assert success is True

        # Verify contact is deleted
        deleted = repository.get_by_id(test_contact.id, test_user.id)
        assert deleted is None

    def test_delete_contact_not_found(self, db_session, test_user):
        """Test deleting non-existent contact."""
        repository = ContactRepository(db_session)

        success = repository.delete(99999, test_user.id)

        assert success is False

    def test_delete_contact_wrong_user(self, db_session, test_contact, test_admin):
        """Test deleting contact with wrong user (user isolation)."""
        repository = ContactRepository(db_session)

        success = repository.delete(test_contact.id, test_admin.id)

        assert success is False

