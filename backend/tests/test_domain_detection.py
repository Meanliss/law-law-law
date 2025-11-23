
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.intent_detection import detect_domain_with_llm, enhanced_decompose_query

def test_domain_detection_with_context():
    print("\n--- Testing Domain Detection with Context ---")
    
    # Mock dependencies
    mock_gemini = MagicMock()
    mock_domain_manager = MagicMock()
    
    # Setup mock domain manager
    mock_domain_manager.list_domains.return_value = [
        {'id': 'lao_dong', 'name': 'Luật Lao động'},
        {'id': 'hon_nhan', 'name': 'Luật Hôn nhân'}
    ]
    
    # Case 1: Short query without context (Should fail or be ambiguous)
    print("Case 1: Short query without context")
    mock_gemini.generate_content.return_value.text = "DOMAIN: NONE"
    domain = detect_domain_with_llm("hợp đồng vô hiệu", mock_gemini, mock_domain_manager)
    print(f"Result: {domain}")
    
    # Case 2: Short query WITH context (Should succeed)
    print("\nCase 2: Short query WITH context")
    mock_gemini.generate_content.return_value.text = "DOMAIN: lao_dong"
    domain = detect_domain_with_llm(
        "hợp đồng vô hiệu", 
        mock_gemini, 
        mock_domain_manager,
        context="Hợp đồng lao động của chị S bị vô hiệu khi nào?"
    )
    print(f"Result: {domain}")
    assert domain == 'lao_dong', "Should detect 'lao_dong' with context"

def test_fallback_logic():
    print("\n--- Testing Fallback Logic in Decompose ---")
    
    # Mock dependencies
    mock_gemini_lite = MagicMock()
    mock_domain_manager = MagicMock()
    
    # Setup mocks
    mock_domain_manager.list_domains.return_value = [{'id': 'lao_dong', 'name': 'Luật Lao động'}]
    mock_domain_manager.detect_domain_from_keywords.return_value = None
    
    # Mock LLM responses
    # 1. Intent detection: YES
    # 2. Domain detection for original query: lao_dong
    # 3. Domain detection for sub-query: NONE (to trigger fallback)
    
    def side_effect(prompt):
        mock_response = MagicMock()
        if "Đây có phải câu hỏi pháp luật" in prompt:
            mock_response.text = '{"is_legal": true, "confidence": 0.9, "reason": "test"}'
        elif "CÂU HỎI CẦN PHÂN LOẠI" in prompt:
            if "Hợp đồng lao động của chị S" in prompt: # Original query
                mock_response.text = "DOMAIN: lao_dong"
            else: # Sub-query
                mock_response.text = "DOMAIN: NONE"
        return mock_response

    mock_gemini_lite.generate_content.side_effect = side_effect
    
    # Mock decompose_query_smart to return sub-queries
    with MagicMock() as mock_decompose:
        # We need to patch the import inside the function, but for now let's just mock the return of the internal call if possible
        # Since we can't easily patch the internal import without `unittest.patch`, we will rely on the fact that 
        # we are testing the logic *around* it. 
        # Actually, `enhanced_decompose_query` imports `decompose_query_smart`. 
        # We will mock the module in sys.modules
        
        sys.modules['core.query_expansion'] = MagicMock()
        sys.modules['core.query_expansion'].decompose_query_smart.return_value = {
            'sub_queries': ['điều kiện vô hiệu'],
            'should_process': True,
            'method': 'decompose'
        }
        
        result = enhanced_decompose_query(
            "Hợp đồng lao động của chị S bị vô hiệu khi nào?",
            mock_gemini_lite,
            domain_manager=mock_domain_manager
        )
        
        print("Sub-questions:")
        for sq in result['sub_questions']:
            print(f"- {sq['question']} [Domain: {sq['domain']}]")
            
        # Check if fallback worked
        sub_q = result['sub_questions'][1] # Index 0 is original, 1 is decomposed
        assert sub_q['domain'] == 'lao_dong', "Fallback logic failed! Should inherit 'lao_dong'"

if __name__ == "__main__":
    test_domain_detection_with_context()
    test_fallback_logic()
