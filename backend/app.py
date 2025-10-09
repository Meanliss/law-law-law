from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import json
import os
import pickle
import re
import hashlib
from collections import defaultdict
import numpy as np
import faiss
import google.generativeai as genai
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from underthesea import word_tokenize
import uvicorn

class QuestionRequest(BaseModel):
    question: str
    use_advanced: bool = True

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]
    search_mode: str

class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    total_chunks: int

app = FastAPI(
    title='Legal Document Q&A API',
    description='Advanced RAG system for Vietnamese legal documents',
    version='1.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

all_chunks = []
bm25_index = None
faiss_index = None
corpus_embeddings = None
embedder = None
gemini_model = None

def get_data_hash(all_chunks):
    content = json.dumps([c.get('content', '')[:100] for c in all_chunks], sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

def tokenize_vi(text):
    if not text:
        return []
    try:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = word_tokenize(text, format='text').split()
        return tokens
    except Exception:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()

def xu_ly_van_ban_phap_luat_json(file_path):
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f'[ERROR] Khong tim thay file: {file_path}')
        return [], ''
    except json.JSONDecodeError:
        print(f'[ERROR] File khong hop le: {file_path}')
        return [], ''

    nguon_luat = data.get('nguon', 'Khong ro nguon')

    for dieu in data.get('du_lieu', []):
        dieu_so = dieu.get('dieu_so')
        if not dieu_so or not str(dieu_so).strip().isdigit():
            continue

        base_source = f'{nguon_luat}, Dieu {dieu_so}'
        base_content = dieu.get('noi_dung_hien_hanh', f"{dieu.get('tieu_de', '')}. {dieu.get('mo_ta', '')}".strip())
        
        base_metadata = {'law_name': nguon_luat, 'article_num': dieu_so, 'level': 'article'}
        
        if 'nguon_sua_doi' in dieu:
            base_source += f' (sua doi boi {dieu["nguon_sua_doi"]})'
            base_metadata['modified_by'] = dieu['nguon_sua_doi']

        if not dieu.get('khoan'):
            chunks.append({'source': base_source, 'content': base_content, 'metadata': base_metadata})
            continue

        for khoan in dieu['khoan']:
            khoan_source = f'{base_source}, Khoan {khoan.get("khoan_so", "")}'
            khoan_content = khoan.get('noi_dung_hien_hanh', khoan.get('noi_dung', ''))
            
            khoan_metadata = base_metadata.copy()
            khoan_metadata.update({'clause_num': khoan.get('khoan_so', ''), 'level': 'clause'})
            
            if 'nguon_sua_doi' in khoan:
                khoan_source += f' (sua doi boi {khoan["nguon_sua_doi"]})'
                khoan_metadata['modified_by'] = khoan['nguon_sua_doi']

            if not khoan.get('diem'):
                chunks.append({'source': khoan_source, 'content': khoan_content, 'metadata': khoan_metadata})
                continue
            
            for diem in khoan.get('diem', []):
                diem_source = f'{khoan_source}, Diem {diem.get("diem_so", "")}'
                diem_content = diem.get('noi_dung_hien_hanh', diem.get('noi_dung', ''))
                
                diem_metadata = khoan_metadata.copy()
                diem_metadata.update({'point_num': diem.get('diem_so', ''), 'level': 'point'})
                
                if 'nguon_sua_doi' in diem:
                    diem_source += f' (sua doi boi {diem["nguon_sua_doi"]})'
                    diem_metadata['modified_by'] = diem['nguon_sua_doi']
                
                chunks.append({'source': diem_source, 'content': diem_content, 'metadata': diem_metadata})
                        
    return chunks, nguon_luat

def build_or_load_bm25(corpus, data_hash, cache_path='cache/bm25_index.pkl'):
    hash_path = cache_path + '.hash'
    
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
    
    bm25 = BM25Okapi(corpus)
    
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(bm25, f)
    with open(hash_path, 'w') as f:
        f.write(data_hash)
    
    print('[OK] Da luu BM25 index vao cache')
    return bm25

def build_or_load_faiss(chunks, data_hash, model, cache_path='cache/embeddings.pkl'):
    hash_path = cache_path + '.hash'
    
    if os.path.exists(cache_path) and os.path.exists(hash_path):
        with open(hash_path, 'r') as f:
            saved_hash = f.read().strip()
        
        if saved_hash == data_hash:
            print('[INFO] FAISS cache hop le, dang tai tu cache...')
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                return data['index'], data['embeddings']
        else:
            print('[WARN] Du lieu da thay doi, dang xay dung lai FAISS index...')
    else:
        print('[INFO] Chua co cache, dang tao FAISS index...')
    
    contents = [chunk['content'] for chunk in chunks]
    print(f'[INFO] Dang embedding {len(contents)} chunks...')
    embeddings = model.encode(contents, show_progress_bar=True, convert_to_numpy=True)
    
    faiss.normalize_L2(embeddings)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump({'index': index, 'embeddings': embeddings}, f)
    with open(hash_path, 'w') as f:
        f.write(data_hash)
    
    print('[OK] Da luu FAISS index vao cache')
    return index, embeddings

def decompose_query(question: str) -> List[str]:
    try:
        prompt = f'''Phan tich cau hoi phap ly thanh cac y chinh.
Cau hoi: {question}
Tra ve danh sach cac sub-query (moi dong 1 sub-query):'''
        
        response = gemini_model.generate_content(prompt)
        sub_queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
        return sub_queries if sub_queries else [question]
    except Exception:
        return [question]

def advanced_hybrid_search(query: str, top_k: int = 8):
    sub_queries = decompose_query(query)
    print(f'[INFO] Decomposed query: {sub_queries}')
    
    combined_scores = defaultdict(float)
    seen_chunks = set()
    
    for sub_q in sub_queries:
        query_tokens = tokenize_vi(sub_q)
        bm25_scores = bm25_index.get_scores(query_tokens)
        
        query_embedding = embedder.encode([sub_q], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        faiss_scores, faiss_indices = faiss_index.search(query_embedding, top_k * 2)
        
        for i, score in enumerate(bm25_scores):
            if i not in seen_chunks:
                combined_scores[i] += score * 0.4
        
        for idx, score in zip(faiss_indices[0], faiss_scores[0]):
            if idx != -1 and idx not in seen_chunks:
                combined_scores[idx] += score * 0.6
        
        seen_chunks.update(range(len(all_chunks)))
    
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

def simple_search(query: str, top_k: int = 8):
    query_tokens = tokenize_vi(query)
    bm25_scores = bm25_index.get_scores(query_tokens)
    
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    faiss_scores, faiss_indices = faiss_index.search(query_embedding, top_k)
    
    combined_scores = defaultdict(float)
    for i, score in enumerate(bm25_scores):
        combined_scores[i] = score * 0.4
    
    for idx, score in zip(faiss_indices[0], faiss_scores[0]):
        if idx != -1:
            combined_scores[idx] += score * 0.6
    
    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results = [all_chunks[idx] for idx, _ in ranked]
    
    return results

def generate_answer(question: str, context: List[Dict]) -> str:
    context_text = '\n\n'.join([
        f"[{i+1}] {chunk['source']}\n{chunk['content']}"
        for i, chunk in enumerate(context)
    ])
    
    prompt = f'''Ban la chuyen gia phap ly Viet Nam. Hay tra loi cau hoi du tren co so van ban phap luat duoi day.

NGON NANG VIET NAM:
{context_text}

CAU HOI: {question}

YEU CAU:
- Tra loi chinh xac, cu the, de hieu
- Ket hop tat ca van ban lien quan
- Neu ro so Dieu, Khoan, Diem
- Neu co thay doi, ghi ro nguon sua doi

TRA LOI:'''
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f'[ERROR] Gemini API error: {e}')
        return 'Xin loi, khong the tao cau tra loi luc nay.'

@app.on_event("startup")
async def startup_event():
    global all_chunks, bm25_index, faiss_index, corpus_embeddings, embedder, gemini_model
    
    print('[STARTUP] Dang khoi dong Legal Q&A System...')
    
    # Load Gemini API
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print('[ERROR] GOOGLE_API_KEY not found in .env file!')
        raise Exception('Missing GOOGLE_API_KEY')
    
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    print('[OK] Google AI da san sang')
    
    # Load embedder model
    print('[INFO] Dang tai SentenceTransformer model...')
    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print('[OK] Model da san sang')
    
    # Load legal documents
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
    
    # Build/Load indexes with hash checking
    data_hash = get_data_hash(all_chunks)
    print(f'[INFO] Data hash: {data_hash}')
    
    corpus = [tokenize_vi(chunk['content']) for chunk in all_chunks]
    bm25_index = build_or_load_bm25(corpus, data_hash)
    
    faiss_index, corpus_embeddings = build_or_load_faiss(all_chunks, data_hash, embedder)
    
    print('[SUCCESS] Server san sang!')

@app.get("/", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": embedder is not None and gemini_model is not None,
        "total_chunks": len(all_chunks)
    }

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    if not all_chunks:
        raise HTTPException(status_code=503, detail="System not ready")
    
    print(f'[INFO] Question: {request.question}')
    
    if request.use_advanced:
        relevant_chunks = advanced_hybrid_search(request.question, top_k=8)
        mode = "advanced"
    else:
        relevant_chunks = simple_search(request.question, top_k=8)
        mode = "simple"
    
    answer = generate_answer(request.question, relevant_chunks)
    
    sources = [{"source": chunk["source"], "content": chunk["content"][:200]} for chunk in relevant_chunks]
    
    return {
        "answer": answer,
        "sources": sources,
        "search_mode": mode
    }

@app.get("/stats")
async def get_stats():
    laws = defaultdict(int)
    for chunk in all_chunks:
        law_name = chunk.get('metadata', {}).get('law_name', 'Unknown')
        laws[law_name] += 1
    
    return {
        "total_chunks": len(all_chunks),
        "laws": dict(laws),
        "models": {
            "embedder": "paraphrase-multilingual-MiniLM-L12-v2",
            "llm": "gemini-2.0-flash-exp"
        }
    }

if __name__ == '__main__':
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=True)
