from sqlalchemy import Column, DateTime, func, UniqueConstraint, String, ForeignKey, Numeric, Date, Index
from db.postgres.base import Base
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID


class Fixes(Base):
    __tablename__ = "fixes"

    fix_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    meter_id = Column(UUID(as_uuid=True), ForeignKey("meters.meter_id", ondelete="SET NULL", name="fk_fixes_meter_id"), nullable=True)
    fix_date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    cost = Column(Numeric(15, 2, asdecimal=False), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_fixes_created_by"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_fixes_updated_by"), nullable=True)

    __table_args__ = (
        Index("ix_fixes_fix_date", "fix_date"),
    )
