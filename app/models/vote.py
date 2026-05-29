from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='SET NULL'), nullable=True) # Optional linking to a post
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(100), nullable=False)
    is_multiple = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=False)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Simple relationship without explicit declarative mappings to avoid errors, we'll query directly if needed
    # options = relationship("VoteOption", back_populates="vote")

class VoteOption(Base):
    __tablename__ = "vote_options"

    id = Column(Integer, primary_key=True, index=True)
    vote_id = Column(Integer, ForeignKey('votes.id', ondelete='CASCADE'), nullable=False, index=True)
    text = Column(String(200), nullable=False)
    vote_count = Column(Integer, default=0)

class VoteCast(Base):
    __tablename__ = "vote_casts"

    id = Column(Integer, primary_key=True, index=True)
    vote_id = Column(Integer, ForeignKey('votes.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    option_id = Column(Integer, ForeignKey('vote_options.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # To prevent users from voting for the exact same option multiple times
        UniqueConstraint('user_id', 'option_id', name='uq_user_option_cast'),
    )
