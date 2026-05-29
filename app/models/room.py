from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=False)
    slug = Column(String(60), unique=True, nullable=False, index=True)
    ticker_code = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RoomMembership(Base):
    __tablename__ = "room_memberships"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
