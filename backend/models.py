"""
Pydantic Models for API
"""

from pydantic import BaseModel
from typing import List, Dict


class QuestionRequest(BaseModel):
    question: str
    use_advanced: bool = True


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]
    search_mode: str


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    total_chunks: int
