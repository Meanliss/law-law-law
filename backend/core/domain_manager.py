"""
Domain Manager - Quản lý multiple domains với lazy loading và domain detection
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from utils.embedding import load_embedding_model
from .domain import Domain
from config import EMBEDDING_MODEL


class DomainManager:
    """Manage multiple legal domains with lazy loading and smart detection"""
    
    def __init__(self, embedder: Optional[SentenceTransformer] = None):
        self.registry_path = Path("data/domain_registry.json")
        
        # Load embedder
        if embedder is None:
            print("🧠 Loading embedder model...", flush=True)
            self.embedder = load_embedding_model()
        else:
            self.embedder = embedder
        
        # ✅ Load registry (tiny, always in memory)
        if not self.registry_path.exists():
            print(f"⚠️ Domain registry not found: {self.registry_path}", flush=True)
            self.registry = {}
        else:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
        
        # ✅ Create domain objects (lazy, don't load indices yet)
        self.domains: Dict[str, Domain] = {}
        for domain_id in self.registry.keys():
            self.domains[domain_id] = Domain(domain_id, self.embedder)
        
        print(f"✅ Loaded {len(self.domains)} domains (lazy mode): {list(self.domains.keys())}", flush=True)
    
    def detect_domain_from_keywords(self, query: str) -> Optional[str]:
        """Detect domain based on keyword matching"""
        query_lower = query.lower()
        
        scores = {}
        for domain_id, meta in self.registry.items():
            # Count keyword matches
            score = sum(1 for kw in meta.get('keywords', []) if kw in query_lower)
            if score > 0:
                scores[domain_id] = score
        
        if scores:
            best_domain = max(scores, key=scores.get)
            print(f"🎯 Detected domain from keywords: {best_domain} (score: {scores[best_domain]})", flush=True)
            return best_domain
        
        return None
    
    def detect_domains_from_intent(self, intent_data: Dict) -> List[str]:
        """
        Detect domains from intent detection results
        
        Intent format:
        {
            "is_legal": true,
            "sub_questions": [
                {
                    "question": "...",
                    "domain": "lao_dong",  # ← We add this
                    "keywords": ["lao động", "nghỉ việc"]
                }
            ]
        }
        """
        detected_domains = []
        
        # Check sub_questions for domain hints
        sub_questions = intent_data.get('sub_questions', [])
        for sub_q in sub_questions:
            # If domain already marked by intent detection
            if 'domain' in sub_q and sub_q['domain']:
                domain_id = sub_q['domain']
                if domain_id in self.domains:
                    detected_domains.append(domain_id)
                    continue
            
            # Otherwise, detect from keywords in sub-question
            question_text = sub_q.get('question', '')
            domain_id = self.detect_domain_from_keywords(question_text)
            if domain_id:
                detected_domains.append(domain_id)
                # Mark domain in sub-question for later use
                sub_q['domain'] = domain_id
        
        # Remove duplicates while preserving order
        unique_domains = []
        for d in detected_domains:
            if d not in unique_domains:
                unique_domains.append(d)
        
        if unique_domains:
            print(f"🎯 Detected domains from intent: {unique_domains}", flush=True)
        
        return unique_domains
    
    def search_in_domain(self, query: str, domain_id: str, tokenize_fn, top_k: int = 8) -> List[Dict]:
        """Search in a specific domain"""
        if domain_id not in self.domains:
            print(f"⚠️ Domain '{domain_id}' not found", flush=True)
            return []
        
        print(f"🔍 Searching in domain: {domain_id} ({self.registry[domain_id]['name']})", flush=True)
        return self.domains[domain_id].search(query, tokenize_fn, top_k)
    
    def search_multi_domain(self, query: str, domain_ids: List[str], tokenize_fn, top_k: int = 8) -> List[Dict]:
        """Search across multiple domains and merge results"""
        all_results = []
        
        for domain_id in domain_ids:
            if domain_id in self.domains:
                results = self.search_in_domain(query, domain_id, tokenize_fn, top_k)
                all_results.extend(results)
        
        # Sort by score and return top_k
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return all_results[:top_k]
    
    def search_all_domains(self, query: str, tokenize_fn, top_k: int = 8) -> List[Dict]:
        """Search across ALL domains (expensive, use as fallback)"""
        print("🌐 Searching across all domains", flush=True)
        
        all_results = []
        for domain_id in self.domains.keys():
            results = self.search_in_domain(query, domain_id, tokenize_fn, top_k)
            all_results.extend(results)
        
        # Sort by score and return top_k
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return all_results[:top_k]
    
    def search(self, query: str, tokenize_fn, top_k: int = 8, 
               domain_ids: Optional[List[str]] = None,
               intent_data: Optional[Dict] = None) -> List[Dict]:
        """
        Smart search with domain detection
        
        Priority:
        1. Use provided domain_ids
        2. Detect from intent_data
        3. Detect from query keywords
        4. Search all domains (fallback)
        """
        
        # Option 1: Use explicitly provided domains
        if domain_ids:
            if len(domain_ids) == 1:
                return self.search_in_domain(query, domain_ids[0], tokenize_fn, top_k)
            else:
                return self.search_multi_domain(query, domain_ids, tokenize_fn, top_k)
        
        # Option 2: Detect from intent data
        if intent_data:
            detected = self.detect_domains_from_intent(intent_data)
            if detected:
                if len(detected) == 1:
                    return self.search_in_domain(query, detected[0], tokenize_fn, top_k)
                else:
                    return self.search_multi_domain(query, detected, tokenize_fn, top_k)
        
        # Option 3: Detect from query keywords
        detected = self.detect_domain_from_keywords(query)
        if detected:
            return self.search_in_domain(query, detected, tokenize_fn, top_k)
        
        # Option 4: Search all domains (fallback)
        return self.search_all_domains(query, tokenize_fn, top_k)
    
    def get_domain_info(self, domain_id: str) -> Optional[Dict]:
        """Get domain metadata"""
        return self.registry.get(domain_id)
    
    def list_domains(self) -> List[Dict]:
        """List all available domains"""
        return [
            {
                'id': domain_id,
                'name': meta['name'],
                'description': meta.get('description', ''),
                'chunk_count': self.domains[domain_id].metadata.get('chunk_count', 0),
                'loaded': self.domains[domain_id].is_loaded
            }
            for domain_id, meta in self.registry.items()
        ]
    
    def unload_all(self):
        """Unload all domains from memory"""
        for domain in self.domains.values():
            domain.unload()
