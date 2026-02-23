from sqlalchemy import Column, DateTime,Date, ForeignKey, func, String, Index,Numeric, UniqueConstraint, Float, Integer, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base





class Payments(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.bill_id", ondelete="SET NULL", name="fk_payments_bill_id"), nullable=True)
    meter_id = Column(UUID(as_uuid=True), ForeignKey("meters.meter_id", ondelete="SET NULL", name="fk_payments_meter_id"), nullable=True)

    amount_lbp = Column(Integer, nullable=False)
    amount_usd = Column(Float, nullable=False)
    
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_payments_created_by"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_payments_updated_by"), nullable=True)

    __table_args__ = (
        Index('ix_payments_bill_id', 'bill_id'),
        Index('ix_payments_meter_id', 'meter_id'),
    )

    