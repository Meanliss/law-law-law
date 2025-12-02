
import sys
import os
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embedding import GeminiEmbedder
from config import EMBEDDING_MODEL, GOOGLE_API_KEY

def test_gemini_embedder():
    print(f"Testing GeminiEmbedder with model: {EMBEDDING_MODEL}")
    if GOOGLE_API_KEY:
        print(f"API Key loaded: {GOOGLE_API_KEY[:5]}...{GOOGLE_API_KEY[-5:]}")
    else:
        print("❌ API Key NOT loaded!")
    
    try:
        embedder = GeminiEmbedder(EMBEDDING_MODEL)
        
        # Test single string
        text = "Xin chào, đây là một câu thử nghiệm."
        print(f"\nEncoding single string: '{text}'")
        embedding = embedder.encode(text)
        
        print(f"Shape: {embedding.shape}")
        print(f"Type: {type(embedding)}")
        print(f"First 5 values: {embedding[0][:5]}")
        
        if embedding.shape[1] == 768:
            print("✅ Dimension check passed (768)")
        else:
            print(f"❌ Dimension check failed: {embedding.shape[1]}")
            
        # Test list of strings
        texts = ["Câu 1", "Câu 2", "Câu 3"]
        print(f"\nEncoding list of {len(texts)} strings")
        embeddings = embedder.encode(texts)
        
        print(f"Shape: {embeddings.shape}")
        
        if embeddings.shape[0] == 3 and embeddings.shape[1] == 768:
            print("✅ Batch encoding check passed")
        else:
            print(f"❌ Batch encoding check failed: {embeddings.shape}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_embedder()
