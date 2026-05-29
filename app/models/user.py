from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    hashed_pw = Column(Text, nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    level = Column(SmallInteger, default=1)
    total_points = Column(Integer, default=0, index=True)
    role = Column(String(10), default='member')
    status = Column(String(10), default='pending')
    invited_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    login_fail_count = Column(SmallInteger, default=0)
    lockout_until = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint('level BETWEEN 1 AND 5', name='chk_level'),
        CheckConstraint("role IN ('member','editor','admin')", name='chk_role'),
        CheckConstraint("status IN ('pending','approved','suspended','banned')", name='chk_status'),
        CheckConstraint('total_points >= 0', name='chk_points'),
    )
