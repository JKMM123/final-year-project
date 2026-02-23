from sqlalchemy import Column, String, Integer

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base

class WhatsAppSession(Base):
    __tablename__ = "whatsapp_session"

    id = Column(Integer, primary_key=True, default=1)
    name = Column(String, nullable=False)
    session_id = Column(Integer, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    webhook_secret = Column(String, nullable=False)
    