from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactUpdate
from app.domain.contact import Contact


class ContactAlreadyExistsError(Exception):
    pass


class ContactNotFoundError(Exception):
    pass


class ContactService:
    def __init__(self, db: Session):
        self.repository = ContactRepository(db)

    def create_contact(self, contact_data: ContactCreate, user_id: int) -> Contact:
        if self.repository.exists_by_email(contact_data.email, user_id):
            raise ContactAlreadyExistsError(
                f"Contact with email {contact_data.email} already exists"
            )
        return self.repository.create(contact_data, user_id)

    def get_contact(self, contact_id: int, user_id: int) -> Contact:
        contact = self.repository.get_by_id(contact_id, user_id)
        if not contact:
            raise ContactNotFoundError(f"Contact with ID {contact_id} not found")
        return contact

    def get_contact_by_email(self, email: str, user_id: int) -> Optional[Contact]:
        return self.repository.get_by_email(email, user_id)

    def get_all_contacts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Contact], int]:
        return self.repository.get_all(user_id, skip, limit)

    def search_contacts(
        self,
        query: str,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Contact], int]:
        if not query or not query.strip():
            return self.get_all_contacts(user_id, skip, limit)
        return self.repository.search(query.strip(), user_id, skip, limit)

    def get_upcoming_birthdays(self, user_id: int, days: int = 7) -> List[Contact]:
        if days < 1 or days > 365:
            raise ValueError("Days must be between 1 and 365")
        return self.repository.get_upcoming_birthdays(user_id, days)

    def update_contact(
        self,
        contact_id: int,
        user_id: int,
        contact_data: ContactUpdate
    ) -> Contact:
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
        success = self.repository.delete(contact_id, user_id)
        if not success:
            raise ContactNotFoundError(f"Contact with ID {contact_id} not found")
        return True

