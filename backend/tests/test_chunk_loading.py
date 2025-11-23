
import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.domain import Domain

def test_chunk_loading_fix():
    print("🧪 Testing chunk loading fix...")
    
    # Mock embedder
    mock_embedder = MagicMock()
    
    # Initialize domain (using 'lao_dong' as it exists)
    domain = Domain('lao_dong', mock_embedder)
    
    # Check if domain dir exists
    if not domain.domain_dir.exists():
        print(f"❌ Domain directory not found: {domain.domain_dir}")
        return
    
    # 1. Simulate a populated cache
    # We'll manually add some dummy entries to the cache to simulate previous searches
    print("📝 Populating cache with dummy data...")
    for i in range(100):
        domain._chunks_cache[i] = {"id": f"dummy_{i}", "content": "dummy"}
        
    initial_cache_size = len(domain._chunks_cache)
    print(f"ℹ️ Initial cache size: {initial_cache_size}")
    
    # 2. Request NEW indices that are NOT in the cache
    # We know chunks.jsonl has lines. Let's pick some indices that are likely valid but not 0-99.
    # Article 49 was around line 142. Let's try loading index 142.
    target_indices = [142, 143]
    
    print(f"🔍 Requesting indices: {target_indices}")
    
    # This call would fail with the old logic because len(cache) (100) >= len(indices) (2)
    chunks = domain.get_chunks(target_indices)
    
    # 3. Verify results
    print(f"📦 Retrieved {len(chunks)} chunks")
    
    if len(chunks) == len(target_indices):
        print("✅ Success! All requested chunks were loaded.")
        for chunk in chunks:
            print(f"   - Chunk ID: {chunk.get('id')}")
            print(f"   - Content snippet: {chunk.get('content', '')[:50]}...")
            
        # Verify cache size increased
        final_cache_size = len(domain._chunks_cache)
        print(f"ℹ️ Final cache size: {final_cache_size}")
        if final_cache_size == initial_cache_size + len(target_indices):
             print("✅ Cache size updated correctly.")
        else:
             print(f"⚠️ Cache size mismatch. Expected {initial_cache_size + len(target_indices)}, got {final_cache_size}")
             
    else:
        print(f"❌ Failed! Expected {len(target_indices)} chunks, got {len(chunks)}.")
        print("   This indicates the bug is still present.")

if __name__ == "__main__":
    test_chunk_loading_fix()
