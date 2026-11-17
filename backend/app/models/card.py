"""
Note, Card, and Revlog Database Models.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    SmallInteger,
    BigInteger,
    ForeignKey,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from ..db.session import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notetype_id = Column(BigInteger, ForeignKey("notetypes.id", ondelete="RESTRICT"), nullable=False, index=True)
    guid = Column(String(255), nullable=False)
    fields = Column(JSON, nullable=False)   # List of strings
    tags = Column(JSON, default=[], nullable=False)     # List of tag strings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    notetype = relationship("Notetype", back_populates="notes")
    cards = relationship("Card", back_populates="note", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    note_id = Column(BigInteger, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    deck_id = Column(BigInteger, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True)
    ord = Column(Integer, nullable=False, default=0)
    type = Column(SmallInteger, default=0, nullable=False)    # 0=New, 1=Learn, 2=Review, 3=Relearn
    queue = Column(SmallInteger, default=0, nullable=False)   # 0=New, 1=Learn, 2=Review, -1=Suspended
    due = Column(BigInteger, default=0, nullable=False)
    ivl = Column(Integer, default=0, nullable=False)          # Interval
    factor = Column(Integer, default=2500, nullable=False)    # Ease factor * 10
    reps = Column(Integer, default=0, nullable=False)
    lapses = Column(Integer, default=0, nullable=False)
    left = Column(Integer, default=0, nullable=False)
    flags = Column(SmallInteger, default=0, nullable=False)   # 0=None, 1=Red, 2=Orange, 3=Green, 4=Blue, etc.
    fsrs_stability = Column(Float, nullable=True)
    fsrs_difficulty = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    note = relationship("Note", back_populates="cards")
    deck = relationship("Deck", back_populates="cards")
    revlogs = relationship("Revlog", back_populates="card", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_cards_study_queue", "user_id", "deck_id", "queue", "due"),
    )


class Revlog(Base):
    __tablename__ = "revlogs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(BigInteger, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(SmallInteger, nullable=False)             # 1=Again, 2=Hard, 3=Good, 4=Easy
    new_ivl = Column(Integer, nullable=False)
    last_ivl = Column(Integer, nullable=False)
    factor = Column(Integer, nullable=False)
    time_taken_ms = Column(Integer, default=0, nullable=False)
    review_type = Column(SmallInteger, default=1, nullable=False)  # 0=Learn, 1=Review, 4=Quiz
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    card = relationship("Card", back_populates="revlogs")
