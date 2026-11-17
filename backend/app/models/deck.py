"""
Deck and DeckConfig Database Models.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, BigInteger, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from ..db.session import Base


class DeckConfig(Base):
    __tablename__ = "deck_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    new_per_day = Column(Integer, default=20, nullable=False)
    reviews_per_day = Column(Integer, default=200, nullable=False)
    learning_steps = Column(JSON, default=[1.0, 10.0], nullable=False)
    relearning_steps = Column(JSON, default=[10.0], nullable=False)
    graduating_interval = Column(Integer, default=1, nullable=False)
    easy_interval = Column(Integer, default=4, nullable=False)
    starting_ease = Column(Integer, default=2500, nullable=False)
    fsrs_enabled = Column(Boolean, default=False, nullable=False)
    fsrs_params = Column(JSON, nullable=True)
    desired_retention = Column(Float, default=0.90, nullable=False)
    leech_threshold = Column(Integer, default=8, nullable=False)
    leech_action = Column(String(20), default="tag", nullable=False)


class Deck(Base):
    __tablename__ = "decks"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    config_id = Column(Integer, ForeignKey("deck_configs.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(String(2048), nullable=True)
    is_collapsed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")
