from sqlalchemy import Column, DateTime, ForeignKey, func, String, Index, UniqueConstraint, Boolean, CheckConstraint, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4
from db.postgres.base import Base

class Templates(Base):
    __tablename__ = "templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    message = Column(String, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_templates_created_by"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_templates_updated_by"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_templates_name"),
    )
    