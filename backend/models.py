"""
Pydantic Models for API
"""

from pydantic import BaseModel
from typing import List, Dict, Optional


class QuestionRequest(BaseModel):
    question: str
    use_advanced: bool = True
    model_mode: str = "quality"  # "fast" or "quality"


class TimingInfo(BaseModel):
    """Performance timing breakdown"""
    total_ms: float
    search_ms: float
    generation_ms: float
    status: str  # "success" or "rejected"


class PDFSource(BaseModel):
    """PDF source with location information"""
    pdf_file: str
    page_num: Optional[int] = None
    content: str
    highlight_text: str  # Text to highlight in PDF
    json_file: Optional[str] = None
    article_num: Optional[str] = None


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]  # Original sources for backward compatibility
    pdf_sources: Optional[List[PDFSource]] = []  # Enhanced PDF metadata
    search_mode: str
    timing: Optional[TimingInfo] = None  # Performance metrics


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    total_chunks: int
