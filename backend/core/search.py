"""
Search Module - BM25 + FAISS Hybrid Search with LLM Re-ranking
"""

import re
import numpy as np
from collections import defaultdict
from typing import List, Dict
from config import BM25_WEIGHT, FAISS_WEIGHT


def rerank_with_llm(query: str, candidates: List[Dict], gemini_model, top_k: int = 5) -> List[Dict]:
    """
    Sử dụng LLM để re-rank các candidate documents
    Đánh giá mức độ liên quan chính xác hơn (chỉ cho Quality mode)
    
    Args:
        query: User query
        candidates: List of candidate chunks
        gemini_model: Gemini model (Flash hoặc Lite)
        top_k: Number of results to return
    
    Returns:
        Re-ranked list of chunks
    """
    try:
        # Tạo prompt cho LLM đánh giá
        docs_text = ""
        for i, doc in enumerate(candidates):
            # Giới hạn độ dài mỗi document để tránh prompt quá dài
            content = doc['content'][:300]
            docs_text += f"\n[{i}] {content}...\n"
        
        prompt = f"""Bạn là chuyên gia pháp lý Việt Nam. Đánh giá mức độ liên quan của các đoạn văn bản pháp luật với câu hỏi.

CÂU HỎI: {query}

CÁC ĐOẠN VĂN BẢN PHÁP LUẬT:
{docs_text}

YÊU CẦU:
- Đánh giá từng đoạn văn bản (0-10 điểm)
- 10 điểm = RẤT LIÊN QUAN, trả lời trực tiếp câu hỏi
- 5-7 điểm = LIÊN QUAN GIÁN TIẾP, cung cấp ngữ cảnh
- 0-4 điểm = ÍT LIÊN QUAN hoặc KHÔNG LIÊN QUAN

FORMAT TRẢ LỜI (bắt buộc - mỗi dòng một đánh giá):
[0]: 8 - Lý do ngắn gọn
[1]: 6 - Lý do ngắn gọn
[2]: 9 - Lý do ngắn gọn
...

CHỈ TRẢ LỜI ĐÚNG FORMAT, KHÔNG THÊM GÌ KHÁC."""

        response = gemini_model.generate_content(prompt)
        scores_text = response.text.strip()
        
        print(f'[RE-RANK] LLM scoring response:\n{scores_text[:300]}...')
        
        # Parse scores
        scores = []
        for line in scores_text.split('\n'):
            match = re.search(r'\[(\d+)\]:\s*(\d+)', line)
            if match:
                idx = int(match.group(1))
                score = int(match.group(2))
                if idx < len(candidates):
                    scores.append((idx, score))
        
        if not scores:
            print('[RE-RANK] No scores parsed, fallback to original order')
            return candidates[:top_k]
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Re-order candidates
        reranked = []
        seen = set()
        for idx, score in scores[:top_k]:
            if idx not in seen:
                reranked.append(candidates[idx])
                seen.add(idx)
                print(f'[RE-RANK] [{idx}] Score: {score}/10')
        
        # Fill remaining slots with original order if needed
        for doc in candidates:
            if len(reranked) >= top_k:
                break
            if doc not in reranked:
                reranked.append(doc)
        
        print(f'[RE-RANK] ✅ Reranked {len(candidates)} → {len(reranked)} documents')
        return reranked[:top_k]
        
    except Exception as e:
        print(f'[RE-RANK] ❌ Error: {e}, fallback to original order')
        return candidates[:top_k]


def advanced_hybrid_search(
    query: str,
    all_chunks: List[Dict],
    bm25_index,
    faiss_index,
    embedder,
    tokenize_fn,
    enhanced_decompose_fn,
    gemini_model=None,
    use_advanced=False,
    top_k: int = 8
) -> List[Dict]:
    """
    Tìm kiếm nâng cao với Intent Detection + Query Expansion + LLM Re-ranking
    
    Args:
        query: User query
        all_chunks: All document chunks
        bm25_index: BM25 index
        faiss_index: FAISS index
        embedder: Embedding model
        tokenize_fn: Tokenization function
        enhanced_decompose_fn: Query decomposition function
        gemini_model: Gemini model for re-ranking (OPTIONAL, for Quality mode)
        use_advanced: True = Quality mode (enable re-ranking), False = Fast mode
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
    
    # ✅ Log refined query
    refined_query = decomp_result.get('refined_query', query)
    if refined_query != query:
        print(f'[REFINED] Original: "{query}"')
        print(f'[REFINED] →→→ New: "{refined_query}"')
    
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
    
    reranked_indices = np.argsort(semantic_scores)[::-1][:top_k * 2]
    results = [candidates[i] for i in reranked_indices]
    
    # ✅ Step 5: LLM Re-ranking (chỉ cho Quality mode)
    if use_advanced and gemini_model and len(results) > top_k:
        print(f'[RE-RANK] Quality mode: Re-ranking {len(results)} candidates with LLM...')
        results = rerank_with_llm(
            query=refined_query,
            candidates=results,
            gemini_model=gemini_model,
            top_k=top_k
        )
    else:
        results = results[:top_k]
    
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
