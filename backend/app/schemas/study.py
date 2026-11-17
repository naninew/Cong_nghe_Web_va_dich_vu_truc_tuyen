"""
Card, Study, Game, and Import/Export Pydantic Schemas.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


# --- Card Schemas ---
class CardRenderedView(BaseModel):
    front_html: str
    back_html: str
    css: str


class CleanCardView(BaseModel):
    term: str
    phonetic: Optional[str] = ""
    meaning: str
    examples: List[str] = []
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    level_tag: Optional[str] = ""
    notes: Optional[str] = ""


class CardDetailResponse(BaseModel):
    id: int
    deck_id: int
    deck_name: str
    note_id: int
    ord: int
    type: int
    queue: int
    due: int
    ivl: int
    factor: int
    reps: int
    lapses: int
    fields: Dict[str, str]
    tags: List[str]
    rendered: CardRenderedView
    clean_data: Optional[CleanCardView] = None
    next_intervals: Dict[str, str]

    class Config:
        from_attributes = True


# --- Study Schemas ---
class StudyQueueResponse(BaseModel):
    card: Optional[CardDetailResponse] = None
    remaining_counts: Dict[str, int] = {"new": 0, "learning": 0, "due": 0}


class CardAnswerRequest(BaseModel):
    card_id: int
    rating: int  # 1=Again, 2=Hard, 3=Good, 4=Easy
    time_taken_ms: int = 0


class CardAnswerResponse(BaseModel):
    card_id: int
    rating: int
    new_interval: int
    due: int
    xp_awarded: int
    streak_days: int


class CustomIncreaseRequest(BaseModel):
    deck_id: Optional[int] = None
    amount: int = 10


class CustomIncreaseResponse(BaseModel):
    success: bool
    added_cards: int
    remaining_new: int


# --- Game Schemas ---
class QuizOption(BaseModel):
    key: str  # "A", "B", "C", "D"
    label: str


class QuizQuestion(BaseModel):
    question_id: str
    card_id: int
    prompt: str
    context_hint: Optional[str] = ""
    audio_file: Optional[str] = None
    direction: str = "front_to_back"
    options: List[QuizOption]
    # correct key is kept on server for evaluation


class StartGameRequest(BaseModel):
    deck_id: Optional[int] = None
    mode: str = "classic"  # "classic", "speed_blitz", "survival", "lapsed_only"
    direction: str = "front_to_back"  # "front_to_back", "back_to_front", "audio_listening", "custom"
    total_questions: int = 10
    question_type: str = "vocab"
    srs_sync: bool = True
    timer_seconds: int = 15
    question_field: Optional[str] = None
    answer_field: Optional[str] = None
    hint_field: Optional[str] = None


class StartGameResponse(BaseModel):
    session_id: str
    deck_id: int
    total_questions: int
    questions: List[QuizQuestion]


class SubmitGameAnswerRequest(BaseModel):
    session_id: str
    card_id: int
    selected_key: str
    response_time_ms: int = 0


class SubmitGameAnswerResponse(BaseModel):
    is_correct: bool
    correct_key: str
    points_earned: int
    combo_xp: int
    current_combo: int
    explanation: str
    srs_updated: bool
    srs_grade: str


class FinishGameRequest(BaseModel):
    session_id: str


class FinishGameResponse(BaseModel):
    session_id: str
    score: int
    xp_earned: int
    total_questions: int
    correct_count: int
    accuracy_percent: float
    duration_seconds: int


# --- Import/Export Schemas ---
class ImportJobStatusResponse(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress_percent: int
    total_cards: int = 0
    imported_cards: int = 0
    imported_decks: int = 0
    imported_notetypes: int = 0
    error_message: Optional[str] = None
