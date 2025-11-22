from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.domain.user import User
from app.core.security import verify_password


class UserAlreadyExistsError(Exception):
    pass


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self, user_data: UserCreate) -> User:
        if self.repository.exists_by_email(user_data.email):
            raise UserAlreadyExistsError(
                f"User with email {user_data.email} already exists"
            )
        return self.repository.create(user_data)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.repository.get_by_email(email)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.repository.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

