"""
Intent Detection & Query Refinement Module
Sử dụng LLM Lite để:
1. Phát hiện câu hỏi có liên quan đến pháp luật
2. Tinh chỉnh câu hỏi (query refinement)
"""

import re
import json
from typing import Dict, Tuple
from config import INTENT_CONFIDENCE_REJECT_THRESHOLD

# Global cache
_intent_cache = {}


def detect_domain_with_llm(question: str, gemini_lite_model, domain_manager) -> str:
    """
    Use LLM to detect which legal domain a question belongs to
    
    Args:
        question: Sub-question to classify
        gemini_lite_model: Gemini lite model instance
        domain_manager: DomainManager instance
    
    Returns:
        domain_id (str) or None if cannot detect
    """
    try:
        # Get available domains
        domains_info = []
        for domain_id in domain_manager.list_domains():
            # ✅ Fix: Access domain object correctly (not dict)
            domain_obj = domain_manager.domains.get(domain_id)
            if domain_obj:
                domain_name = domain_obj.domain_name
            else:
                domain_name = domain_id
            domains_info.append(f"- {domain_id}: {domain_name}")
        
        domains_list = "\n".join(domains_info)
        
        prompt = f"""Bạn là chuyên gia phân loại câu hỏi pháp luật.

CÂU HỎI: "{question}"

CÁC LĨNH VỰC PHÁP LUẬT:
{domains_list}

NHIỆM VỤ: Xác định câu hỏi thuộc lĩnh vực pháp luật nào.

QUY TẮC:
1. Chỉ trả về MỘT domain_id phù hợp nhất
2. Nếu không rõ ràng, trả về "NONE"
3. Chỉ trả về domain_id, KHÔNG giải thích

FORMAT TRẢLỜI:
DOMAIN: <domain_id hoặc NONE>

BẮT ĐẦU PHÂN LOẠI:"""

        response = gemini_lite_model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse domain
        domain_match = re.search(r'DOMAIN:\s*(\w+)', text, re.IGNORECASE)
        if domain_match:
            domain = domain_match.group(1).strip()
            if domain.upper() != 'NONE' and domain in domain_manager.list_domains():
                return domain
        
        return None
        
    except Exception as e:
        print(f'[ERROR] LLM domain detection failed: {e}', flush=True)
        return None


def detect_intent_and_refine(query: str, gemini_lite_model, previous_context: str = None) -> tuple:
    """
    Sử dụng LLM Lite để:
    1. Phát hiện intent (câu hỏi có liên quan pháp luật không)
    2. Refine câu hỏi (chuẩn hóa, làm rõ)
    
    Args:
        query: User query
        gemini_lite_model: Gemini lite model instance
        previous_context: Context từ 2 câu hỏi/trả lời trước (optional)
    
    Returns:
        (intent_result, refined_query)
        intent_result: {'is_legal': bool, 'confidence': float, 'reason': str}
        refined_query: Câu hỏi đã được tinh chỉnh
    """
    try:
        # ✅ Thêm context section nếu có
        context_section = ""
        if previous_context:
            context_section = f"""
════════════════════════════════════════
📚 NGỮ CẢNH HỘI THOẠI TRƯỚC:
{previous_context}
════════════════════════════════════════

"""
        
        prompt = f"""{context_section}Phân tích câu hỏi: "{query}"

NHIỆM VỤ 1: Câu hỏi có liên quan đến PHÁP LUẬT VIỆT NAM không?
- Pháp luật bao gồm: Luật, Nghị định, Thông tư, Quy định về hôn nhân, lao động, đất đai, hình sự, dân sự, hành chính, v.v.
- ✅ NẾU CÓ NGỮ CẢNH PHÁP LUẬT TRƯỚC: Câu hỏi follow-up (như "còn trường hợp này thì sao?", "cảm ơn", "giải thích thêm") cũng được coi là câu hỏi pháp luật

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


def enhanced_decompose_query(question: str, gemini_lite_model, gemini_flash_model=None, use_advanced=False, domain_manager=None, previous_context: str = None) -> Dict:
    """
    Intent detection + Smart decomposition (with refinement) + Domain detection
    
    Args:
        question: User question (ORIGINAL - không refine trước)
        gemini_lite_model: Gemini lite model instance (for Fast mode)
        gemini_flash_model: Gemini flash model instance (for Quality mode) - OPTIONAL
        use_advanced: True = Quality mode (dùng Flash cho decompose), False = Fast mode (dùng Lite)
        domain_manager: DomainManager instance for domain detection - OPTIONAL
        previous_context: Context từ 2 câu hỏi/trả lời trước (optional)
    
    Returns:
        {
            'sub_questions': List[{'question': str, 'domain': str}],  # Includes ORIGINAL + decomposed (refined inside)
            'intent': dict,
            'should_process': bool,
            'method': str
        }
    """
    from .query_expansion import decompose_query_smart
    
    # ✅ Step 1: Intent detection ONLY (không refine riêng nữa)
    print(f'\n[INTENT] Checking if legal: "{question}"', flush=True)
    
    # Detect intent without refining (refine will be inside decompose)
    prompt = f"""Câu hỏi: "{question}"

Đây có phải câu hỏi pháp luật Việt Nam không?
- YES nếu hỏi về luật, quy định, quyền lợi, nghĩa vụ, thủ tục pháp lý
- NO nếu: chào hỏi, toán học, lập trình, nấu ăn, du lịch, giải trí, thể thao, v.v.

Trả lời JSON:
{{"is_legal": true/false, "confidence": 0.0-1.0, "reason": "..."}}"""
    
    try:
        response = gemini_lite_model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Parse JSON
        json_match = re.search(r'\{[^}]+\}', result_text)
        if json_match:
            intent = json.loads(json_match.group(0))
        else:
            intent = {'is_legal': True, 'confidence': 0.5, 'reason': 'Cannot parse, assume legal'}
    except Exception as e:
        print(f'[INTENT] Error: {e}', flush=True)
        intent = {'is_legal': True, 'confidence': 0.4, 'reason': 'LLM error, fallback to accept'}
    
    # ✅ Step 2: Reject if not legal
    if not intent['is_legal'] and intent['confidence'] >= INTENT_CONFIDENCE_REJECT_THRESHOLD:
        print(f'[INTENT] REJECTED: {intent["reason"]}', flush=True)
        return {
            'sub_questions': [],
            'intent': intent,
            'should_process': False,
            'method': 'rejected'
        }
    
    # ✅ Step 3: Smart decomposition (bao gồm cả refine + decompose)
    # Quality mode: Dùng Flash (reasoning tốt hơn, tách câu phức tạp chính xác hơn)
    # Fast mode: Dùng Lite (nhanh hơn)
    decompose_model = gemini_flash_model if (use_advanced and gemini_flash_model) else gemini_lite_model
    model_name = "Flash (Quality)" if (use_advanced and gemini_flash_model) else "Lite (Fast)"
    
    print(f'[DECOMPOSE+REFINE] Using {model_name} for: "{question}"', flush=True)
    decompose_result = decompose_query_smart(question, decompose_model)  # ✅ Truyền original question
    
    # ✅ Step 4: Build sub_questions with original + decomposed (refined)
    sub_questions = []
    
    # Detect domain for original question
    original_domain = None
    if domain_manager:
        original_domain = detect_domain_with_llm(question, gemini_lite_model, domain_manager)
        if not original_domain:
            original_domain = domain_manager.detect_domain_from_keywords(question)
        if original_domain:
            print(f'🎯 [DOMAIN] Original query → {original_domain}', flush=True)
    
    # Add ORIGINAL question as FIRST sub-question (không refine)
    sub_questions.append({
        'question': question,  # ✅ Giữ nguyên câu hỏi gốc
        'domain': original_domain,
        'is_original': True  # Mark as original
    })
    
    # Then add decomposed (refined) sub-questions
    for sub_query in decompose_result['sub_queries']:
        # Skip if sub_query giống hệt original (avoid duplication)
        if sub_query.strip().lower() == question.strip().lower():
            continue
            
        sub_q_obj = {
            'question': sub_query,  # ✅ Đây là câu đã refined + decomposed
            'domain': None,
            'is_original': False
        }
        
        # Detect domain for sub-question
        if domain_manager:
            # Use LLM to detect domain (more accurate than keywords)
            detected_domain = detect_domain_with_llm(sub_query, gemini_lite_model, domain_manager)
            if detected_domain:
                sub_q_obj['domain'] = detected_domain
                print(f'🎯 [DOMAIN-LLM] "{sub_query}" → {detected_domain}', flush=True)
            else:
                # Fallback to keyword matching
                detected_domain = domain_manager.detect_domain_from_keywords(sub_query)
                if detected_domain:
                    sub_q_obj['domain'] = detected_domain
                    print(f'🔑 [DOMAIN-KEYWORD] "{sub_query}" → {detected_domain}', flush=True)
        
        sub_questions.append(sub_q_obj)
    
    return {
        'sub_questions': sub_questions,  # ✅ Original + refined/decomposed
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
