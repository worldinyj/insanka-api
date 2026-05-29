from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class PointLog(Base):
    __tablename__ = "point_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = Column(Integer, nullable=False) # Positive or negative
    reason = Column(String(50), nullable=False) # e.g. "post_created", "signup", "comment_created"
    target_id = Column(Integer, nullable=True) # ID of the post/comment associated with the point
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
