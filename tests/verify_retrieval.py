import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.search import reciprocal_rank_fusion
from core.document_processor import xu_ly_van_ban_phap_luat_json
import json

def test_rrf():
    print("Testing RRF...")
    # Rank lists: [0, 1, 2] and [0, 2, 1]
    # Chunk 0 is 1st in both.
    # Chunk 1 is 2nd in list 1, 3rd in list 2.
    # Chunk 2 is 3rd in list 1, 2nd in list 2.
    
    ranks = [
        [0, 1, 2],
        [0, 2, 1]
    ]
    
    scores = reciprocal_rank_fusion(ranks, k=1) # Use small k for easy math
    # Score 0 = 1/(1+1) + 1/(1+1) = 0.5 + 0.5 = 1.0
    # Score 1 = 1/(1+2) + 1/(1+3) = 0.33 + 0.25 = 0.58
    # Score 2 = 1/(1+3) + 1/(1+2) = 0.25 + 0.33 = 0.58
    
    print(f"Scores: {dict(scores)}")
    assert scores[0] > scores[1]
    assert abs(scores[1] - scores[2]) < 0.001
    print("[OK] RRF Test Passed")

def test_contextual_chunking():
    print("\nTesting Contextual Chunking...")
    
    # Create a dummy JSON file
    dummy_data = {
        "nguon": "Luat Test",
        "du_lieu": [
            {
                "dieu_so": "1",
                "tieu_de": "Dieu 1",
                "mo_ta": "Noi dung dieu 1",
                "khoan": [
                    {
                        "khoan_so": "1",
                        "noi_dung": "Noi dung khoan 1",
                        "diem": [
                            {
                                "diem_so": "a",
                                "noi_dung": "Noi dung diem a"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    with open("test_law.json", "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)
        
    chunks, source = xu_ly_van_ban_phap_luat_json("test_law.json")
    
    # Check Clause Chunk
    # Should contain: "Dieu 1 Noi dung dieu 1\nNoi dung khoan 1"
    # Wait, the logic is: if clause has points, it doesn't create a chunk for the clause itself (unless I misread).
    # Let's check the code.
    # "Process clause without points" -> if not khoan.get('diem'): chunks.append(...)
    # So if it has points, it skips the clause chunk and goes to points.
    
    # Check Point Chunk
    # Should contain: "Dieu 1 Noi dung dieu 1\nNoi dung khoan 1\nNoi dung diem a"
    
    point_chunk = chunks[0]
    print(f"Point Chunk Content:\n{point_chunk['content']}")
    
    expected = "Dieu 1 Noi dung dieu 1\nNoi dung khoan 1\nNoi dung diem a"
    assert point_chunk['content'] == expected
    print("[OK] Contextual Chunking Test Passed")
    
    os.remove("test_law.json")

if __name__ == "__main__":
    test_rrf()
    test_contextual_chunking()
