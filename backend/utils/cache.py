"""
Cache Management Module
"""

import os
import json
import hashlib
import pickle
from typing import List, Dict, Tuple
import faiss
from rank_bm25 import BM25Okapi


def get_data_hash(all_chunks: List[Dict]) -> str:
    """
    Generate MD5 hash from chunk content for cache validation
    
    Args:
        all_chunks: List of all document chunks
    
    Returns:
        MD5 hash string
    """
    content = json.dumps(
        [c.get('content', '')[:100] for c in all_chunks],
        sort_keys=True
    )
    return hashlib.md5(content.encode()).hexdigest()


def build_or_load_bm25(
    corpus: List[List[str]],
    data_hash: str,
    cache_path: str = 'cache/bm25_index.pkl'
) -> BM25Okapi:
    """
    Build or load BM25 index from cache with hash validation
    
    Args:
        corpus: Tokenized corpus
        data_hash: Current data hash
        cache_path: Path to cache file
    
    Returns:
        BM25 index
    """
    hash_path = cache_path + '.hash'
    
    # Check if cache exists and valid
    if os.path.exists(cache_path) and os.path.exists(hash_path):
        with open(hash_path, 'r') as f:
            saved_hash = f.read().strip()
        
        if saved_hash == data_hash:
            print('[INFO] BM25 cache hop le, dang tai tu cache...')
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        else:
            print('[WARN] Du lieu da thay doi, dang xay dung lai BM25 index...')
    else:
        print('[INFO] Chua co cache, dang xay dung BM25 index...')
    
    # Build new index
    bm25 = BM25Okapi(corpus)
    
    # Save to cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(bm25, f)
    with open(hash_path, 'w') as f:
        f.write(data_hash)
    
    print('[OK] Da luu BM25 index vao cache')
    return bm25


def build_or_load_faiss(
    chunks: List[Dict],
    data_hash: str,
    model,
    cache_path: str = 'cache/embeddings.pkl'
) -> Tuple[faiss.Index, any]:
    """
    Build or load FAISS index from cache with hash validation
    
    Args:
        chunks: List of document chunks
        data_hash: Current data hash
        model: Embedding model
        cache_path: Path to cache file
    
    Returns:
        Tuple of (FAISS index, embeddings)
    """
    hash_path = cache_path + '.hash'
    dimension_path = cache_path + '.dim'  # Track embedding dimension
    
    # Get current model dimension
    test_embedding = model.encode(["test"], convert_to_numpy=True)
    current_dim = test_embedding.shape[1]
    
    # Check if cache exists and valid
    if os.path.exists(cache_path) and os.path.exists(hash_path):
        with open(hash_path, 'r') as f:
            saved_hash = f.read().strip()
        
        # Check dimension compatibility
        rebuild_needed = False
        if os.path.exists(dimension_path):
            with open(dimension_path, 'r') as f:
                saved_dim = int(f.read().strip())
            if saved_dim != current_dim:
                print(f'[WARN] Embedding dimension changed: {saved_dim} → {current_dim}')
                print(f'       Rebuilding FAISS index with new dimension...')
                rebuild_needed = True
        
        if saved_hash == data_hash and not rebuild_needed:
            print('[INFO] FAISS cache hop le, dang tai tu cache...')
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    # Verify dimension
                    if data['index'].d == current_dim:
                        return data['index'], data['embeddings']
                    else:
                        print(f'[WARN] Cached index dimension mismatch, rebuilding...')
                        rebuild_needed = True
            except Exception as e:
                print(f'[ERROR] Failed to load cache: {e}')
                rebuild_needed = True
        
        if not rebuild_needed and saved_hash != data_hash:
            print('[WARN] Du lieu da thay doi, dang xay dung lai FAISS index...')
    else:
        print('[INFO] Chua co cache, dang tao FAISS index...')
    
    # Build new index
    contents = [chunk['content'] for chunk in chunks]
    print(f'[INFO] Dang embedding {len(contents)} chunks voi dimension {current_dim}...')
    embeddings = model.encode(contents, show_progress_bar=True, convert_to_numpy=True)
    
    faiss.normalize_L2(embeddings)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    # Save to cache with dimension info
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump({'index': index, 'embeddings': embeddings}, f)
    with open(hash_path, 'w') as f:
        f.write(data_hash)
    with open(dimension_path, 'w') as f:
        f.write(str(dimension))
    
    print(f'[OK] Da luu FAISS index vao cache (dimension: {dimension})')
    return index, embeddings
