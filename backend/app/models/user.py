"""
User Database Model.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Date, DateTime
from ..db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    display_name = Column(String(255), nullable=False)
    avatar_url = Column(String(1024), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    streak_days = Column(Integer, default=0, nullable=False)
    last_study_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
