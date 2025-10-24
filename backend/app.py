"""
Legal Document Q&A API - FastAPI Application
Modular architecture with clean separation of concerns
Production vs Review file system
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from contextlib import asynccontextmanager
from collections import defaultdict
import os
import json
import time
import shutil
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
from config import EMBEDDING_MODEL


# ============================================================================
# Global State Variables
# ============================================================================

all_chunks = []
bm25_index = None
faiss_index = None
corpus_embeddings = None
embedder = None
gemini_model = None
gemini_lite_model = None


# ============================================================================
# Lifespan Event Handler
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all models and indexes on server startup and cleanup on shutdown"""
    global all_chunks, bm25_index, faiss_index, corpus_embeddings, embedder, gemini_model, gemini_lite_model
    
    print('='*70, flush=True)
    print('[STARTUP] Legal Q&A System v2.0', flush=True)
    print('='*70, flush=True)
    
    # ============================================================================
    # STEP 0: Auto-convert new PDFs (to json_auto/ for review)
    # ============================================================================
    print('\n[STEP 0] Checking for new PDFs to convert...', flush=True)
    try:
        from core.auto_processor import AutoProcessor
        
        processor = AutoProcessor(
            pdf_dir='data/pdf',
            json_dir='data/json_auto',  # ✅ Auto-converted files go here for review
            registry_file='data/.conversion_registry.json'
        )
        
        result = processor.process_all()
        
        if result['converted'] > 0:
            print(f"[AUTO] Converted {result['converted']} new PDFs to data/json_auto/", flush=True)
            print(f"[AUTO]  Review these files before approving for production", flush=True)
        elif result['total'] == 0:
            print(f"[AUTO] All PDFs are up-to-date", flush=True)
    
    except Exception as e:
        print(f'[AUTO]Auto-conversion error: {e}', flush=True)
        import traceback
        traceback.print_exc()
    
    # ============================================================================
    # STEP 1: Load Gemini API
    # ============================================================================
    print('\n[STEP 1] Loading Google AI API...', flush=True)
    
    # Try environment variable first (for cloud platforms)
    api_key = os.getenv('GOOGLE_API_KEY')
    
    # If not found, try .env file (for local development)
    if not api_key:
        print('[INFO] Loading from .env file...', flush=True)
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print('[ERROR] GOOGLE_API_KEY not found!', flush=True)
        raise Exception('Missing GOOGLE_API_KEY')
    
    genai.configure(api_key=api_key)
    print('[OK] Google API key loaded', flush=True)
    
    # ============================================================================
    # STEP 2: Initialize Gemini models
    # ============================================================================
    print('\n[STEP 2] Initializing AI models...', flush=True)
    
    try:
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        gemini_lite_model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # Test the model
        test_response = gemini_model.generate_content('Say "Ready" in one word')
        print(f'[OK] Models ready: {test_response.text.strip()}', flush=True)
        print('  - gemini-2.0-flash-exp (answer generation)', flush=True)
        print('  - gemini-2.0-flash-lite (intent detection)', flush=True)
    
    except Exception as e:
        print(f'[ERROR] Model initialization failed: {e}', flush=True)
        raise
    
    # ============================================================================
    # STEP 3: Load embedding model
    # ============================================================================
    print('\n[STEP 3] Loading embedding model...', flush=True)
    print(f'[INFO] Model: {EMBEDDING_MODEL}', flush=True)
    
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    print('[OK] Embedding model ready', flush=True)
    print('     Vietnamese-optimized PhoBERT', flush=True)
    
    # ============================================================================
    # STEP 4: Load legal documents (MANUAL ONLY - Production)
    # ============================================================================
    print('\n[STEP 4] Loading legal documents...', flush=True)
    
    json_manual_dir = Path('data/json_manual')
    json_auto_dir = Path('data/json_auto')
    
    # Check if manual directory exists
    if not json_manual_dir.exists():
        print(f'[ERROR] {json_manual_dir} not found!', flush=True)
        print(f'[HELP] Create directory: mkdir -p data/json_manual', flush=True)
        print(f'[HELP] Add verified JSON files to this directory', flush=True)
        raise Exception('json_manual directory required')
    
    all_chunks = []
    manual_files = []
    
    # Load ONLY from json_manual (production-ready files)
    print(f'[LOAD] Loading PRODUCTION files from: {json_manual_dir}', flush=True)
    
    for json_file in sorted(json_manual_dir.glob('*.json')):
        # Skip hidden/system files
        if json_file.name.startswith('.'):
            continue
        
        try:
            chunks, law_name = xu_ly_van_ban_phap_luat_json(str(json_file))
            all_chunks.extend(chunks)
            manual_files.append({
                'name': json_file.name,
                'chunks': len(chunks),
                'law': law_name
            })
            print(f'{json_file.name}: {len(chunks)} chunks', flush=True)
        
        except Exception as e:
            print(f' Failed to load {json_file.name}: {e}', flush=True)
    
    # Show auto-converted files (for info only - NOT loaded)
    if json_auto_dir.exists():
        auto_files = [f for f in json_auto_dir.glob('*.json') if not f.name.startswith('.')]
        
        if auto_files:
            print(f'\n[INFO] Found {len(auto_files)} auto-converted files (NOT LOADED)', flush=True)
            print(f'[INFO] Location: {json_auto_dir}', flush=True)
            print(f'[INFO] Review quality before approving for production', flush=True)
            
            for json_file in sorted(auto_files):
                print(f'{json_file.name} (needs manual review)', flush=True)
    
    # Validate we have data
    if not all_chunks:
        print('\n[ERROR] No manual JSON files found!', flush=True)
        print('[HELP] Place verified JSON files in: data/json_manual/', flush=True)
        print('[HELP] Example: cp your_law.json data/json_manual/', flush=True)
        raise Exception('No production data loaded')
    
    print(f'\n[OK] Loaded {len(all_chunks):,} chunks from {len(manual_files)} production files', flush=True)
    
    # ============================================================================
    # STEP 5: Build/Load search indexes
    # ============================================================================
    print('\n[STEP 5] Building search indexes...', flush=True)
    
    # Calculate data hash
    data_hash = get_data_hash(all_chunks)
    print(f'[INFO] Data hash: {data_hash}', flush=True)
    
    # Build BM25 index
    print('[INDEX] Building BM25 index...', flush=True)
    corpus = [tokenize_vi(chunk['content']) for chunk in all_chunks]
    bm25_index = build_or_load_bm25(corpus, data_hash)
    print('[OK] BM25 index ready', flush=True)
    
    # Build FAISS index
    print('[INDEX] Building FAISS index...', flush=True)
    faiss_index, corpus_embeddings = build_or_load_faiss(all_chunks, data_hash, embedder)
    print(f'[OK] FAISS index ready ({faiss_index.ntotal:,} vectors)', flush=True)
    
    # ============================================================================
    # Startup Complete
    # ============================================================================
    print('\n' + '='*70, flush=True)
    print('[STARTUP] System Ready!', flush=True)
    print('='*70, flush=True)
    print(f'  • Production files: {len(manual_files)}', flush=True)
    print(f'  • Total chunks: {len(all_chunks):,}', flush=True)
    print(f'  • Embeddings: {faiss_index.ntotal:,}', flush=True)
    print(f'  • Models: Gemini 2.0 Flash + Flash Lite', flush=True)
    print('='*70 + '\n', flush=True)
    
    # Application is running
    yield
    
    # Cleanup on shutdown
    print('[SHUTDOWN] Cleaning up resources...', flush=True)


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title='Legal Document Q&A API',
    description='Advanced RAG system for Vietnamese legal documents with production/review separation',
    version='2.0.0',
    lifespan=lifespan
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
    """Log validation errors for debugging"""
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
    return {
        "status": "healthy",
        "models_loaded": embedder is not None and gemini_model is not None,
        "total_chunks": len(all_chunks)
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Main Q&A endpoint with advanced search and intent detection"""
    start_time = time.time()
    timing = {}
    
    if not all_chunks:
        raise HTTPException(status_code=503, detail="System not ready")
    
    print(f'\n{"="*70}', flush=True)
    print(f'[INFO] Question: {request.question}', flush=True)
    print(f'[INFO] Model Mode: {request.model_mode.upper()}', flush=True)
    print(f'{"="*70}', flush=True)
    
    # Select models based on mode
    if request.model_mode == "fast":
        intent_model = gemini_lite_model
        answer_model = gemini_lite_model
        decompose_model = gemini_lite_model
        rerank_model = None
        use_advanced = False
        print('[MODE] ⚡ FAST - Flash Lite only', flush=True)
    else:
        intent_model = gemini_lite_model
        answer_model = gemini_model
        decompose_model = gemini_model
        rerank_model = gemini_model
        use_advanced = True
        print('[MODE] 🎯 QUALITY - Flash Lite + Flash', flush=True)
    
    # Search
    intent_start = time.time()
    
    if request.use_advanced:
        def enhanced_decompose_fn(query):
            return enhanced_decompose_query(
                query, 
                intent_model,
                gemini_flash_model=decompose_model,
                use_advanced=use_advanced
            )
        
        relevant_chunks = advanced_hybrid_search(
            query=request.question,
            all_chunks=all_chunks,
            bm25_index=bm25_index,
            faiss_index=faiss_index,
            embedder=embedder,
            tokenize_fn=tokenize_vi,
            enhanced_decompose_fn=enhanced_decompose_fn,
            gemini_model=rerank_model,
            use_advanced=use_advanced,
            top_k=5
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
    print(f'[TIMING] Search: {timing["search_ms"]}ms', flush=True)
    
    # Check if rejected
    if not relevant_chunks:
        total_time = round((time.time() - start_time) * 1000, 2)
        print(f'[TIMING] Total (rejected): {total_time}ms', flush=True)
        print(f'{"="*70}\n', flush=True)
        return {
            "answer": get_rejection_message(),
            "sources": [],
            "pdf_sources": [],
            "search_mode": mode,
            "timing": {
                "total_ms": total_time,
                "search_ms": timing['search_ms'],
                "generation_ms": 0,
                "status": "rejected"
            }
        }
    
    # Generate answer
    gen_start = time.time()
    
    if request.model_mode == "quality" and request.chat_history:
        print(f'[CONTEXT] Using chat history: {len(request.chat_history)} messages', flush=True)
        answer = generate_answer(
            request.question, 
            relevant_chunks, 
            answer_model, 
            chat_history=request.chat_history,
            use_advanced=use_advanced
        )
    else:
        answer = generate_answer(
            request.question, 
            relevant_chunks, 
            answer_model,
            use_advanced=use_advanced
        )
    
    timing['generation_ms'] = round((time.time() - gen_start) * 1000, 2)
    timing['total_ms'] = round((time.time() - start_time) * 1000, 2)
    
    print(f'[TIMING] Generation: {timing["generation_ms"]}ms', flush=True)
    print(f'[TIMING] ⚡ TOTAL: {timing["total_ms"]}ms', flush=True)
    print(f'{"="*70}\n', flush=True)
    
    # Format sources
    sources = [
        {"source": chunk["source"], "content": chunk["content"][:200]} 
        for chunk in relevant_chunks
    ]
    
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
            "llm_full": "gemini-2.0-flash-exp",
            "llm_lite": "gemini-2.0-flash-lite"
        },
        "intent_cache_size": get_cache_size()
    }


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback"""
    from datetime import datetime
    
    feedback_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback_logs')
    os.makedirs(feedback_dir, exist_ok=True)
    
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "query": request.query,
        "answer": request.answer,
        "context": request.context,
        "status": request.status,
        "comment": request.comment
    }
    
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


@app.post("/api/get-document")
async def get_document(request: dict):
    """Serve PDF as base64"""
    import base64
    
    filename = request.get('filename')
    if not filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(current_dir, 'data', 'pdf', filename)
    
    print(f"[PDF] Requested: {filename}", flush=True)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
    
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return {
        "filename": filename,
        "data": pdf_base64,
        "size": len(pdf_bytes),
        "type": "application/pdf"
    }


@app.get("/files")
async def get_files_status():
    """Get status of all files (manual vs auto-converted)"""
    registry_file = Path('data/.conversion_registry.json')
    registry = {}
    
    if registry_file.exists():
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    
    manual_dir = Path('data/json_manual')
    auto_dir = Path('data/json_auto')
    pdf_dir = Path('data/pdf')
    
    result = {
        'manual_files': [],
        'auto_files': [],
        'pending_pdfs': [],
        'summary': {}
    }
    
    # Manual files (in production)
    if manual_dir.exists():
        for json_file in sorted(manual_dir.glob('*.json')):
            if json_file.name.startswith('.'):
                continue
            
            pdf_name = None
            for pdf_file in pdf_dir.glob('*.pdf'):
                if registry.get(pdf_file.name, {}).get('json_file') == json_file.name:
                    pdf_name = pdf_file.name
                    break
            
            result['manual_files'].append({
                'json_file': json_file.name,
                'pdf_file': pdf_name,
                'status': 'production',
                'size': json_file.stat().st_size,
                'modified': json_file.stat().st_mtime
            })
    
    # Auto-converted files (need review)
    if auto_dir.exists():
        for json_file in sorted(auto_dir.glob('*.json')):
            if json_file.name.startswith('.'):
                continue
            
            pdf_name = None
            converted_at = None
            
            for pdf_file in pdf_dir.glob('*.pdf'):
                reg_entry = registry.get(pdf_file.name, {})
                if reg_entry.get('json_file') == json_file.name:
                    pdf_name = pdf_file.name
                    converted_at = reg_entry.get('converted_at')
                    break
            
            result['auto_files'].append({
                'json_file': json_file.name,
                'pdf_file': pdf_name,
                'status': 'needs_review',
                'converted_at': converted_at,
                'size': json_file.stat().st_size
            })
    
    # PDFs without JSON
    if pdf_dir.exists():
        for pdf_file in sorted(pdf_dir.glob('*.pdf')):
            if pdf_file.name not in registry:
                result['pending_pdfs'].append({
                    'pdf_file': pdf_file.name,
                    'status': 'not_converted',
                    'size': pdf_file.stat().st_size
                })
    
    result['summary'] = {
        'manual_count': len(result['manual_files']),
        'auto_count': len(result['auto_files']),
        'pending_count': len(result['pending_pdfs']),
        'total_in_production': len(result['manual_files'])
    }
    
    return result


@app.post("/admin/approve-file")
async def approve_auto_file(request: dict):
    """Move auto-converted file to manual (approve for production)"""
    json_filename = request.get('json_file')
    
    if not json_filename:
        raise HTTPException(status_code=400, detail="json_file required")
    
    auto_path = Path('data/json_auto') / json_filename
    manual_path = Path('data/json_manual') / json_filename
    
    if not auto_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found in json_auto: {json_filename}")
    
    if manual_path.exists():
        raise HTTPException(status_code=409, detail=f"File already exists in json_manual: {json_filename}")
    
    try:
        shutil.move(str(auto_path), str(manual_path))
        
        print(f"[ADMIN] ✅ Approved: {json_filename} → json_manual/", flush=True)
        
        return {
            "success": True,
            "message": f"✅ {json_filename} approved for production",
            "action": "restart_required",
            "note": "Restart the server to load this file"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move file: {e}")


@app.post("/admin/reject-file")
async def reject_auto_file(request: dict):
    """Delete auto-converted file (reject)"""
    json_filename = request.get('json_file')
    reason = request.get('reason', 'Quality issues')
    
    if not json_filename:
        raise HTTPException(status_code=400, detail="json_file required")
    
    auto_path = Path('data/json_auto') / json_filename
    
    if not auto_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {json_filename}")
    
    try:
        auto_path.unlink()
        
        print(f"[ADMIN] ❌ Rejected: {json_filename} - {reason}", flush=True)
        
        return {
            "success": True,
            "message": f"❌ {json_filename} deleted",
            "reason": reason,
            "note": "Create a manual JSON file to replace this"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")


# ============================================================================
# Helper Functions
# ============================================================================

def map_json_to_pdf(json_filename: str) -> str:
    """Map JSON filename to PDF filename"""
    mapping = {
        'luat_hon_nhan_hopnhat.json': 'luat_hon_nhan.pdf',
        'luat_dat_dai_hopnhat.json': 'luat_dat_dai.pdf',
        'luat_lao_donghopnhat.json': 'luat_lao_dong.pdf',
        'luat_dauthau_hopnhat.json': 'luat_dau_thau.pdf',
        'chuyen_giao_cong_nghe_hopnhat.json': 'luat_chuyen_giao_cong_nghe.pdf',
        'nghi_dinh_214_2025.json': 'nghi_dinh_214_2025.pdf',
    }
    
    if json_filename in mapping:
        return mapping[json_filename]
    
    # Fallback
    return json_filename.replace('_hopnhat.json', '.pdf').replace('.json', '.pdf')


def extract_pdf_metadata(chunk: dict) -> PDFSource:
    """Extract PDF metadata from chunk"""
    metadata = chunk.get('metadata', {})
    json_file = metadata.get('json_file', '')
    pdf_file = map_json_to_pdf(json_file) if json_file else 'unknown.pdf'
    
    article_num = metadata.get('article_num', '')
    section_num = metadata.get('section_num', '')
    
    full_reference = article_num
    if section_num:
        if 'Khoan' not in article_num and 'khoan' not in article_num.lower():
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
        article_num=full_reference
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 7860))
    uvicorn.run('app:app', host='0.0.0.0', port=port, reload=False)