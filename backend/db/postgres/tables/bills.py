from sqlalchemy import Column, DateTime, func, UniqueConstraint, String,Float, ForeignKey, Integer, Date, Integer, Index, Identity
from db.postgres.base import Base
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID


class Bills(Base):
    __tablename__ = "bills" 

    bill_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_number = Column(
        Integer,
        Identity(start=1),   
        nullable=False,
        unique=True,
    )
    meter_id = Column(UUID(as_uuid=True), ForeignKey(column="meters.meter_id", ondelete="SET NULL", name="fk_bills_meter_id"), nullable=True)

    amount_due_lbp = Column(Integer, nullable=False)
    amount_due_usd = Column(Float, nullable=False)

    total_paid_lbp = Column(Integer, nullable=False, default=0, server_default='0')
    total_paid_usd = Column(Float, nullable=False, default=0, server_default='0')

    due_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="unpaid")  # could be 'unpaid', 'partial', 'paid'

    blob_name = Column(String(255), nullable=True)

    rate_id = Column(UUID(as_uuid=True), ForeignKey("rates.rate_id", name="fk_bills_rate_id", ondelete="SET NULL"), nullable=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_bills_created_by"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_bills_updated_by"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('meter_id', 'due_date', name='uq_bill_identity'),
        Index("ix_bills_due_date", "due_date"),
        Index("ix_bills_status", "status"),
    )

    @property
    def amount_unpaid_lbp(self):
        return self.amount_due_lbp - self.total_paid_lbp

    @property
    def amount_unpaid_usd(self):
        return self.amount_due_usd - self.total_paid_usd


