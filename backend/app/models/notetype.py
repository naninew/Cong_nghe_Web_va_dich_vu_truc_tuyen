"""
Notetype, Field, and Template Models.
"""

from sqlalchemy import Column, String, Integer, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from ..db.session import Base


class Notetype(Base):
    __tablename__ = "notetypes"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    css = Column(Text, default="", nullable=False)
    latex_pre = Column(Text, nullable=True)
    latex_post = Column(Text, nullable=True)

    fields = relationship("NotetypeField", back_populates="notetype", cascade="all, delete-orphan", order_by="NotetypeField.ord")
    templates = relationship("NotetypeTemplate", back_populates="notetype", cascade="all, delete-orphan", order_by="NotetypeTemplate.ord")
    notes = relationship("Note", back_populates="notetype")


class NotetypeField(Base):
    __tablename__ = "notetype_fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notetype_id = Column(BigInteger, ForeignKey("notetypes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    ord = Column(Integer, nullable=False, default=0)

    notetype = relationship("Notetype", back_populates="fields")


class NotetypeTemplate(Base):
    __tablename__ = "notetype_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notetype_id = Column(BigInteger, ForeignKey("notetypes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    ord = Column(Integer, nullable=False, default=0)
    qfmt = Column(Text, nullable=False)
    afmt = Column(Text, nullable=False)

    notetype = relationship("Notetype", back_populates="templates")
