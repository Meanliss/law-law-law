"""
Query Expansion Module
Mở rộng query với các khía cạnh liên quan
"""

import re
from typing import List, Dict
from config import QUERY_EXPANSION_RULES


def expand_legal_query(query: str) -> List[str]:
    """
    Mở rộng query pháp luật với các khía cạnh liên quan
    
    Examples:
        "độ tuổi kết hôn" → ["độ tuổi kết hôn", "điều kiện kết hôn", "quy định kết hôn"]
        "quyền lợi lao động" → ["quyền lợi lao động", "nghĩa vụ lao động", "hợp đồng lao động"]
    
    Args:
        query: Original user query
    
    Returns:
        List of expanded queries (max 3)
    """
    query_lower = query.lower()
    expanded = [query]  # Always include original
    
    # Check each rule
    for pattern, expansions in QUERY_EXPANSION_RULES.items():
        if re.search(pattern, query_lower):
            # Add related queries (avoid duplicates)
            for exp in expansions:
                if exp.lower() not in [q.lower() for q in expanded]:
                    expanded.append(exp)
            break  # Only use first matching rule
    
    # Limit to top 3 most relevant
    return expanded[:3]


def decompose_query_smart(question: str, gemini_lite_model) -> Dict:
    """
    Decompose query with semantic expansion
    Kết hợp rule-based expansion VÀ LLM decomposition
    
    Args:
        question: User question
        gemini_lite_model: Gemini lite model instance
    
    Returns:
        {
            'sub_queries': List[str],
            'method': str,
            'should_process': bool
        }
    """
    
    # Step 1: Rule-based expansion (local, fast)
    expanded_queries = expand_legal_query(question)
    
    print(f'[DECOMPOSE] Expanded: {expanded_queries}')
    
    # Step 2: Nếu có expansion rules match, dùng luôn
    if len(expanded_queries) > 1:
        return {
            'sub_queries': expanded_queries,
            'method': 'rule_based_expansion',
            'should_process': True
        }
    
    # Step 3: Fallback to LLM decomposition cho câu phức tạp
    try:
        prompt = f"""Phân tích câu hỏi thành các TRUY VẤN PHÁP LÝ để tìm kiếm trong văn bản luật.

CÂU HỎI: "{question}"

YÊU CẦU:
1. Trừu tượng hóa - BỎ TÊN RIÊNG (người, công ty, địa danh cụ thể)
2. Tập trung vào KHÁI NIỆM PHÁP LÝ và HÀNH VI
3. Mỗi truy vấn phải NGẮN GỌN, DỄ TÌM KIẾM trong văn bản luật
4. Tránh câu dài, chỉ giữ yếu tố pháp lý cốt lõi
5. Trả về 2-4 truy vấn, mỗi dòng 1 truy vấn

VÍ DỤ:
Input: "Anh A mua nhà của bà B nhưng không làm sổ đỏ, có hợp pháp không?"
Output:
1. Mua bán nhà đất không làm sổ đỏ có hợp pháp không?
2. Quy định về đăng ký quyền sở hữu nhà đất
3. Hậu quả pháp lý khi không đăng ký quyền sử dụng đất

BẮT ĐẦU:"""
        
        # ✅ Use LOW temperature for consistent, focused decomposition
        response = gemini_lite_model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,  # Slightly higher for variety in phrasing
                'top_p': 0.85,
                'top_k': 30
            }
        )
        text = response.text.strip()
        
        # Parse numbered list
        sub_queries = []
        for line in text.split('\n'):
            line = line.strip()
            # Match: "1. ...", "- ...", etc
            match = re.match(r'^[\d\-\*\.]+\s*(.+)$', line)
            if match:
                q = match.group(1).strip()
                if q and q not in sub_queries and len(q) > 5:
                    sub_queries.append(q)
        
        if not sub_queries:
            sub_queries = [question]
        
        print(f'[DECOMPOSE] LLM result: {sub_queries}')
        
        return {
            'sub_queries': sub_queries[:4],  # Limit to 4
            'method': 'llm_decomposition',
            'should_process': True
        }
        
    except Exception as e:
        print(f'[ERROR] Decomposition failed: {e}')
        return {
            'sub_queries': [question],
            'method': 'fallback',
            'should_process': True
        }
