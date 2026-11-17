"""
Game Session and Answers Database Models.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..db.session import Base


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    deck_id = Column(BigInteger, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True)
    game_type = Column(String(50), default="4-option-quiz", nullable=False)
    total_questions = Column(Integer, default=10, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    answers = relationship("GameSessionAnswer", back_populates="session", cascade="all, delete-orphan")


class GameSessionAnswer(Base):
    __tablename__ = "game_session_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(BigInteger, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(String(255), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, default=0, nullable=False)

    session = relationship("GameSession", back_populates="answers")
