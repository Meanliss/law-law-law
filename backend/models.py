"""
Pydantic Models for API
"""

from pydantic import BaseModel
from typing import List, Dict, Optional


class QuestionRequest(BaseModel):
    question: str
    use_advanced: bool = True


class TimingInfo(BaseModel):
    """Performance timing breakdown"""
    total_ms: float
    search_ms: float
    generation_ms: float
    status: str  # "success" or "rejected"


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]
    search_mode: str
    timing: Optional[TimingInfo] = None  # Performance metrics


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    total_chunks: int
