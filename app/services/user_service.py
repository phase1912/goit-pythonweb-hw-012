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

    def save_refresh_token(self, user_id: int, refresh_token: str) -> User:
        return self.repository.update_refresh_token(user_id, refresh_token)

    def verify_refresh_token(self, email: str, refresh_token: str) -> bool:
        return self.repository.verify_refresh_token(email, refresh_token)

    def revoke_refresh_token(self, user_id: int) -> None:
        self.repository.clear_refresh_token(user_id)

    def confirm_email(self, email: str) -> Optional[User]:
        return self.repository.confirm_email(email)

    def update_avatar(self, user_id: int, avatar_url: str) -> Optional[User]:
        return self.repository.update_avatar(user_id, avatar_url)

    def reset_password(self, email: str, new_password: str) -> Optional[User]:
        return self.repository.reset_password(email, new_password)

