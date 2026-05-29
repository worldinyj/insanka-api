from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    # Use string for UUID in SQLite compatibility or use a dedicated UUID type
    token = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    inviter_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(254), nullable=False, index=True)
    status = Column(String(10), default='pending') # pending, accepted, expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
