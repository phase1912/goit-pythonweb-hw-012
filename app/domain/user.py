from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import expression

from app.domain.base import BaseModel
from app.domain.enums import UserRoles


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    hashed_password = mapped_column(String(255), nullable=False)
    role: Mapped[UserRoles] = mapped_column(
        SQLAlchemyEnum(UserRoles),
        nullable=False,
        default=UserRoles.ADMIN.value,
        server_default=UserRoles.ADMIN.value,
    )
    is_confirmed = mapped_column(
        Boolean,
        default=False,
        server_default=expression.text("false"),  # DB-side default
    )
    avatar = mapped_column(String(255), nullable=True)
    refresh_token = mapped_column(String(500), nullable=True)

    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
