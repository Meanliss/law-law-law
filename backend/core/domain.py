"""
Domain class - Lazy loading legal domain with separate indices
"""
import json
import pickle
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer


class Domain:
    """
    Lazy-loading domain:
    - Metadata: Always in memory (tiny)
    - Indices: Load on first query (lazy)
    - Chunks: Load on-demand from JSONL
    """
    
    def __init__(self, domain_id: str, embedder: SentenceTransformer):
        self.domain_id = domain_id
        self.domain_dir = Path(f"data/domains/{domain_id}")
        self.embedder = embedder
        
        # ✅ Always load metadata (tiny)
        metadata_path = self.domain_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'domain_id': domain_id,
                'name': domain_id,
                'chunk_count': 0
            }
        
        # ❌ Don't load indices yet (lazy)
        self._bm25_index = None
        self._faiss_index = None
        self._tokenized_chunks = None
        self._chunks_cache = {}  # Cache loaded chunks
        self._loaded = False
    
    @property
    def domain_name(self) -> str:
        """Get domain display name"""
        return self.metadata.get('domain_name', self.domain_id)
    
    @property
    def chunk_count(self) -> int:
        """Get total number of chunks (from metadata)"""
        return self.metadata.get('total_chunks', self.metadata.get('chunk_count', 0))
    
    @property
    def is_loaded(self) -> bool:
        """Check if indices are loaded"""
        return self._loaded
    
    def load_indices(self):
        """Load BM25 and FAISS indices into memory"""
        if self._loaded:
            return
        
        print(f"📂 Loading indices for domain: {self.domain_id}", flush=True)
        
        # Load BM25
        bm25_path = self.domain_dir / "bm25.pkl"
        if bm25_path.exists():
            with open(bm25_path, 'rb') as f:
                self._bm25_index = pickle.load(f)
        
        # Load FAISS
        faiss_path = self.domain_dir / "faiss.index"
        if faiss_path.exists():
            self._faiss_index = faiss.read_index(str(faiss_path))
        
        # Load tokenized chunks
        tokens_path = self.domain_dir / "tokens.pkl"
        if tokens_path.exists():
            with open(tokens_path, 'rb') as f:
                self._tokenized_chunks = pickle.load(f)
        
        self._loaded = True
        self._loaded = True
        print(f"✅ Domain '{self.domain_id}' loaded: {self.metadata.get('total_chunks', 0)} chunks", flush=True)
    
    @property
    def bm25_index(self):
        """Lazy load BM25 index"""
        if self._bm25_index is None:
            self.load_indices()
        return self._bm25_index
    
    @property
    def faiss_index(self):
        """Lazy load FAISS index"""
        if self._faiss_index is None:
            self.load_indices()
        return self._faiss_index
    
    @property
    def tokenized_chunks(self):
        """Lazy load tokenized chunks"""
        if self._tokenized_chunks is None:
            self.load_indices()
        return self._tokenized_chunks
    
    def get_chunk(self, idx: int) -> Dict:
        """Load chunk from JSONL (with caching)"""
        if idx in self._chunks_cache:
            return self._chunks_cache[idx]
        
        # Read specific line from JSONL
        chunks_path = self.domain_dir / "chunks.jsonl"
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == idx:
                    chunk = json.loads(line)
                    self._chunks_cache[idx] = chunk
                    return chunk
        
        raise IndexError(f"Chunk {idx} not found in domain {self.domain_id}")
    
    def get_chunks(self, indices: List[int]) -> List[Dict]:
        """Batch load chunks (optimized)"""
        needed_indices = set(indices) - set(self._chunks_cache.keys())
        
        if needed_indices:
            # Read JSONL and cache needed chunks
            chunks_path = self.domain_dir / "chunks.jsonl"
            found_count = 0
            with open(chunks_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i in needed_indices:
                        chunk = json.loads(line)
                        self._chunks_cache[i] = chunk
                        found_count += 1
                        if found_count == len(needed_indices):
                            break
        
        return [self._chunks_cache[i] for i in indices if i in self._chunks_cache]
    
    def search(self, query: str, tokenize_fn, top_k: int = 8) -> List[Dict]:
        """Hybrid search within this domain"""
        
        # Ensure indices are loaded
        self.load_indices()
        
        if self._bm25_index is None or self._faiss_index is None:
            print(f"⚠️ Domain '{self.domain_id}' has no indices", flush=True)
            return []
        
        # Tokenize query
        tokenized_query = tokenize_fn(query)
        
        # ===== BM25 Search =====
        bm25_scores = self._bm25_index.get_scores(tokenized_query)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k*2]
        
        # ===== FAISS Search =====
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)
        faiss_distances, faiss_indices = self._faiss_index.search(
            query_embedding.astype('float32'), top_k*2
        )
        
        # ===== Normalize and Merge Scores =====
        from config import BM25_WEIGHT, FAISS_WEIGHT
        combined_scores = {}
        
        # BM25 normalization
        if len(bm25_top_indices) > 0:
            bm25_subset = bm25_scores[bm25_top_indices]
            bm25_min, bm25_max = bm25_subset.min(), bm25_subset.max()
            bm25_range = bm25_max - bm25_min
            
            if bm25_range > 0:
                for idx in bm25_top_indices:
                    normalized = (bm25_scores[idx] - bm25_min) / bm25_range
                    combined_scores[int(idx)] = normalized * BM25_WEIGHT
        
        # FAISS contribution
        for rank, idx in enumerate(faiss_indices[0]):
            distance = faiss_distances[0][rank]
            similarity = 1 / (1 + distance)
            combined_scores[int(idx)] = combined_scores.get(int(idx), 0) + similarity * FAISS_WEIGHT
        
        # ===== Sort and Load Top Chunks =====
        sorted_indices = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, score in sorted_indices[:top_k]]
        
        # ✅ Only load top chunks from disk
        results = self.get_chunks(top_indices)
        
        # Add scores and domain info
        for i, (idx, score) in enumerate(sorted_indices[:len(results)]):
            if i < len(results):
                results[i]['score'] = float(score)
                results[i]['domain_name'] = self.metadata.get('name', self.domain_id)
                results[i]['domain_id'] = self.domain_id
        
        return results
    
    def unload(self):
        """Free memory (call when domain not needed)"""
        self._bm25_index = None
        self._faiss_index = None
        self._tokenized_chunks = None
        self._chunks_cache.clear()
        self._loaded = False
        print(f"💨 Domain '{self.domain_id}' unloaded from memory", flush=True)
