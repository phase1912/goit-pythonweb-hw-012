from sqlalchemy import Column, String, Date, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.domain.base import BaseModel


class Contact(BaseModel):
    __tablename__ = "contacts"

    first_name = Column(String(50), nullable=False, index=True)
    last_name = Column(String(50), nullable=False, index=True)
    email = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    additional_data = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="contacts")
