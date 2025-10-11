"""
Search Module - BM25 + FAISS Hybrid Search
"""

import numpy as np
from collections import defaultdict
from typing import List, Dict
from config import BM25_WEIGHT, FAISS_WEIGHT


def advanced_hybrid_search(
    query: str,
    all_chunks: List[Dict],
    bm25_index,
    faiss_index,
    embedder,
    tokenize_fn,
    enhanced_decompose_fn,
    top_k: int = 8
) -> List[Dict]:
    """
    Tìm kiếm nâng cao với Intent Detection + Query Expansion
    
    Args:
        query: User query
        all_chunks: All document chunks
        bm25_index: BM25 index
        faiss_index: FAISS index
        embedder: Embedding model
        tokenize_fn: Tokenization function
        enhanced_decompose_fn: Query decomposition function
        top_k: Number of results
    
    Returns:
        List of relevant chunks
    """
    
    # Step 1: Intent check + Decompose
    decomp_result = enhanced_decompose_fn(query)
    
    # Step 2: Reject if not legal question
    if not decomp_result['should_process']:
        print(f'[WARN] Rejected query: {decomp_result["intent"]["reason"]}')
        return []
    
    sub_queries = decomp_result['sub_queries']
    print(f'[INFO] Decomposed into {len(sub_queries)} sub-queries: {sub_queries}')
    
    # Step 3: Hybrid search with sub-queries
    combined_scores = defaultdict(float)
    seen_chunks = set()
    
    for sub_q in sub_queries:
        # BM25 search
        query_tokens = tokenize_fn(sub_q)
        bm25_scores = bm25_index.get_scores(query_tokens)
        
        # FAISS search
        query_embedding = embedder.encode([sub_q], convert_to_numpy=True)
        import faiss as faiss_lib
        faiss_lib.normalize_L2(query_embedding)
        faiss_scores, faiss_indices = faiss_index.search(query_embedding, top_k * 2)
        
        # Combine scores
        for i, score in enumerate(bm25_scores):
            if i not in seen_chunks:
                combined_scores[i] += score * BM25_WEIGHT
        
        for idx, score in zip(faiss_indices[0], faiss_scores[0]):
            if idx != -1 and idx not in seen_chunks:
                combined_scores[idx] += score * FAISS_WEIGHT
        
        seen_chunks.update(range(len(all_chunks)))
    
    if not combined_scores:
        return []
    
    # Step 4: Rerank top candidates with semantic similarity
    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k * 2]
    
    candidates = [all_chunks[idx] for idx, _ in ranked]
    candidate_texts = [c['content'] for c in candidates]
    
    query_emb = embedder.encode([query], convert_to_numpy=True)
    candidate_embs = embedder.encode(candidate_texts, convert_to_numpy=True)
    
    query_norm = query_emb / np.linalg.norm(query_emb)
    candidate_norms = candidate_embs / np.linalg.norm(candidate_embs, axis=1, keepdims=True)
    semantic_scores = np.dot(candidate_norms, query_norm.T).flatten()
    
    reranked_indices = np.argsort(semantic_scores)[::-1][:top_k]
    results = [candidates[i] for i in reranked_indices]
    
    return results


def simple_search(
    query: str,
    all_chunks: List[Dict],
    bm25_index,
    faiss_index,
    embedder,
    tokenize_fn,
    top_k: int = 8
) -> List[Dict]:
    """
    Tìm kiếm đơn giản - BM25 + FAISS kết hợp
    
    Args:
        query: User query
        all_chunks: All document chunks
        bm25_index: BM25 index
        faiss_index: FAISS index
        embedder: Embedding model
        tokenize_fn: Tokenization function
        top_k: Number of results
    
    Returns:
        List of relevant chunks
    """
    # BM25 search
    query_tokens = tokenize_fn(query)
    bm25_scores = bm25_index.get_scores(query_tokens)
    
    # FAISS search
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    import faiss as faiss_lib
    faiss_lib.normalize_L2(query_embedding)
    faiss_scores, faiss_indices = faiss_index.search(query_embedding, top_k)
    
    # Combine scores
    combined_scores = defaultdict(float)
    for i, score in enumerate(bm25_scores):
        combined_scores[i] = score * BM25_WEIGHT
    
    for idx, score in zip(faiss_indices[0], faiss_scores[0]):
        if idx != -1:
            combined_scores[idx] += score * FAISS_WEIGHT
    
    # Sort and return top_k
    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results = [all_chunks[idx] for idx, _ in ranked]
    
    return results
