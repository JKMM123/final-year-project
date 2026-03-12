from sqlalchemy import Column, DateTime, ForeignKey, func, UniqueConstraint, Integer
from db.postgres.base import Base
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID


class Packages(Base):
    __tablename__ = "packages"

    package_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amperage = Column(Integer, nullable=False, unique=True)
    activation_fee = Column(Integer, nullable=False)
    fixed_fee = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_packages_created_by"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_packages_updated_by"), nullable=True)

    __table_args__ = (
        UniqueConstraint('amperage', name='uq_amperage'),
    )