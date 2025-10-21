"""
Intent Detection & Query Refinement Module
Sử dụng LLM Lite để:
1. Phát hiện câu hỏi có liên quan đến pháp luật
2. Tinh chỉnh câu hỏi (query refinement)
"""

import re
from typing import Dict, Tuple
from config import INTENT_CONFIDENCE_REJECT_THRESHOLD

# Global cache
_intent_cache = {}


def detect_intent_and_refine(query: str, gemini_lite_model) -> Tuple[Dict, str]:
    """
    Sử dụng LLM Lite để:
    1. Phát hiện intent (câu hỏi có liên quan pháp luật không)
    2. Refine câu hỏi (chuẩn hóa, làm rõ)
    
    Args:
        query: User query
        gemini_lite_model: Gemini lite model instance
    
    Returns:
        (intent_result, refined_query)
        intent_result: {'is_legal': bool, 'confidence': float, 'reason': str}
        refined_query: Câu hỏi đã được tinh chỉnh
    """
    try:
        prompt = f"""Phân tích câu hỏi: "{query}"

NHIỆM VỤ 1: Câu hỏi có liên quan đến PHÁP LUẬT VIỆT NAM không?
- Pháp luật bao gồm: Luật, Nghị định, Thông tư, Quy định về hôn nhân, lao động, đất đai, hình sự, dân sự, hành chính, v.v.

NHIỆM VỤ 2: Tinh chỉnh câu hỏi (nếu là câu hỏi pháp luật):
- Chuẩn hóa ngôn ngữ (sửa lỗi chính tả, ngữ pháp)
- Làm rõ ý nghĩa (thêm bối cảnh nếu cần)
- Giữ nguyên ý chính, ngắn gọn

FORMAT TRẢ LỜI (bắt buộc):
LEGAL: YES hoặc NO
CONFIDENCE: 0.XX (từ 0.00 đến 1.00)
REASON: lý do ngắn gọn (1 câu)
REFINED: câu hỏi đã tinh chỉnh (nếu LEGAL=YES) hoặc NONE (nếu LEGAL=NO)

VÍ DỤ 1 (Câu hỏi pháp luật):
LEGAL: YES
CONFIDENCE: 0.95
REASON: Hỏi về điều kiện kết hôn theo luật
REFINED: Độ tuổi kết hôn theo quy định của Luật Hôn nhân và Gia đình Việt Nam?

VÍ DỤ 2 (Không phải pháp luật):
LEGAL: NO
CONFIDENCE: 0.90
REASON: Câu hỏi về nấu ăn, không liên quan pháp luật
REFINED: NONE

BẮT ĐẦU PHÂN TÍCH:"""
        
        response = gemini_lite_model.generate_content(prompt)
        text = response.text.strip()
        
        print(f'[INTENT+REFINE] LLM Response:\n{text}')
        
        # Parse response
        is_legal = False
        confidence = 0.5
        reason = 'Unknown'
        refined_query = query  # Fallback: giữ nguyên câu gốc
        
        # Extract LEGAL field
        legal_match = re.search(r'LEGAL:\s*(YES|NO)', text, re.IGNORECASE)
        if legal_match:
            is_legal = legal_match.group(1).upper() == 'YES'
        
        # Extract CONFIDENCE
        conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', text, re.IGNORECASE)
        if conf_match:
            confidence = min(0.98, float(conf_match.group(1)))
        
        # Extract REASON
        reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if reason_match:
            reason = reason_match.group(1).strip()[:100]
        
        # Extract REFINED query
        refined_match = re.search(r'REFINED:\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
        if refined_match:
            refined_text = refined_match.group(1).strip()
            # Nếu là câu hỏi pháp luật và có refined query (không phải NONE)
            if is_legal and refined_text.upper() != 'NONE' and len(refined_text) > 5:
                refined_query = refined_text
                print(f'[REFINED] Original: "{query}" → Refined: "{refined_query}"')
        
        intent_result = {
            'is_legal': is_legal,
            'confidence': confidence,
            'reason': reason
        }
        
        print(f'[INTENT] is_legal={is_legal}, confidence={confidence:.2f}, reason={reason}')
        
        return intent_result, refined_query
        
    except Exception as e:
        print(f'[ERROR] LLM intent detection failed: {e}')
        # Fallback: Accept với confidence thấp
        return {
            'is_legal': True,
            'confidence': 0.4,
            'reason': 'LLM error, fallback to accept'
        }, query


def enhanced_decompose_query(question: str, gemini_lite_model, gemini_flash_model=None, use_advanced=False) -> Dict:
    """
    Intent detection + Query refinement + Smart decomposition
    
    Args:
        question: User question
        gemini_lite_model: Gemini lite model instance (for Fast mode)
        gemini_flash_model: Gemini flash model instance (for Quality mode) - OPTIONAL
        use_advanced: True = Quality mode (dùng Flash cho decompose), False = Fast mode (dùng Lite)
    
    Returns:
        {
            'sub_queries': List[str],
            'intent': dict,
            'should_process': bool,
            'method': str,
            'refined_query': str  # ✅ Câu hỏi đã tinh chỉnh
        }
    """
    from .query_expansion import decompose_query_smart
    
    # ✅ Step 1: Intent detection + Query refinement (luôn dùng Lite - nhanh)
    print(f'\n[INTENT+REFINE] Analyzing: "{question}"')
    intent, refined_query = detect_intent_and_refine(question, gemini_lite_model)
    
    # ✅ Step 2: Reject if not legal
    if not intent['is_legal'] and intent['confidence'] >= INTENT_CONFIDENCE_REJECT_THRESHOLD:
        print(f'[INTENT] REJECTED: {intent["reason"]}')
        return {
            'sub_queries': [],
            'intent': intent,
            'should_process': False,
            'method': 'rejected',
            'refined_query': question  # Không refine nếu bị reject
        }
    
    # ✅ Step 3: Smart decomposition
    # Quality mode: Dùng Flash (reasoning tốt hơn, tách câu phức tạp chính xác hơn)
    # Fast mode: Dùng Lite (nhanh hơn)
    decompose_model = gemini_flash_model if (use_advanced and gemini_flash_model) else gemini_lite_model
    model_name = "Flash (Quality)" if (use_advanced and gemini_flash_model) else "Lite (Fast)"
    
    print(f'[DECOMPOSE] Using {model_name} model for query: "{refined_query}"')
    decompose_result = decompose_query_smart(refined_query, decompose_model)
    
    return {
        'sub_queries': decompose_result['sub_queries'],
        'intent': intent,
        'should_process': decompose_result['should_process'],
        'method': decompose_result['method'],
        'refined_query': refined_query  # ✅ Trả về câu hỏi đã tinh chỉnh
    }


def get_cache_size() -> int:
    """Get current intent cache size"""
    return len(_intent_cache)


def clear_cache():
    """Clear intent cache"""
    global _intent_cache
    _intent_cache = {}
