import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.core.domain_manager import DomainManager
from backend.utils.tokenizer import tokenize_vi

def test_search():
    print("Initializing DomainManager...")
    dm = DomainManager()
    
    query = "điều kiện kết hôn"
    print(f"\nTesting search with query: '{query}'")
    
    results = dm.search(query, tokenize_vi, top_k=3)
    
    print(f"\nFound {len(results)} results:")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res.get('content')[:100]}... (Score: {res.get('score')})")

if __name__ == "__main__":
    test_search()
