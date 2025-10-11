"""
Core modules for Legal Q&A System
"""

from .intent_detection import detect_intent_fast, detect_intent_llm, enhanced_decompose_query
from .query_expansion import expand_legal_query, decompose_query_smart
from .search import advanced_hybrid_search, simple_search
from .generation import generate_answer
from .document_processor import xu_ly_van_ban_phap_luat_json

__all__ = [
    'detect_intent_fast',
    'detect_intent_llm',
    'enhanced_decompose_query',
    'expand_legal_query',
    'decompose_query_smart',
    'advanced_hybrid_search',
    'simple_search',
    'generate_answer',
    'xu_ly_van_ban_phap_luat_json',
]
