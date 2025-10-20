"""
Legal Document Q&A API - FastAPI Application
Modular architecture with clean separation of concerns
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from collections import defaultdict
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
from core.generation import generate_answer, get_rejection_message
from core.intent_detection import get_cache_size, enhanced_decompose_query

# Import utilities
from utils.cache import get_data_hash, build_or_load_bm25, build_or_load_faiss
from utils.tokenizer import tokenize_vi
from config import EMBEDDING_MODEL  # Import embedding model name


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title='Legal Document Q&A API',
    description='Advanced RAG system for Vietnamese legal documents',
    version='2.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ============================================================================
# Global State Variables
# ============================================================================

all_chunks = []
bm25_index = None
faiss_index = None
corpus_embeddings = None
embedder = None
gemini_model = None  # Full model for answer generation
gemini_lite_model = None  # Lite model for intent detection


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize all models and indexes on server startup"""
    global all_chunks, bm25_index, faiss_index, corpus_embeddings, embedder, gemini_model, gemini_lite_model
    
    print('[STARTUP] Dang khoi dong Legal Q&A System v2.0...')
    
    # 1. Load Gemini API
    # 1. Load Gemini API
    # Try environment variable first (for cloud platforms like Render)
    api_key = os.getenv('GOOGLE_API_KEY')
    
    # If not found, try loading from .env file (for local development)
    if not api_key:
        print('[INFO] API key not in environment, trying .env file...')
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print('[ERROR] GOOGLE_API_KEY not found in environment variables or .env file!')
        raise Exception('Missing GOOGLE_API_KEY')
    
    print('[OK] Google API key loaded successfully')
        
    genai.configure(api_key=api_key)
    
    # 2. Initialize dual Gemini models
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')  # For answer generation
    gemini_lite_model = genai.GenerativeModel('gemini-2.5-flash-lite')  # For intent/decompose
    
    print('[OK] Google AI models ready:')
    print('  - gemini-2.5-flash (answer generation)')
    print('  - gemini-2.5-flash-lite (intent detection, decomposition)')
    
    # 3. Load embedding model
    print(f'[INFO] Dang tai embedding model: {EMBEDDING_MODEL}...')
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    print(f'[OK] Embedding model {EMBEDDING_MODEL} da san sang')
    print(f'     Model info: Vietnamese-optimized PhoBERT (vinai/phobert-base)')
    
    # 4. Load legal documents
    data_folder = 'data'
    if not os.path.exists(data_folder):
        print(f'[WARN] Khong tim thay thu muc {data_folder}')
        return
    
    json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
    print(f'[INFO] Tim thay {len(json_files)} file JSON')
    
    all_chunks = []
    for json_file in json_files:
        file_path = os.path.join(data_folder, json_file)
        chunks, nguon = xu_ly_van_ban_phap_luat_json(file_path)
        all_chunks.extend(chunks)
        print(f'[OK] {json_file}: {len(chunks)} chunks')
    
    if not all_chunks:
        print('[ERROR] Khong co du lieu nao duoc tai!')
        return
    
    print(f'[OK] Tong cong: {len(all_chunks)} chunks')
    
    # 5. Build/Load indexes with hash-based caching
    data_hash = get_data_hash(all_chunks)
    print(f'[INFO] Data hash: {data_hash}')
    
    corpus = [tokenize_vi(chunk['content']) for chunk in all_chunks]
    bm25_index = build_or_load_bm25(corpus, data_hash)
    
    faiss_index, corpus_embeddings = build_or_load_faiss(all_chunks, data_hash, embedder)
    
    print('[SUCCESS] Server san sang!')


# ============================================================================
# API Routes
# ============================================================================

@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": embedder is not None and gemini_model is not None,
        "total_chunks": len(all_chunks)
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Main Q&A endpoint with advanced search and intent detection"""
    # ===== START TIMING =====
    start_time = time.time()
    timing = {}
    
    if not all_chunks:
        raise HTTPException(status_code=503, detail="System not ready")
    
    print(f'\n{"="*70}')
    print(f'[INFO] Question: {request.question}')
    print(f'[INFO] Model Mode: {request.model_mode.upper()} {"(all Flash Lite)" if request.model_mode == "fast" else "(Flash Lite for intent, Flash for answer)"}')
    print(f'{"="*70}')
    
    # Select models based on mode
    if request.model_mode == "fast":
        # Fast mode: Use Flash Lite for everything
        intent_model = gemini_lite_model
        answer_model = gemini_lite_model
        print('[MODE] ⚡ FAST - Using Flash Lite for all operations')
    else:
        # Quality mode: Use Flash Lite for intent, Flash for answer
        intent_model = gemini_lite_model
        answer_model = gemini_model
        print('[MODE] 🎯 QUALITY - Using Flash Lite (intent) + Flash (answer)')
    
    # ===== PHASE 1: INTENT DETECTION & QUERY EXPANSION =====
    intent_start = time.time()
    
    # Search with selected mode
    if request.use_advanced:
        # Create enhanced_decompose function with intent_model closure
        def enhanced_decompose_fn(query):
            return enhanced_decompose_query(query, intent_model)
        
        relevant_chunks = advanced_hybrid_search(
            query=request.question,
            all_chunks=all_chunks,
            bm25_index=bm25_index,
            faiss_index=faiss_index,
            embedder=embedder,
            tokenize_fn=tokenize_vi,
            enhanced_decompose_fn=enhanced_decompose_fn,
            top_k=8
        )
        mode = "advanced"
    else:
        relevant_chunks = simple_search(
            query=request.question,
            all_chunks=all_chunks,
            bm25_index=bm25_index,
            faiss_index=faiss_index,
            embedder=embedder,
            tokenize_fn=tokenize_vi,
            top_k=8
        )
        mode = "simple"
    
    timing['search_ms'] = round((time.time() - intent_start) * 1000, 2)
    print(f'[TIMING] Search completed in {timing["search_ms"]}ms')
    
    # Check if query was rejected by intent detection
    if not relevant_chunks:
        total_time = round((time.time() - start_time) * 1000, 2)
        print(f'[TIMING] Total time (rejected): {total_time}ms')
        print(f'{"="*70}\n')
        return {
            "answer": get_rejection_message(),
            "sources": [],
            "search_mode": mode,
            "timing": {
                "total_ms": total_time,
                "search_ms": timing['search_ms'],
                "generation_ms": 0,
                "status": "rejected"
            }
        }
    
    # ===== PHASE 2: ANSWER GENERATION =====
    gen_start = time.time()
    answer = generate_answer(request.question, relevant_chunks, answer_model)
    timing['generation_ms'] = round((time.time() - gen_start) * 1000, 2)
    print(f'[TIMING] Answer generation completed in {timing["generation_ms"]}ms')
    
    # Total time
    timing['total_ms'] = round((time.time() - start_time) * 1000, 2)
    print(f'[TIMING] ⚡ TOTAL TIME: {timing["total_ms"]}ms')
    print(f'  ├─ Search: {timing["search_ms"]}ms ({round(timing["search_ms"]/timing["total_ms"]*100, 1)}%)')
    print(f'  └─ Generation: {timing["generation_ms"]}ms ({round(timing["generation_ms"]/timing["total_ms"]*100, 1)}%)')
    print(f'{"="*70}\n')
    
    # Format sources (original format)
    sources = [
        {"source": chunk["source"], "content": chunk["content"][:200]} 
        for chunk in relevant_chunks
    ]
    
    # Extract PDF metadata
    pdf_sources = [extract_pdf_metadata(chunk) for chunk in relevant_chunks]
    
    return {
        "answer": answer,
        "sources": sources,
        "pdf_sources": pdf_sources,
        "search_mode": mode,
        "timing": {
            "total_ms": timing['total_ms'],
            "search_ms": timing['search_ms'],
            "generation_ms": timing['generation_ms'],
            "status": "success"
        }
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    laws = defaultdict(int)
    for chunk in all_chunks:
        law_name = chunk.get('metadata', {}).get('law_name', 'Unknown')
        laws[law_name] += 1
    
    return {
        "total_chunks": len(all_chunks),
        "laws": dict(laws),
        "models": {
            "embedder": EMBEDDING_MODEL,
            "llm_full": "gemini-2.5-flash (answer generation)",
            "llm_lite": "gemini-2.5-flash-lite (intent detection, decomposition)"
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
        
        print(f'[FEEDBACK] {request.status.upper()}: {request.query[:50]}...')
        
        return {
            "success": True,
            "message": "Cảm ơn phản hồi của bạn!"
        }
    except Exception as e:
        print(f'[ERROR] Failed to save feedback: {e}')
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
    pdf_path = os.path.join(current_dir, 'data', filename)
    
    print(f"[PDF] Requested: {filename}")
    print(f"[PDF] Looking at: {pdf_path}")
    print(f"[PDF] Exists: {os.path.exists(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Document not found")
    
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
