from sqlalchemy import Column, DateTime, func, String, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from db.postgres.base import Base


class Areas(Base):
    __tablename__ = "areas"
    
    area_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    area_name = Column(String, nullable=False)
    elevation = Column(Integer, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_areas_created_by"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey(column="users.user_id", ondelete="SET NULL", name="fk_areas_updated_by"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    
    __table_args__ = (
    UniqueConstraint('area_name', name='uq_area_name'),  
)