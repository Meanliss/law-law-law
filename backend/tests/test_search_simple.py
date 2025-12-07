import sys
import os

# Add current directory to path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from core.domain_manager import DomainManager
from utils.tokenizer import tokenize_vi

def test_search():
    print("Initializing DomainManager...")
    dm = DomainManager()
    
    query = "điều kiện kết hôn"
    print(f"\nTesting search with query: '{query}'")
    
    # Debug embedding dimension
    emb = dm.embedder.encode([query])
    print(f"Embedding shape: {emb.shape}")
    
    results = dm.search(query, tokenize_vi, top_k=3)
    
    print(f"\nFound {len(results)} results:")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res.get('content')[:100]}... (Score: {res.get('score')})")

if __name__ == "__main__":
    test_search()
