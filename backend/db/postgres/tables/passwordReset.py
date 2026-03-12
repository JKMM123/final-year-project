from sqlalchemy import Column, DateTime, func, String, Boolean, Integer
from db.postgres.base import Base
from uuid import uuid4

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, nullable=False)
    token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, onupdate=func.now())



