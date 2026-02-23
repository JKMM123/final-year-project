from sqlalchemy import Column, DateTime, func, String, Boolean, Integer
from db.postgres.base import Base
from uuid import uuid4


class OTP(Base):
    __tablename__ = "otp"

    id = Column(Integer, primary_key=True, autoincrement=True) 
    otp = Column(String(4), nullable=False, comment="One-time password for verification")
    phone_number = Column(String(15), nullable=False, comment="Phone number associated with the OTP")
    expires_at = Column(DateTime, nullable=False, comment="Expiry time for the OTP")
    used = Column(Boolean, default=False, comment="Indicates if the OTP has been used")
    created_at = Column(DateTime, default=func.now(), comment="Timestamp when the OTP was created")
    used_at = Column(DateTime, onupdate=func.now())

