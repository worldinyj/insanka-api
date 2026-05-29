from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class MembershipProof(Base):
    __tablename__ = "membership_proofs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    image_url = Column(Text, nullable=False)
    status = Column(String(10), default='pending') # pending, approved, rejected
    reviewer_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    auto_delete_at = Column(DateTime(timezone=True), nullable=True)
