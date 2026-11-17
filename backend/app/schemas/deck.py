"""
Deck Pydantic Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class DeckCountSchema(BaseModel):
    new: int = 0
    learning: int = 0
    due: int = 0


class DeckTreeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    is_collapsed: bool = False
    total_cards: int = 0
    counts: DeckCountSchema = DeckCountSchema()
    children: List["DeckTreeResponse"] = []

    class Config:
        from_attributes = True


class DeckCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    config_id: Optional[int] = None


class DeckUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_collapsed: Optional[bool] = None
    config_id: Optional[int] = None
