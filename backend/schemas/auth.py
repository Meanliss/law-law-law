"""
Pydantic Models for API
"""


from pydantic import BaseModel, EmailStr, validator
from typing import List, Dict, Optional
import re


# ============================================================================
# Auth Models
# ============================================================================

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

    @validator('username')
    def username_must_be_english(cls, v):
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('Username must contain only English letters and numbers')
        return v
    
class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# ============================================================================
# Q&A Models
# ============================================================================
class QuestionRequest(BaseModel):
    question: str
    use_advanced: bool = True
    model_mode: str = "detail"  # "summary" or "detail"
    chat_history: Optional[List[Dict[str, str]]] = []  # ✅ Lịch sử chat từ client


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
    domain_id: Optional[str] = None  # ✅ Add domain_id for correct mapping
    article_num: Optional[str] = None


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]  # Original sources for backward compatibility
    pdf_sources: Optional[List[PDFSource]] = []  # Enhanced PDF metadata
    search_mode: Optional[str] = None  # Legacy field (deprecated)
    search_method: Optional[str] = None  # New field: domain_based_detail, domain_based_summary, etc.
    timing: Optional[TimingInfo] = None  # Performance metrics
    timing_ms: Optional[float] = None  # Simple timing for domain-based


class SuggestQuestionsRequest(BaseModel):
    """Request for generating suggested questions"""
    question: str
    answer: str
    max_questions: int = 3


class SuggestQuestionsResponse(BaseModel):
    """Response with suggested questions"""
    questions: List[str]


class FeedbackRequest(BaseModel):
    """User feedback on answer quality"""
    query: str
    answer: str
    context: List[Dict[str, str]]  # Sources used
    status: str  # "like" or "dislike"
    comment: Optional[str] = None  # Optional user comment


class FeedbackResponse(BaseModel):
    """Feedback submission response"""
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    total_chunks: int
