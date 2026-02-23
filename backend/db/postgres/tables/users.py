from sqlalchemy import Column, DateTime, func, String, Index, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base


class Users(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_users_created_by"), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_users_updated_by"), nullable=True)

    __table_args__ = (
        UniqueConstraint('username', name='uq_users_username'),
        UniqueConstraint('phone_number', name='uq_users_phone_number'),
        Index('idx_users_username', 'username'),
        Index('idx_users_phone_number', 'phone_number'),
        Index('idx_users_role', 'role'),
    )