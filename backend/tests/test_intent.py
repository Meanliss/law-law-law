"""
Test Intent Detection
Chạy: python test_intent.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock imports to test logic
import re
import hashlib

LEGAL_KEYWORDS = {
    'primary': [
        'luật', 'pháp luật', 'quy định', 'điều', 'khoản', 'điểm', 
        'nghị định', 'thông tư', 'bộ luật', 'quyền', 'nghĩa vụ',
        'hợp đồng', 'tài sản', 'kết hôn', 'ly hôn', 'lao động',
        'đất đai', 'hình sự', 'dân sự', 'tố tụng', 'hành chính',
        'đấu thầu', 'chuyển giao công nghệ', 'vi phạm', 'xử phạt',
        'tuổi', 'độ tuổi'
    ],
    'secondary': [
        'khiếu nại', 'tố cáo', 'án', 'tòa', 'bồi thường', 'trách nhiệm',
        'hợp pháp', 'quy trình', 'đăng ký', 'cấp phép', 'thuế', 'phí',
        'lệ phí', 'thủ tục', 'điều kiện', 'tiêu chuẩn', 'quyết định',
        'gia đình', 'con cái', 'cha mẹ', 'vợ chồng', 'di sản'
    ]
}

IRRELEVANT_PATTERNS = [
    r'\b(thời tiết|bóng đá|game|phim|nhạc|ăn uống|du lịch)\b',
    r'\b(nấu ăn|công thức|món ăn|quán|nhà hàng|cafe)\b',
    r'\b(bệnh|thuốc|chữa|triệu chứng|y tế)\b',
    r'\b(laptop|điện thoại|máy tính|cấu hình|smartphone)\b',
    r'\b(toán|vật lý|hóa học|sinh học|lịch sử|địa lý)\b',
]

intent_cache = {}

def detect_intent_fast(query: str) -> dict:
    cache_key = hashlib.md5(query.lower().encode()).hexdigest()
    if cache_key in intent_cache:
        return intent_cache[cache_key]
    
    query_lower = query.lower()
    
    # Layer 1: Rule-based
    for pattern in IRRELEVANT_PATTERNS:
        if re.search(pattern, query_lower):
            result = {
                'is_legal': False,
                'confidence': 0.95,
                'reason': 'Chủ đề không liên quan đến pháp luật',
                'needs_llm_check': False
            }
            intent_cache[cache_key] = result
            return result
    
    # Layer 2: Keyword scoring
    primary_matches = sum(1 for kw in LEGAL_KEYWORDS['primary'] if kw in query_lower)
    secondary_matches = sum(1 for kw in LEGAL_KEYWORDS['secondary'] if kw in query_lower)
    
    total_score = min(1.0, (primary_matches * 2 + secondary_matches) / 8.0)
    
    if total_score >= 0.4:
        result = {
            'is_legal': True,
            'confidence': min(0.95, 0.7 + total_score * 0.3),
            'reason': f'Phát hiện {primary_matches} từ khóa chính, {secondary_matches} từ khóa phụ',
            'needs_llm_check': False
        }
    elif total_score >= 0.15:
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
    
    intent_cache[cache_key] = result
    return result


# Test cases
test_queries = [
    # Should ACCEPT (legal questions)
    ("Quy định về độ tuổi kết hôn?", True),
    ("Tuổi kết hôn ở Việt Nam?", True),
    ("Điều kiện mua bán đất đai?", True),
    ("Quyền lợi người lao động?", True),
    ("Luật hôn nhân quy định thế nào?", True),
    ("Thủ tục ly hôn như thế nào?", True),
    
    # Should REJECT (non-legal)
    ("Hôm nay thời tiết thế nào?", False),
    ("Món ăn ngon ở Hà Nội?", False),
    ("Cách chữa cảm cúm?", False),
    ("Laptop nào tốt nhất?", False),
    ("Công thức nấu phở?", False),
]

print("=" * 80)
print("TESTING INTENT DETECTION")
print("=" * 80)

passed = 0
failed = 0

for query, expected_legal in test_queries:
    result = detect_intent_fast(query)
    status = "✅ PASS" if result['is_legal'] == expected_legal else "❌ FAIL"
    
    if result['is_legal'] == expected_legal:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status}")
    print(f"Query: {query}")
    print(f"Expected: {'LEGAL' if expected_legal else 'NOT LEGAL'}")
    print(f"Got: {'LEGAL' if result['is_legal'] else 'NOT LEGAL'} (conf={result['confidence']:.2f})")
    print(f"Reason: {result['reason']}")
    print(f"Needs LLM: {result['needs_llm_check']}")

print("\n" + "=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed")
print(f"Accuracy: {passed/(passed+failed)*100:.1f}%")
print("=" * 80)
