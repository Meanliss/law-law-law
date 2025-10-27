"""
Build domain indices from pre-organized files
Files should already be in:
- data/domains/{domain_id}/raw/*.json
- data/domains/{domain_id}/pdfs/*.pdf
"""

import json
import pickle
from pathlib import Path
import sys
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.tokenizer import tokenize_vi as tokenize_vietnamese
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

# ===== CONFIG =====
EMBEDDING_MODEL = "keepitreal/vietnamese-sbert"

# Load domain registry
with open("data/domain_registry.json", "r", encoding="utf-8") as f:
    DOMAIN_REGISTRY = json.load(f)

def build_domain(domain_id: str):
    """Build indices for a single domain from files in domains/{domain_id}/raw/"""
    
    print(f"\n{'='*60}")
    print(f"🔨 Building domain: {domain_id}")
    print(f"{'='*60}\n")
    
    domain_dir = Path(f"data/domains/{domain_id}")
    
    if not domain_dir.exists():
        print(f"⚠️ Domain directory not found: {domain_dir}")
        return
    
    # Check if already built (has all required files)
    required_files = ['chunks.jsonl', 'tokens.pkl', 'bm25.pkl', 'faiss.index', 'metadata.json']
    if all((domain_dir / f).exists() for f in required_files):
        print(f"✅ Domain '{domain_id}' already built - SKIPPING")
        print(f"   Location: {domain_dir}")
        # Show metadata
        with open(domain_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            meta = json.load(f)
            print(f"   Chunks: {meta.get('total_chunks', 0)}")
        return
    
    # Check for JSON files
    json_files = list((domain_dir / "raw").glob("*.json"))
    if not json_files:
        print(f"⚠️ No JSON files found in {domain_dir / 'raw'}")
        return
    
    print(f"📂 Found {len(json_files)} JSON file(s):")
    for f in json_files:
        print(f"  - {f.name}")
    
    # ===== STEP 1: Load and chunk data =====
    print("\n📖 Loading and chunking data...")
    chunks = []
    
    for json_path in json_files:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(data, dict) and 'du_lieu' in data:
                # Format: { "nguon": "...", "du_lieu": [...] }
                items = data['du_lieu']
                print(f"  📄 {json_path.name}: {len(items)} articles")
            elif isinstance(data, list):
                # Format: [{ ... }, { ... }]
                items = data
                print(f"  📄 {json_path.name}: {len(items)} items")
            else:
                print(f"  ⚠️ Unknown format in {json_path.name}")
                continue
            
            # Process each item
            for item in items:
                # Create content from available fields
                if 'content' in item:
                    content = item['content']
                else:
                    # Build content from legal document structure
                    parts = []
                    if 'chuong' in item:
                        parts.append(item['chuong'])
                    if 'tieu_de' in item:
                        parts.append(item['tieu_de'])
                    if 'mo_ta' in item and item['mo_ta']:
                        parts.append(item['mo_ta'])
                    if 'khoan' in item and isinstance(item['khoan'], list):
                        for khoan in item['khoan']:
                            if isinstance(khoan, dict) and 'noi_dung' in khoan:
                                parts.append(khoan['noi_dung'])
                    content = '\n'.join(parts)
                
                if not content.strip():
                    continue
                
                # Find corresponding PDF file
                pdf_file = ''
                pdf_files = list((domain_dir / "pdfs").glob("*.pdf"))
                if pdf_files:
                    pdf_file = pdf_files[0].name  # Use first PDF
                
                chunks.append({
                    'id': f"{domain_id}_{len(chunks)}",
                    'content': content,
                    'json_file': json_path.name,
                    'pdf_file': pdf_file,
                    'article_num': item.get('article_num', item.get('dieu_so', '')),
                    'page_num': item.get('page_num', ''),
                    'domain_id': domain_id,
                    'domain_name': DOMAIN_REGISTRY.get(domain_id, {}).get('name', domain_id)
                })
    
    print(f"\n✅ Total chunks: {len(chunks)}")
    
    if len(chunks) == 0:
        print("⚠️ No chunks to process!")
        return
    
    # ===== STEP 2: Save chunks as JSONL =====
    print("\n💾 Saving chunks.jsonl...")
    chunks_path = domain_dir / "chunks.jsonl"
    with open(chunks_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    print(f"  ✓ Saved {len(chunks)} chunks")
    
    # ===== STEP 3: Tokenize =====
    print("\n🔤 Tokenizing chunks...")
    tokenized_chunks = [tokenize_vietnamese(chunk['content']) for chunk in chunks]
    
    tokens_path = domain_dir / "tokens.pkl"
    with open(tokens_path, 'wb') as f:
        pickle.dump(tokenized_chunks, f)
    print(f"  ✓ Saved tokens.pkl")
    
    # ===== STEP 4: Build BM25 index =====
    print("\n🔍 Building BM25 index...")
    bm25_index = BM25Okapi(tokenized_chunks)
    
    bm25_path = domain_dir / "bm25.pkl"
    with open(bm25_path, 'wb') as f:
        pickle.dump(bm25_index, f)
    print(f"  ✓ Saved bm25.pkl")
    
    # ===== STEP 5: Build FAISS index =====
    print("\n🧠 Building FAISS index...")
    print(f"  Loading embedder: {EMBEDDING_MODEL}...")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    
    print(f"  Encoding {len(chunks)} chunks...")
    texts = [chunk['content'] for chunk in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    
    # Build FAISS index
    import faiss
    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings)
    
    faiss_path = domain_dir / "faiss.index"
    faiss.write_index(faiss_index, str(faiss_path))
    print(f"  ✓ Saved faiss.index ({dimension}D, {faiss_index.ntotal} vectors)")
    
    # ===== STEP 6: Save metadata =====
    metadata = {
        'domain_id': domain_id,
        'domain_name': DOMAIN_REGISTRY.get(domain_id, {}).get('name', domain_id),
        'total_chunks': len(chunks),
        'json_files': [f.name for f in json_files],
        'pdf_files': [f.name for f in (domain_dir / "pdfs").glob("*.pdf")],
        'embedding_model': EMBEDDING_MODEL,
        'embedding_dim': dimension
    }
    
    metadata_path = domain_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"\n📊 Saved metadata.json")
    
    print(f"\n🎉 Domain '{domain_id}' built successfully!")
    print(f"  Location: {domain_dir}")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Files: chunks.jsonl, tokens.pkl, bm25.pkl, faiss.index, metadata.json")


def main():
    """Build all domains from registry"""
    print("🚀 Building all domains...")
    
    for domain_id in DOMAIN_REGISTRY.keys():
        try:
            build_domain(domain_id)
        except Exception as e:
            print(f"\n❌ Error building domain '{domain_id}': {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*60)
    print("✅ All domains built!")
    print("="*60)


if __name__ == "__main__":
    main()
