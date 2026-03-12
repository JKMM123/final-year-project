from sqlalchemy import Column, DateTime, func, String, Index, ForeignKey, Date, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base



class Readings(Base):
    __tablename__ = "readings"
    
    reading_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    meter_id = Column(UUID(as_uuid=True), ForeignKey("meters.meter_id", ondelete="SET NULL", name="fk_readings_meter_id"), nullable=True)
    reading_date = Column(Date, nullable=False)
    current_reading = Column(Integer, nullable=False)
    previous_reading = Column(Integer, nullable=False)
    usage = Column(Integer, nullable=False)
    reading_sequence = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default='pending')
    
    blob_name = Column(String, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_readings_created_by"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_readings_updated_by"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_readings_meter_id', 'meter_id'),
        Index('ix_readings_reading_date', 'reading_date'),
        Index('ix_readings_status', 'status'),
    )
