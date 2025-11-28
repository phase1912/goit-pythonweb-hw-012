from typing import Optional
from sqlalchemy.orm import Session

from app.domain.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: UserCreate) -> User:
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def exists_by_email(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None

    def update_refresh_token(self, user_id: int, refresh_token: str) -> User:
        user = self.get_by_id(user_id)
        if user:
            user.refresh_token = refresh_token
            self.db.commit()
            self.db.refresh(user)
        return user

    def verify_refresh_token(self, email: str, refresh_token: str) -> bool:
        user = self.get_by_email(email)
        if not user or not user.refresh_token:
            return False
        return user.refresh_token == refresh_token

    def clear_refresh_token(self, user_id: int) -> None:
        user = self.get_by_id(user_id)
        if user:
            user.refresh_token = None
            self.db.commit()

    def confirm_email(self, email: str) -> Optional[User]:
        user = self.get_by_email(email)
        if user:
            user.is_confirmed = True
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_avatar(self, user_id: int, avatar_url: str) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.avatar = avatar_url
            self.db.commit()
            self.db.refresh(user)
        return user

    def reset_password(self, email: str, new_password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if user:
            hashed_password = get_password_hash(new_password)
            user.hashed_password = hashed_password
            user.refresh_token = None
            self.db.commit()
            self.db.refresh(user)
        return user

