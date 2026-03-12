from sqlalchemy import Column, DateTime, func, UniqueConstraint, String, ForeignKey, Integer
from db.postgres.base import Base
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID


class Meters(Base):
    __tablename__ = "meters"

    meter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_full_name = Column(String(255), nullable=False)
    customer_phone_number = Column(String(20), nullable=False)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.area_id", name="fk_meters_area_id"), nullable=False)
    address = Column(String(255), nullable=True)
    initial_reading = Column(Integer, nullable=True)
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.package_id", name="fk_meters_package_id"), nullable=False)
    package_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    blob_name = Column(String(500), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_meters_created_by"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_meters_updated_by"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('customer_full_name', 'customer_phone_number', 'address', name='uq_customer_identity_address'),
)
    