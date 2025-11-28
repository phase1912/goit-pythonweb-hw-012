from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactUpdate
from app.domain.contact import Contact


class ContactAlreadyExistsError(Exception):
    """
    Exception raised when attempting to create a contact with an email that already exists.

    This ensures email uniqueness per user in the contact list.
    """
    pass


class ContactNotFoundError(Exception):
    """
    Exception raised when a requested contact cannot be found.

    This typically occurs when accessing a non-existent contact or
    when a user tries to access another user's contact.
    """
    pass


class ContactService:
    """
    Service layer for contact business logic operations.

    This service handles all contact-related operations including CRUD,
    search, and birthday tracking. It enforces business rules such as
    email uniqueness and user isolation.

    Attributes:
        repository (ContactRepository): Repository for contact data access.

    Note:
        All operations are user-scoped - users can only access their own contacts.
    """

    def __init__(self, db: Session):
        """
        Initialize the ContactService.

        Args:
            db (Session): SQLAlchemy database session.
        """
        self.repository = ContactRepository(db)

    def create_contact(self, contact_data: ContactCreate, user_id: int) -> Contact:
        """
        Create a new contact for a user.

        Args:
            contact_data (ContactCreate): Contact information including name, email, phone, etc.
            user_id (int): ID of the user creating the contact.

        Returns:
            Contact: The newly created contact object.

        Raises:
            ContactAlreadyExistsError: If a contact with the same email already exists for this user.

        Example:
            >>> contact_data = ContactCreate(
            ...     first_name="John",
            ...     last_name="Doe",
            ...     email="john@example.com"
            ... )
            >>> service.create_contact(contact_data, user_id=1)
            <Contact id=1 email='john@example.com'>
        """
        if self.repository.exists_by_email(contact_data.email, user_id):
            raise ContactAlreadyExistsError(
                f"Contact with email {contact_data.email} already exists"
            )
        return self.repository.create(contact_data, user_id)

    def get_contact(self, contact_id: int, user_id: int) -> Contact:
        """
        Retrieve a specific contact by ID.

        Args:
            contact_id (int): The ID of the contact to retrieve.
            user_id (int): The ID of the user requesting the contact.

        Returns:
            Contact: The requested contact object.

        Raises:
            ContactNotFoundError: If the contact doesn't exist or doesn't belong to the user.

        Note:
            Users can only access their own contacts (user isolation enforced).
        """
        contact = self.repository.get_by_id(contact_id, user_id)
        if not contact:
            raise ContactNotFoundError(f"Contact with ID {contact_id} not found")
        return contact

    def get_contact_by_email(self, email: str, user_id: int) -> Optional[Contact]:
        """
        Find a contact by email address.

        Args:
            email (str): The email address to search for.
            user_id (int): The ID of the user performing the search.

        Returns:
            Optional[Contact]: The contact if found, None otherwise.

        Note:
            Search is scoped to the user's own contacts only.
        """
        return self.repository.get_by_email(email, user_id)

    def get_all_contacts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Contact], int]:
        """
        Retrieve all contacts for a user with pagination.

        Args:
            user_id (int): The ID of the user requesting contacts.
            skip (int): Number of records to skip (for pagination). Defaults to 0.
            limit (int): Maximum number of records to return. Defaults to 100.

        Returns:
            tuple[List[Contact], int]: A tuple containing:
                - List of contact objects
                - Total count of contacts (for pagination)

        Example:
            >>> contacts, total = service.get_all_contacts(user_id=1, skip=0, limit=10)
            >>> print(f"Showing {len(contacts)} of {total} contacts")
            Showing 10 of 50 contacts
        """
        return self.repository.get_all(user_id, skip, limit)

    def search_contacts(
        self,
        query: str,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Contact], int]:
        """
        Search contacts by name, email, or phone number.

        Performs a case-insensitive search across multiple fields.
        If query is empty, returns all contacts.

        Args:
            query (str): Search query string to match against contact fields.
            user_id (int): The ID of the user performing the search.
            skip (int): Number of records to skip (for pagination). Defaults to 0.
            limit (int): Maximum number of records to return. Defaults to 100.

        Returns:
            tuple[List[Contact], int]: A tuple containing:
                - List of matching contact objects
                - Total count of matching contacts

        Note:
            Search is performed on first_name, last_name, email, and phone fields.
            Empty or whitespace-only queries return all contacts.

        Example:
            >>> contacts, total = service.search_contacts("john", user_id=1)
            >>> # Returns all contacts with "john" in name, email, or phone
        """
        if not query or not query.strip():
            return self.get_all_contacts(user_id, skip, limit)
        return self.repository.search(query.strip(), user_id, skip, limit)

    def get_upcoming_birthdays(self, user_id: int, days: int = 7) -> List[Contact]:
        """
        Get contacts with birthdays in the upcoming specified days.

        Args:
            user_id (int): The ID of the user requesting birthday information.
            days (int): Number of days to look ahead. Defaults to 7. Must be between 1 and 365.

        Returns:
            List[Contact]: List of contacts with birthdays in the specified period.

        Raises:
            ValueError: If days is not between 1 and 365.

        Example:
            >>> # Get contacts with birthdays in the next week
            >>> upcoming = service.get_upcoming_birthdays(user_id=1, days=7)
            >>> for contact in upcoming:
            ...     print(f"{contact.first_name}'s birthday is coming up!")
        """
        if days < 1 or days > 365:
            raise ValueError("Days must be between 1 and 365")
        return self.repository.get_upcoming_birthdays(user_id, days)

    def update_contact(
        self,
        contact_id: int,
        user_id: int,
        contact_data: ContactUpdate
    ) -> Contact:
        """
        Update an existing contact.

        Args:
            contact_id (int): The ID of the contact to update.
            user_id (int): The ID of the user performing the update.
            contact_data (ContactUpdate): Updated contact information.

        Returns:
            Contact: The updated contact object.

        Raises:
            ContactNotFoundError: If the contact doesn't exist or doesn't belong to the user.
            ContactAlreadyExistsError: If updating email to one that already exists for another contact.

        Note:
            - Only provided fields will be updated (partial update supported)
            - Email uniqueness is enforced per user
            - Users can only update their own contacts

        Example:
            >>> update_data = ContactUpdate(phone="+1234567890")
            >>> updated = service.update_contact(contact_id=1, user_id=1, contact_data=update_data)
            >>> print(updated.phone)
            +1234567890
        """
        existing_contact = self.repository.get_by_id(contact_id, user_id)
        if not existing_contact:
            raise ContactNotFoundError(f"Contact with ID {contact_id} not found")

        if contact_data.email and contact_data.email != existing_contact.email:
            if self.repository.exists_by_email(contact_data.email, user_id, exclude_id=contact_id):
                raise ContactAlreadyExistsError(
                    f"Contact with email {contact_data.email} already exists"
                )

        updated_contact = self.repository.update(contact_id, user_id, contact_data)
        if not updated_contact:
            raise ContactNotFoundError(f"Contact with ID {contact_id} not found")
        return updated_contact

    def delete_contact(self, contact_id: int, user_id: int) -> bool:
        """
        Delete a contact.

        Args:
            contact_id (int): The ID of the contact to delete.
            user_id (int): The ID of the user performing the deletion.

        Returns:
            bool: True if deletion was successful.

        Raises:
            ContactNotFoundError: If the contact doesn't exist or doesn't belong to the user.

        Note:
            Users can only delete their own contacts (user isolation enforced).

        Example:
            >>> service.delete_contact(contact_id=1, user_id=1)
            True
        """
        success = self.repository.delete(contact_id, user_id)
        if not success:
            raise ContactNotFoundError(f"Contact with ID {contact_id} not found")
        return True

