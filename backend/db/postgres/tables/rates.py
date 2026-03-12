from sqlalchemy import Column, DateTime, ForeignKey, func, Integer, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base


class Rates(Base):
    __tablename__ = "rates"

    rate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    coastal_kwh_rate = Column(Integer, nullable=False)
    mountain_kwh_rate = Column(Integer, nullable=False)
    fixed_sub_hours = Column(Integer, nullable=False)
    fixed_sub_rate = Column(Integer, nullable=False)
    dollar_rate = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_rates_created_by"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_rates_updated_by"), nullable=True)


    