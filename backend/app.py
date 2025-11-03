"""
Legal Document Q&A API - FastAPI Application
Modular architecture with clean separation of concerns
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from contextlib import asynccontextmanager
from collections import defaultdict
from typing import Optional
import os
import time  # For performance timing
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Import models
from models import QuestionRequest, AnswerResponse, HealthResponse, PDFSource, FeedbackRequest, FeedbackResponse

# Import core functions
from core.document_processor import xu_ly_van_ban_phap_luat_json
from core.search import advanced_hybrid_search, simple_search
from core.search_domains import search_with_domains, search_multi_query_with_domains  # ✅ New
from core.generation import generate_answer, get_rejection_message
from core.intent_detection import get_cache_size, enhanced_decompose_query
from core.domain_manager import DomainManager  # ✅ New

# Import utilities
from utils.cache import get_data_hash, build_or_load_bm25, build_or_load_faiss
from utils.tokenizer import tokenize_vi
from config import EMBEDDING_MODEL, GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL, GEMINI_LITE_MODEL  # Import model names


# ============================================================================
# Global State Variables
# ============================================================================

# all_chunks = []
# bm25_index = None
# faiss_index = None
# corpus_embeddings = None

# ✅ NEW: Domain-based architecture
domain_manager: Optional[DomainManager] = None
embedder = None
gemini_flash_model = None  # Flash model for fast mode answer
gemini_pro_model = None    # Pro model for quality mode answer
gemini_lite_model = None   # Lite model for intent detection


# ============================================================================
# Lifespan Event Handler (replaces deprecated on_event)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all models and domain manager on server startup"""
    global domain_manager, embedder, gemini_flash_model, gemini_pro_model, gemini_lite_model
    
    print('[STARTUP] 🚀 Khoi dong Legal Q&A System v3.0 (Domain-based)...', flush=True)
    
    # 1. Load Gemini API
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print('[INFO] API key not in environment, trying .env file...', flush=True)
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print('[ERROR] GOOGLE_API_KEY not found!', flush=True)
        raise Exception('Missing GOOGLE_API_KEY')
    
    print('[OK] Google API key loaded successfully', flush=True)
    genai.configure(api_key=api_key)
    
    # 2. Initialize Gemini models (3 models for different purposes)
    gemini_flash_model = genai.GenerativeModel(GEMINI_FLASH_MODEL)  # Fast mode answer
    gemini_pro_model = genai.GenerativeModel(GEMINI_PRO_MODEL)      # Quality mode answer
    gemini_lite_model = genai.GenerativeModel(GEMINI_LITE_MODEL)    # Intent/decompose
    
    print('[OK] Google AI models ready:', flush=True)
    print(f'  - {GEMINI_FLASH_MODEL} (fast mode answer)', flush=True)
    print(f'  - {GEMINI_PRO_MODEL} (quality mode answer)', flush=True)
    print(f'  - {GEMINI_LITE_MODEL} (intent detection, decomposition)', flush=True)
    
    # 3. Load embedding model
    print(f'[INFO] Loading embedding model: {EMBEDDING_MODEL}...', flush=True)
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    print(f'[OK] Embedding model ready', flush=True)
    
    # 4. Initialize Domain Manager (lazy loading)
    print('[INFO] Initializing Domain Manager...', flush=True)
    domain_manager = DomainManager(embedder=embedder)
    print(f'[OK] Domain Manager ready with {len(domain_manager.domains)} domains', flush=True)
    
    # List domains
    for domain_id, domain in domain_manager.domains.items():
        print(f'  ✓ {domain_id}: {domain.domain_name} ({domain.chunk_count} chunks)', flush=True)
    
    print('[SUCCESS] ✅ Server ready! (Indices will load on first query)', flush=True)
    
    # Application is running
    yield
    
    # Cleanup on shutdown
    print('[SHUTDOWN] Cleaning up resources...', flush=True)
    if domain_manager:
        domain_manager.unload_all()


# ============================================================================
# FastAPI Application Setup (with lifespan)
# ============================================================================

app = FastAPI(
    title='Legal Document Q&A API',
    description='Advanced RAG system for Vietnamese legal documents',
    version='2.0.0',
    lifespan=lifespan  # ✅ Use lifespan instead of on_event
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log request validation errors for easier debugging"""
    print('[VALIDATION ERROR]', exc.errors(), flush=True)
    print('[REQUEST BODY]', exc.body, flush=True)
    return await request_validation_exception_handler(request, exc)


# ============================================================================
# API Routes
# ============================================================================

@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    total_chunks = sum(d.metadata.get('chunk_count', 0) for d in domain_manager.domains.values()) if domain_manager else 0
    
    return {
        "status": "healthy",
        "models_loaded": embedder is not None and gemini_flash_model is not None,
        "total_chunks": total_chunks
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Main Q&A endpoint with domain-based search"""
    start_time = time.time()
    timing = {}
    
    if not domain_manager:
        raise HTTPException(status_code=503, detail="System not ready")
    
    print(f'\n{"="*70}', flush=True)
    print(f'[INFO] Question: {request.question}', flush=True)
    print(f'[INFO] Mode: {request.model_mode.upper()}', flush=True)
    print(f'{"="*70}', flush=True)
    
    # ===== PHASE 1: Intent Detection + Domain Detection =====
    intent_start = time.time()
    
    use_advanced = (request.model_mode == "detail")
    decompose_model = gemini_flash_model if use_advanced else gemini_lite_model
    
    intent_result = enhanced_decompose_query(
        question=request.question,
        gemini_lite_model=gemini_lite_model,
        gemini_flash_model=decompose_model,
        use_advanced=use_advanced,
        domain_manager=domain_manager  # ✅ Pass domain_manager for domain detection
    )
    
    timing['intent_ms'] = round((time.time() - intent_start) * 1000, 2)
    print(f'[TIMING] Intent+Decompose: {timing["intent_ms"]}ms', flush=True)
    
    # Check if rejected
    if not intent_result['should_process']:
        total_time = round((time.time() - start_time) * 1000, 2)
        print(f'[TIMING] Total (rejected): {total_time}ms', flush=True)
        return {
            "answer": get_rejection_message(),
            "sources": [],
            "pdf_sources": [],
            "search_method": "rejected",
            "timing_ms": total_time
        }
    
    # ===== PHASE 2: Domain-based Search =====
    search_start = time.time()
    
    # Check if we have sub_questions (multi-query) or single query
    sub_questions = intent_result.get('sub_questions', [])
    
    if len(sub_questions) > 1:
        # Multi-query search across domains
        print(f'[SEARCH] Multi-query mode: {len(sub_questions)} sub-questions', flush=True)
        relevant_chunks = search_multi_query_with_domains(
            sub_questions=sub_questions,
            domain_manager=domain_manager,
            tokenize_fn=tokenize_vi,
            gemini_model=gemini_lite_model if use_advanced else None,  # ✅ Use Lite for re-ranking (fast & cheap)
            use_advanced=use_advanced,
            top_k=5
        )
    else:
        # Single query search with domain hint
        query = intent_result.get('refined_query', request.question)
        print(f'[SEARCH] Single-query mode: "{query}"', flush=True)
        relevant_chunks = search_with_domains(
            query=query,
            domain_manager=domain_manager,
            tokenize_fn=tokenize_vi,
            intent_data=intent_result,
            gemini_model=gemini_lite_model if use_advanced else None,  # ✅ Use Lite for re-ranking (fast & cheap)
            use_advanced=use_advanced,
            top_k=5
        )
    
    timing['search_ms'] = round((time.time() - search_start) * 1000, 2)
    print(f'[TIMING] Search: {timing["search_ms"]}ms', flush=True)
    print(f'[RESULTS] Found {len(relevant_chunks)} relevant chunks', flush=True)
    
    if not relevant_chunks:
        total_time = round((time.time() - start_time) * 1000, 2)
        return {
            "answer": "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu pháp luật.",
            "sources": [],
            "pdf_sources": [],
            "search_method": "domain_based_no_results",
            "timing_ms": total_time
        }
    
    # ===== PHASE 3: Generate Answer =====
    gen_start = time.time()
    
    # Select model based on mode: Flash for both (Detail uses detailed prompt, Summary uses concise)
    answer_model = gemini_flash_model  # Always use Flash for answer generation
    
    answer = generate_answer(
        question=request.question,
        context=relevant_chunks,
        gemini_model=answer_model,
        chat_history=request.chat_history if hasattr(request, 'chat_history') else None,
        use_advanced=use_advanced  # ✅ CRITICAL: Pass mode to enable detail prompt
    )
    
    timing['generation_ms'] = round((time.time() - gen_start) * 1000, 2)
    timing['total_ms'] = round((time.time() - start_time) * 1000, 2)
    
    print(f'[TIMING] Generation: {timing["generation_ms"]}ms', flush=True)
    print(f'[TIMING] Total: {timing["total_ms"]}ms', flush=True)
    print(f'{"="*70}\n', flush=True)
    
    # ===== Prepare Response =====
    pdf_sources = []
    for chunk in relevant_chunks[:3]:  # Top 3 for display
        # Convert page_num to int or None
        page_num = chunk.get('page_num')
        if page_num == '' or page_num is None:
            page_num = None
        else:
            try:
                page_num = int(page_num)
            except (ValueError, TypeError):
                page_num = None
        
        pdf_sources.append(PDFSource(
            pdf_file=chunk.get('pdf_file', ''),
            json_file=chunk.get('json_file', ''),
            page_num=page_num,
            article_num=chunk.get('article_num', ''),
            content=chunk.get('content', '')[:500],  # Limit to 500 chars
            highlight_text=chunk.get('content', '')[:200]  # First 200 chars for highlight
        ))
    
    return {
        "answer": answer,
        "sources": [{"source": c.get('json_file', ''), "content": c.get('content', '')} for c in relevant_chunks],
        "pdf_sources": pdf_sources,
        "search_method": f"domain_based_{'detail' if use_advanced else 'summary'}",
        "timing_ms": timing['total_ms']
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    domains_info = {}
    total_chunks = 0
    
    for domain_id in domain_manager.list_domains():
        domain = domain_manager.get_domain(domain_id)
        # Count chunks from JSONL without loading all into memory
        chunk_count = 0
        chunks_path = os.path.join(domain.domain_dir, 'chunks.jsonl')
        if os.path.exists(chunks_path):
            with open(chunks_path, 'r', encoding='utf-8') as f:
                chunk_count = sum(1 for _ in f)
        
        domains_info[domain_id] = {
            "name": domain.domain_name,
            "chunks": chunk_count,
            "loaded": domain._bm25_index is not None  # Check if indices are loaded
        }
        total_chunks += chunk_count
    
    return {
        "total_chunks": total_chunks,
        "domains": domains_info,
        "models": {
            "embedder": EMBEDDING_MODEL,
            "llm_flash": f"{GEMINI_FLASH_MODEL} (summary mode answer)",
            "llm_pro": f"{GEMINI_PRO_MODEL} (detail mode answer)",
            "llm_lite": f"{GEMINI_LITE_MODEL} (intent detection, decomposition)"
        },
        "intent_cache_size": get_cache_size()
    }


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback (like/dislike) on answer quality"""
    import json
    from datetime import datetime
    
    # Create feedback log directory if not exists
    feedback_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback_logs')
    os.makedirs(feedback_dir, exist_ok=True)
    
    # Prepare feedback data
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "query": request.query,
        "answer": request.answer,
        "context": request.context,
        "status": request.status,
        "comment": request.comment
    }
    
    # Save to JSON file (append mode)
    feedback_file = os.path.join(feedback_dir, f"feedback_{datetime.now().strftime('%Y%m')}.jsonl")
    
    try:
        with open(feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_data, ensure_ascii=False) + '\n')
        
        print(f'[FEEDBACK] {request.status.upper()}: {request.query[:50]}...', flush=True)
        
        return {
            "success": True,
            "message": "Cảm ơn phản hồi của bạn!"
        }
    except Exception as e:
        print(f'[ERROR] Failed to save feedback: {e}', flush=True)
        return {
            "success": False,
            "message": "Không thể lưu phản hồi"
        }


# ============================================================================
# PDF Serving Endpoint
# ============================================================================

@app.post("/api/get-document")
async def get_document(request: dict):
    """Serve PDF as base64 via POST to avoid IDM detection"""
    import base64
    
    filename = request.get('filename')
    if not filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    # Get absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find PDF in domain folders first
    pdf_path = None
    domains_dir = os.path.join(current_dir, 'data', 'domains')
    
    if os.path.exists(domains_dir):
        for domain_id in os.listdir(domains_dir):
            domain_pdf_path = os.path.join(domains_dir, domain_id, 'pdfs', filename)
            if os.path.exists(domain_pdf_path):
                pdf_path = domain_pdf_path
                print(f"[PDF] Found in domain: {domain_id}", flush=True)
                break
    
    # Fallback: Try old location (data/{filename})
    if pdf_path is None:
        pdf_path = os.path.join(current_dir, 'data', filename)
    
    print(f"[PDF] Requested: {filename}", flush=True)
    print(f"[PDF] Looking at: {pdf_path}", flush=True)
    print(f"[PDF] Exists: {os.path.exists(pdf_path)}", flush=True)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
    
    # Read and encode to base64
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Return JSON with base64 data
    return {
        "filename": filename,
        "data": pdf_base64,
        "size": len(pdf_bytes),
        "type": "application/pdf"
    }


# ============================================================================
# Helper Functions
# ============================================================================

def map_json_to_pdf(json_filename: str) -> str:
    """Map JSON filename to corresponding PDF filename"""
    json_to_pdf_map = {
        'luat_hon_nhan_hopnhat.json': 'luat_hon_nhan.pdf',
        'luat_dat_dai_hopnhat.json': 'luat_dat_dai.pdf',
        'luat_lao_donghopnhat.json': 'luat_lao_dong.pdf',
        'luat_dauthau_hopnhat.json': 'luat_dau_thau.pdf',
        'chuyen_giao_cong_nghe_hopnhat.json': 'luat_chuyen_giao_cong_nghe.pdf',
        'nghi_dinh_214_2025.json': 'nghi_dinh_214_2025.pdf',
    }
    return json_to_pdf_map.get(json_filename, 'unknown.pdf')


def extract_pdf_metadata(chunk: dict) -> PDFSource:
    """Extract PDF metadata from chunk with full article + section reference"""
    metadata = chunk.get('metadata', {})
    json_file = metadata.get('json_file', '')
    pdf_file = map_json_to_pdf(json_file) if json_file else 'unknown.pdf'
    
    # Build complete reference: "Dieu X, Khoan Y"
    article_num = metadata.get('article_num', '')  # e.g., "3" or "Dieu 3"
    section_num = metadata.get('section_num', '')  # e.g., "5" or "Khoan 5"
    
    # Construct full reference
    full_reference = article_num
    if section_num:
        # If article_num doesn't already contain section info
        if 'Khoan' not in article_num and 'khoan' not in article_num.lower():
            # Clean section number
            section_clean = section_num.replace('Khoan', '').replace('khoan', '').strip()
            if article_num:
                full_reference = f"{article_num}, Khoan {section_clean}"
            else:
                full_reference = f"Khoan {section_clean}"
    
    return PDFSource(
        pdf_file=pdf_file,
        page_num=metadata.get('page_num'),
        content=chunk['content'][:200],
        highlight_text=chunk['content'],
        json_file=json_file,
        article_num=full_reference  # Now contains "Dieu 3, Khoan 5"
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    import os
    port = int(os.getenv('PORT', 7860))  # Support both 8000 (local) and 7860 (HF Spaces)
    uvicorn.run('app:app', host='0.0.0.0', port=port, reload=False)
