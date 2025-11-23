
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import xu_ly_van_ban_phap_luat_json

def test_chunking():
    file_path = "data/domains/hon_nhan/raw/luat_hon_nhan_hopnhat.json"
    print(f"Testing chunking on: {file_path}")
    
    if not os.path.exists(file_path):
        print("File not found!")
        return

    chunks, source = xu_ly_van_ban_phap_luat_json(file_path)
    print(f"Source: {source}")
    print(f"Total chunks: {len(chunks)}")
    
    # Print first 5 chunks
    for i, chunk in enumerate(chunks[:5]):
        print(f"\n--- Chunk {i} ---")
        print(f"Source: {chunk['source']}")
        print(f"Content: {chunk['content'][:100]}...")
        print(f"Metadata: {chunk['metadata']}")

if __name__ == "__main__":
    test_chunking()
