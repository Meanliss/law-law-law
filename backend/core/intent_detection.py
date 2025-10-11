"""
Intent Detection Module
Phát hiện câu hỏi có liên quan đến pháp luật hay không
"""

import re
import hashlib
from typing import Dict
from config import (
    LEGAL_KEYWORDS,
    IRRELEVANT_PATTERNS,
    INTENT_KEYWORD_ACCEPT_THRESHOLD,
    INTENT_KEYWORD_UNCERTAIN_THRESHOLD,
    INTENT_CONFIDENCE_REJECT_THRESHOLD
)

# Global cache
_intent_cache = {}


def detect_intent_fast(query: str) -> Dict:
    """
    Layer 1+2: Rule-based + Keyword matching (Local, <10ms, 0 cost)
    
    Returns:
        {
            'is_legal': bool,
            'confidence': float (0-1),
            'reason': str,
            'needs_llm_check': bool
        }
    """
    # Check cache first
    cache_key = hashlib.md5(query.lower().encode()).hexdigest()
    if cache_key in _intent_cache:
        return _intent_cache[cache_key]
    
    query_lower = query.lower()
    
    # Layer 1: Rule-based - Reject obvious non-legal queries
    for pattern in IRRELEVANT_PATTERNS:
        if re.search(pattern, query_lower):
            result = {
                'is_legal': False,
                'confidence': 0.95,
                'reason': 'Chủ đề không liên quan đến pháp luật',
                'needs_llm_check': False
            }
            _intent_cache[cache_key] = result
            return result
    
    # Layer 2: Keyword scoring
    primary_matches = sum(1 for kw in LEGAL_KEYWORDS['primary'] if kw in query_lower)
    secondary_matches = sum(1 for kw in LEGAL_KEYWORDS['secondary'] if kw in query_lower)
    
    total_score = min(1.0, (primary_matches * 2 + secondary_matches) / 8.0)
    
    # Decision based on score
    if total_score >= INTENT_KEYWORD_ACCEPT_THRESHOLD:
        result = {
            'is_legal': True,
            'confidence': min(0.95, 0.7 + total_score * 0.3),
            'reason': f'Phát hiện {primary_matches} từ khóa chính, {secondary_matches} từ khóa phụ',
            'needs_llm_check': False
        }
    elif total_score >= INTENT_KEYWORD_UNCERTAIN_THRESHOLD:
        result = {
            'is_legal': True,
            'confidence': 0.5,
            'reason': 'Không chắc chắn, cần kiểm tra LLM',
            'needs_llm_check': True
        }
    else:
        result = {
            'is_legal': False,
            'confidence': 0.8,
            'reason': 'Không phát hiện từ khóa pháp luật',
            'needs_llm_check': False
        }
    
    _intent_cache[cache_key] = result
    return result


def detect_intent_llm(query: str, gemini_lite_model) -> Dict:
    """
    Layer 3: LLM-based detection using Gemini Flash Lite (fast, cheap)
    
    Args:
        query: User query
        gemini_lite_model: Gemini lite model instance
    
    Returns:
        Intent detection result
    """
    try:
        prompt = f"""Phân loại câu hỏi: "{query}"

Câu hỏi có liên quan đến PHÁP LUẬT VIỆT NAM không?

Trả lời theo format:
LEGAL: YES hoặc NO
CONFIDENCE: 0.XX
REASON: lý do ngắn gọn

Ví dụ:
LEGAL: YES
CONFIDENCE: 0.95
REASON: Hỏi về luật hôn nhân

LEGAL: NO
CONFIDENCE: 0.90
REASON: Hỏi về nấu ăn"""
        
        response = gemini_lite_model.generate_content(prompt)
        text = response.text.strip()
        
        print(f'[DEBUG] LLM Raw Response: {text}')
        
        # Parse response
        is_legal = False
        confidence = 0.5
        reason = 'Unknown'
        
        # Extract LEGAL field
        legal_match = re.search(r'LEGAL:\s*(YES|NO)', text, re.IGNORECASE)
        if legal_match:
            is_legal = legal_match.group(1).upper() == 'YES'
        else:
            # Fallback
            if 'YES' in text.upper() and 'NO' not in text.upper().split('YES')[0]:
                is_legal = True
            elif 'NO' in text.upper() and 'YES' not in text.upper().split('NO')[0]:
                is_legal = False
        
        # Extract CONFIDENCE
        conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', text, re.IGNORECASE)
        if conf_match:
            confidence = float(conf_match.group(1))
        else:
            conf_fallback = re.search(r'\b0\.\d+\b', text)
            if conf_fallback:
                confidence = float(conf_fallback.group(0))
        
        # Extract REASON
        reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if reason_match:
            reason = reason_match.group(1).strip()
        else:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                reason = lines[-1][:100]
        
        result = {
            'is_legal': is_legal,
            'confidence': min(0.98, confidence),
            'reason': reason[:100],
            'needs_llm_check': False
        }
        
        print(f'[DEBUG] Parsed result: {result}')
        return result
        
    except Exception as e:
        print(f'[ERROR] LLM intent detection failed: {e}')
        return {
            'is_legal': True,
            'confidence': 0.4,
            'reason': f'LLM error, fallback to accept',
            'needs_llm_check': False
        }


def enhanced_decompose_query(question: str, gemini_lite_model) -> Dict:
    """
    Intent detection + Smart decomposition
    
    Args:
        question: User question
        gemini_lite_model: Gemini lite model instance
    
    Returns:
        {
            'sub_queries': List[str],
            'intent': dict,
            'should_process': bool,
            'method': str
        }
    """
    from .query_expansion import decompose_query_smart
    
    # Step 1: Intent detection
    intent = detect_intent_fast(question)
    print(f'[INTENT] Fast: is_legal={intent["is_legal"]}, conf={intent["confidence"]:.2f}')
    
    # Step 2: LLM check if needed
    if intent['needs_llm_check']:
        print('[INTENT] Calling LLM Lite...')
        intent = detect_intent_llm(question, gemini_lite_model)
        print(f'[INTENT] LLM Lite: is_legal={intent["is_legal"]}, conf={intent["confidence"]:.2f}')
    
    # Step 3: Safety override for strong indicators
    strong_legal_indicators = ['kết hôn', 'ly hôn', 'luật', 'điều', 'khoản', 'quy định', 'lao động', 'đất đai']
    if not intent['is_legal'] and any(ind in question.lower() for ind in strong_legal_indicators):
        print('[INTENT] Override: Strong legal indicator detected')
        intent['is_legal'] = True
        intent['confidence'] = 0.85
        intent['reason'] = 'Override: Phát hiện từ khóa pháp luật mạnh'
    
    # Step 4: Reject if not legal
    if not intent['is_legal'] and intent['confidence'] >= INTENT_CONFIDENCE_REJECT_THRESHOLD:
        return {
            'sub_queries': [],
            'intent': intent,
            'should_process': False,
            'method': 'rejected'
        }
    
    # Step 5: Smart decomposition with expansion
    decompose_result = decompose_query_smart(question, gemini_lite_model)
    
    return {
        'sub_queries': decompose_result['sub_queries'],
        'intent': intent,
        'should_process': decompose_result['should_process'],
        'method': decompose_result['method']
    }


def get_cache_size() -> int:
    """Get current intent cache size"""
    return len(_intent_cache)


def clear_cache():
    """Clear intent cache"""
    global _intent_cache
    _intent_cache = {}
