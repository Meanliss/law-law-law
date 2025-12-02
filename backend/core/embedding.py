"""
Gemini Embedding Wrapper
Compatible with SentenceTransformer interface for easy integration
"""

import numpy as np
import google.generativeai as genai
from typing import List, Union
import time
from config import GOOGLE_API_KEY, EMBEDDING_MODEL

# Configure API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class GeminiEmbedder:
    """
    Wrapper for Gemini Embedding API to be compatible with SentenceTransformer
    """
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        
    def encode(self, sentences: Union[str, List[str]], batch_size: int = 32, show_progress_bar: bool = False, convert_to_numpy: bool = True) -> np.ndarray:
        """
        Encode sentences using Gemini Embedding API
        
        Args:
            sentences: Single string or list of strings
            batch_size: Batch size for API calls (Gemini has limits)
            show_progress_bar: (Ignored, kept for compatibility)
            convert_to_numpy: Whether to return numpy array (default True)
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(sentences, str):
            sentences = [sentences]
            
        embeddings = []
        
        # Process in batches
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]
            try:
                # Gemini embedding-001 supports batching
                # content format: list of strings
                result = genai.embed_content(
                    model=self.model_name,
                    content=batch,
                    task_type="retrieval_document" # Optimized for retrieval
                )
                
                # result['embedding'] is a list of lists
                if 'embedding' in result:
                    embeddings.extend(result['embedding'])
                else:
                    # Fallback or error handling
                    print(f"⚠️ Warning: No embedding returned for batch {i}")
                    # Append zero vectors or handle error? 
                    # For now, append zeros to keep shape matches if possible, or skip
                    # But skipping breaks index alignment. Let's raise error.
                    raise ValueError("No embedding returned from Gemini API")
                    
                # Rate limit handling (simple sleep)
                time.sleep(0.1) 
                
            except Exception as e:
                print(f"❌ Error encoding batch {i}: {e}")
                # Retry logic could go here
                # For now, re-raise
                raise e
                
        result_array = np.array(embeddings)
        
        if convert_to_numpy:
            return result_array
        return result_array.tolist()
