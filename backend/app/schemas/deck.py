"""
Deck Pydantic Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


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


def _check_steps(v: Optional[List[float]]) -> Optional[List[float]]:
    if v is not None and any(s <= 0 for s in v):
        raise ValueError("steps must be positive minutes")
    return v


def _check_fsrs_params(v: Optional[List[float]]) -> Optional[List[float]]:
    if v is not None and len(v) != 19:
        raise ValueError("fsrs_params must contain exactly 19 FSRS-5 weights")
    return v


class DeckConfigSchema(BaseModel):
    """Scheduling options of a deck (Anki "deck options")."""
    id: Optional[int] = None
    name: str = "Default"
    new_per_day: int = Field(20, ge=0, le=9999)
    reviews_per_day: int = Field(200, ge=0, le=99999)
    learning_steps: List[float] = [1.0, 10.0]      # minutes
    relearning_steps: List[float] = [10.0]         # minutes, [] = no relearning
    graduating_interval: int = Field(1, ge=1)
    easy_interval: int = Field(4, ge=1)
    starting_ease: int = Field(2500, ge=1300)
    fsrs_enabled: bool = False
    fsrs_params: Optional[List[float]] = None      # 19 FSRS-5 weights, None = defaults
    desired_retention: float = Field(0.90, ge=0.70, le=0.99)
    leech_threshold: int = Field(8, ge=1)
    leech_action: str = Field("tag", pattern="^(tag|suspend)$")

    @field_validator("learning_steps", "relearning_steps")
    @classmethod
    def validate_steps(cls, v):
        return _check_steps(v)

    @field_validator("fsrs_params")
    @classmethod
    def validate_fsrs_params(cls, v):
        return _check_fsrs_params(v)


class DeckConfigUpdateRequest(BaseModel):
    """Partial update: only provided fields are changed."""
    new_per_day: Optional[int] = Field(None, ge=0, le=9999)
    reviews_per_day: Optional[int] = Field(None, ge=0, le=99999)
    learning_steps: Optional[List[float]] = None
    relearning_steps: Optional[List[float]] = None
    graduating_interval: Optional[int] = Field(None, ge=1)
    easy_interval: Optional[int] = Field(None, ge=1)
    starting_ease: Optional[int] = Field(None, ge=1300)
    fsrs_enabled: Optional[bool] = None
    fsrs_params: Optional[List[float]] = None
    desired_retention: Optional[float] = Field(None, ge=0.70, le=0.99)
    leech_threshold: Optional[int] = Field(None, ge=1)
    leech_action: Optional[str] = Field(None, pattern="^(tag|suspend)$")

    @field_validator("learning_steps", "relearning_steps")
    @classmethod
    def validate_steps(cls, v):
        return _check_steps(v)

    @field_validator("fsrs_params")
    @classmethod
    def validate_fsrs_params(cls, v):
        return _check_fsrs_params(v)
