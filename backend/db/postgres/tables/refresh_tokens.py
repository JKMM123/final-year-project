from sqlalchemy import Column, DateTime, func, String, Index, UniqueConstraint, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base


class RefreshTokens(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_refresh_tokens_user_id"), nullable=True)
    token_hash = Column(String, nullable=False)
    device_id = Column(String, nullable=False) 
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', 'token_hash', name='uq_refresh_tokens_user_device'),
        Index('idx_refresh_tokens_user_id', 'user_id'),
        Index('idx_refresh_tokens_device_id', 'device_id'),
        Index('idx_refresh_tokens_revoked', 'revoked'),
    )

