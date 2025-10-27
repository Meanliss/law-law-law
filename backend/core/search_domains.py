"""
Domain-based Search Module
"""
from typing import List, Dict, Optional
from .search import rerank_with_llm


def search_with_domains(
    query: str,
    domain_manager,
    tokenize_fn,
    intent_data: Optional[Dict] = None,
    gemini_model = None,
    use_advanced: bool = False,
    top_k: int = 8
) -> List[Dict]:
    """
    Search using domain-based indices
    
    Args:
        query: User query
        domain_manager: DomainManager instance
        tokenize_fn: Tokenization function
        intent_data: Intent detection result with sub_questions and domains
        gemini_model: Gemini model for re-ranking (Quality mode only)
        use_advanced: True = Quality mode with LLM re-ranking
        top_k: Number of results to return
    
    Returns:
        List of top_k relevant chunks
    """
    
    # ===== STEP 1: Determine which domains to search =====
    domain_ids = None
    
    if intent_data and 'sub_questions' in intent_data:
        # Extract domains from sub_questions
        detected_domains = []
        for sub_q in intent_data['sub_questions']:
            if isinstance(sub_q, dict) and 'domain' in sub_q and sub_q['domain']:
                detected_domains.append(sub_q['domain'])
            elif isinstance(sub_q, str):
                # Fallback: detect from query text
                detected = domain_manager.detect_domain_from_keywords(sub_q)
                if detected:
                    detected_domains.append(detected)
        
        # Remove duplicates
        domain_ids = list(dict.fromkeys(detected_domains))
    
    # ===== STEP 2: Search in detected domains =====
    print(f"\n[SEARCH] Query: '{query}'", flush=True)
    print(f"[SEARCH] Target domains: {domain_ids if domain_ids else 'AUTO-DETECT'}", flush=True)
    
    results = domain_manager.search(
        query=query,
        tokenize_fn=tokenize_fn,
        top_k=top_k * 2,  # Get more candidates for re-ranking
        domain_ids=domain_ids,
        intent_data=intent_data
    )
    
    print(f"[SEARCH] Found {len(results)} candidates", flush=True)
    
    # ===== STEP 3: Re-rank with LLM (Quality mode only) =====
    if use_advanced and gemini_model and len(results) > 0:
        print("[SEARCH] Applying LLM re-ranking (Quality mode)...", flush=True)
        results = rerank_with_llm(query, results, gemini_model, top_k=top_k)
    else:
        results = results[:top_k]
    
    # ===== STEP 4: Add domain context to results =====
    for result in results:
        if 'domain_id' not in result:
            result['domain_id'] = 'unknown'
        if 'domain_name' not in result:
            result['domain_name'] = result.get('domain_id', 'Chưa xác định')
    
    print(f"[SEARCH] Returning {len(results)} results", flush=True)
    return results


def search_multi_query_with_domains(
    sub_questions: List[Dict],
    domain_manager,
    tokenize_fn,
    gemini_model = None,
    use_advanced: bool = False,
    top_k: int = 8
) -> List[Dict]:
    """
    Search multiple sub-questions across domains and merge results
    
    Args:
        sub_questions: List of {'question': str, 'domain': str}
        domain_manager: DomainManager instance
        tokenize_fn: Tokenization function
        gemini_model: Gemini model for re-ranking
        use_advanced: Quality mode flag
        top_k: Number of final results
    
    Returns:
        Merged and deduplicated top_k results
    """
    
    all_results = []
    seen_contents = set()
    
    # Search each sub-question
    for sub_q in sub_questions:
        if isinstance(sub_q, dict):
            question = sub_q.get('question', '')
            domain_id = sub_q.get('domain')
        else:
            question = sub_q
            domain_id = None
        
        if not question:
            continue
        
        print(f"\n[MULTI-SEARCH] Sub-question: '{question}'", flush=True)
        print(f"[MULTI-SEARCH] Domain: {domain_id if domain_id else 'AUTO-DETECT'}", flush=True)
        
        # Search with domain hint
        results = domain_manager.search(
            query=question,
            tokenize_fn=tokenize_fn,
            top_k=top_k,
            domain_ids=[domain_id] if domain_id else None
        )
        
        # Deduplicate by content
        for result in results:
            content = result.get('content', '')
            # Use first 100 chars as fingerprint
            fingerprint = content[:100] if content else ''
            
            if fingerprint and fingerprint not in seen_contents:
                seen_contents.add(fingerprint)
                all_results.append(result)
    
    print(f"\n[MULTI-SEARCH] Collected {len(all_results)} unique results", flush=True)
    
    # Sort by score
    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Re-rank if Quality mode
    if use_advanced and gemini_model and len(all_results) > top_k:
        # Combine all sub-questions into one query for re-ranking
        combined_query = " | ".join([
            sq.get('question', sq) if isinstance(sq, dict) else sq
            for sq in sub_questions
        ])
        print(f"[MULTI-SEARCH] Re-ranking with combined query: '{combined_query[:100]}...'", flush=True)
        all_results = rerank_with_llm(combined_query, all_results, gemini_model, top_k=top_k)
    
    return all_results[:top_k]
