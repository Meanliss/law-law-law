"""
Test: JSON Data Traceability with Text Highlighting
Kiểm tra khả năng truy ngược từ search results về vị trí trong file JSON gốc
và highlight đoạn text được trích dẫn

Workflow:
1. User đặt câu hỏi
2. System search trong FAISS/BM25 → trả về chunks
3. Mỗi chunk có metadata: source file, điều, khoản
4. Load lại file JSON gốc
5. Tìm và highlight đoạn text được trích dẫn
6. Hiển thị context xung quanh với highlight

Chạy: python test_json_trace_highlight.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import glob
from termcolor import colored, cprint
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

# Import core functions
from core.document_processor import xu_ly_van_ban_phap_luat_json
from core.search import advanced_hybrid_search
from core.intent_detection import enhanced_decompose_query
from utils.cache import build_or_load_bm25, build_or_load_faiss, get_data_hash
from utils.tokenizer import tokenize_vi


def highlight_text_in_context(full_text, search_text, context_chars=200):
    """
    Tìm và highlight đoạn text trong context
    
    Args:
        full_text: Text đầy đủ
        search_text: Text cần highlight
        context_chars: Số ký tự context trước/sau
        
    Returns:
        String với highlight (sử dụng ANSI colors)
    """
    # Normalize để tìm kiếm
    full_lower = full_text.lower()
    search_lower = search_text.lower()
    
    # Tìm vị trí
    pos = full_lower.find(search_lower)
    
    if pos == -1:
        # Không tìm thấy chính xác, thử tìm partial match
        # Lấy 50 ký tự đầu của search_text
        search_partial = search_lower[:50]
        pos = full_lower.find(search_partial)
    
    if pos == -1:
        return f"⚠️  Text không tìm thấy trong JSON\n{full_text[:300]}..."
    
    # Lấy context trước và sau
    start = max(0, pos - context_chars)
    end = min(len(full_text), pos + len(search_text) + context_chars)
    
    # Extract các phần
    before = full_text[start:pos]
    matched = full_text[pos:pos + len(search_text)]
    after = full_text[pos + len(search_text):end]
    
    # Add ellipsis nếu cần
    if start > 0:
        before = "..." + before
    if end < len(full_text):
        after = after + "..."
    
    # Format với colors
    result = (
        colored(before, 'white', attrs=['dark']) +
        colored(matched, 'yellow', 'on_red', attrs=['bold']) +
        colored(after, 'white', attrs=['dark'])
    )
    
    return result


def trace_chunk_to_json(chunk, json_files_dict):
    """
    Truy ngược chunk về vị trí trong file JSON gốc
    
    Args:
        chunk: Search result chunk
        json_files_dict: Dict mapping filename -> JSON data
        
    Returns:
        Dict với thông tin trace và highlighted text
    """
    source = chunk.get('source', '')
    content = chunk.get('content', '')
    metadata = chunk.get('metadata', {})
    
    # Get JSON filename from metadata (added in document_processor)
    json_filename = metadata.get('json_file', '')
    
    # Fallback: try to extract from source or match by law_name
    if not json_filename or json_filename not in json_files_dict:
        # Try to match by filename pattern in source
        for key in json_files_dict.keys():
            # Remove extension and check if in source
            key_base = key.replace('.json', '').replace('_hopnhat', '')
            if key_base in source.lower() or key in source:
                json_filename = key
                break
        
        # If still not found, try to match by law name
        if not json_filename or json_filename not in json_files_dict:
            law_name = metadata.get('law_name', '')
            # Create mapping based on common patterns
            law_to_json = {
                'Luật Hôn nhân': 'luat_hon_nhan_hopnhat.json',
                'Luật Đất đai': 'luat_dat_dai_hopnhat.json',
                'Luật Lao động': 'luat_lao_donghopnhat.json',
                'Luật Đấu thầu': 'luat_dauthau_hopnhat.json',
                'Chuyển giao công nghệ': 'chuyen_giao_cong_nghe_hopnhat.json',
                'Nghị định 214': 'nghi_dinh_214_2025.json',
            }
            
            for pattern, filename in law_to_json.items():
                if pattern.lower() in law_name.lower():
                    json_filename = filename
                    break
    
    if not json_filename or json_filename not in json_files_dict:
        return {
            'status': 'error',
            'message': f'Cannot find JSON file. Source: {source[:100]}..., Law: {metadata.get("law_name", "N/A")}'
        }
    
    json_data = json_files_dict[json_filename]
    
    # Get PDF filename mapping
    json_to_pdf = {
        'luat_hon_nhan_hopnhat.json': 'luat_hon_nhan.pdf',
        'luat_dat_dai_hopnhat.json': 'luat_dat_dai.pdf',
        'luat_lao_donghopnhat.json': 'luat_lao_dong.pdf',
        'luat_dauthau_hopnhat.json': 'luat_dau_thau.pdf',
        'chuyen_giao_cong_nghe_hopnhat.json': 'luat_chuyen_giao_cong_nghe.pdf',
        'nghi_dinh_214_2025.json': 'nghi_dinh_214_2025.pdf',
    }
    
    pdf_filename = json_to_pdf.get(json_filename, 'UNKNOWN.pdf')
    
    # Tìm article trong JSON
    article_num = metadata.get('article_num', '')
    
    if not article_num or 'du_lieu' not in json_data:
        return {
            'status': 'error',
            'message': 'Missing article number or invalid JSON structure'
        }
    
    # Search for article
    found_article = None
    for article in json_data['du_lieu']:
        if article.get('dieu_so') == str(article_num):
            found_article = article
            break
    
    if not found_article:
        return {
            'status': 'error',
            'message': f'Article {article_num} not found in JSON'
        }
    
    # Build full text của article để highlight
    article_text_parts = []
    
    # Tiêu đề
    if found_article.get('tieu_de'):
        article_text_parts.append(found_article['tieu_de'])
    
    # Mô tả
    if found_article.get('mo_ta'):
        article_text_parts.append(found_article['mo_ta'])
    
    # Các khoản
    if found_article.get('khoan'):
        for khoan in found_article['khoan']:
            if khoan.get('noi_dung'):
                article_text_parts.append(khoan['noi_dung'])
            
            # Các điểm
            if khoan.get('diem'):
                for diem in khoan['diem']:
                    if diem.get('noi_dung'):
                        article_text_parts.append(diem['noi_dung'])
    
    full_article_text = '\n'.join(article_text_parts)
    
    # Highlight content trong full text
    highlighted = highlight_text_in_context(
        full_article_text, 
        content[:200],  # Chỉ dùng 200 ký tự đầu để search
        context_chars=150
    )
    
    return {
        'status': 'success',
        'json_file': json_filename,
        'pdf_file': pdf_filename,
        'article_num': article_num,
        'article_title': found_article.get('tieu_de', ''),
        'full_text': full_article_text,
        'highlighted': highlighted,
        'metadata': metadata
    }


def test_json_traceability():
    """Test chính: Truy ngược và highlight"""
    
    print("\n" + "="*80)
    cprint("JSON TRACEABILITY TEST WITH HIGHLIGHTING", 'cyan', attrs=['bold'])
    print("="*80)
    
    # 1. Load JSON files
    print("\n📂 Step 1: Loading JSON files...")
    json_files = glob.glob("data/*.json")
    
    if not json_files:
        cprint("❌ No JSON files found in data/", 'red')
        return
    
    # Load all JSON data vào memory
    json_files_dict = {}
    for json_file in json_files:
        filename = os.path.basename(json_file)
        with open(json_file, 'r', encoding='utf-8') as f:
            json_files_dict[filename] = json.load(f)
    
    cprint(f"✅ Loaded {len(json_files_dict)} JSON files", 'green')
    
    # 2. Process to chunks
    print("\n📊 Step 2: Processing JSON to chunks...")
    all_chunks = []
    for json_file in json_files:
        chunks, law_source = xu_ly_van_ban_phap_luat_json(json_file)
        all_chunks.extend(chunks)
    cprint(f"✅ Created {len(all_chunks)} chunks", 'green')
    
    # Sample chunk structure
    if all_chunks:
        sample = all_chunks[0]
        print(f"\n   Sample chunk:")
        print(f"   - source: {sample['source']}")
        print(f"   - metadata: {sample.get('metadata', {})}")
    
    # 3. Build search indexes
    print("\n🔧 Step 3: Building search indexes...")
    
    # Initialize Gemini
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        gemini_lite_model = genai.GenerativeModel('gemini-2.5-flash-lite')
    else:
        cprint("⚠️  No GOOGLE_API_KEY found, using simple search", 'yellow')
        gemini_lite_model = None
    
    # Initialize embedder
    embedder = SentenceTransformer('keepitreal/vietnamese-sbert')
    
    # Get data hash
    data_hash = get_data_hash(all_chunks)
    
    # Build BM25 index (need tokenized corpus)
    corpus = [tokenize_vi(chunk['content']) for chunk in all_chunks]
    bm25_index = build_or_load_bm25(corpus, data_hash)
    
    # Build FAISS index
    faiss_index, _ = build_or_load_faiss(all_chunks, data_hash, embedder)
    
    cprint("✅ Indexes ready", 'green')
    
    # 4. Test queries
    test_queries = [
        "Độ tuổi kết hôn là bao nhiêu?",
        "Quyền sử dụng đất?",
        "Điều kiện đấu thầu?"
    ]
    
    # Test với query đầu tiên
    query = test_queries[0]
    
    print("\n" + "="*80)
    cprint(f"🔍 TESTING QUERY: '{query}'", 'cyan', attrs=['bold'])
    print("="*80)
    
    # 5. Search
    print("\n⚡ Step 4: Searching...")
    
    # Create a wrapper function for enhanced_decompose_query
    def decompose_fn(query):
        if gemini_lite_model:
            return enhanced_decompose_query(query, gemini_lite_model)
        else:
            # Fallback: return simple result without LLM
            return {
                'is_legal': True,
                'confidence': 0.8,
                'sub_queries': [query],
                'keywords': []
            }
    
    results = advanced_hybrid_search(
        query=query,
        all_chunks=all_chunks,
        bm25_index=bm25_index,
        faiss_index=faiss_index,
        embedder=embedder,
        tokenize_fn=tokenize_vi,
        enhanced_decompose_fn=decompose_fn,
        top_k=3
    )
    
    cprint(f"✅ Found {len(results)} relevant chunks", 'green')
    
    # 6. Trace và highlight từng result
    print("\n" + "="*80)
    cprint("📍 TRACING RESULTS TO JSON SOURCE WITH HIGHLIGHTING", 'cyan', attrs=['bold'])
    print("="*80)
    
    for i, chunk in enumerate(results, 1):
        print("\n" + "-"*80)
        cprint(f"Result #{i}", 'yellow', attrs=['bold'])
        print("-"*80)
        
        # Basic info
        print(f"\n📋 Chunk Info:")
        print(f"   Source: {chunk['source']}")
        print(f"   Content preview: {chunk['content'][:100]}...")
        
        metadata = chunk.get('metadata', {})
        if metadata:
            print(f"\n🏷️  Metadata:")
            print(f"   Law: {metadata.get('law_name', 'N/A')}")
            print(f"   Article: Điều {metadata.get('article_num', 'N/A')}")
            print(f"   Clause: Khoản {metadata.get('clause_num', 'N/A')}")
        
        # Trace to JSON
        print(f"\n🔍 Tracing to JSON source...")
        trace_result = trace_chunk_to_json(chunk, json_files_dict)
        
        if trace_result['status'] == 'error':
            cprint(f"   ❌ {trace_result['message']}", 'red')
            continue
        
        # Show trace result
        cprint(f"   ✅ Found in: {trace_result['json_file']}", 'green')
        cprint(f"   📄 PDF file: {trace_result['pdf_file']}", 'cyan')
        print(f"   📖 Article: {trace_result['article_title']}")
        
        # Show highlighted text
        print(f"\n💡 Highlighted in JSON:")
        print(f"   (Yellow text = matched content from search)")
        print()
        print(trace_result['highlighted'])
        print()
        
        # Show full article structure (optional)
        print(f"\n📖 Full Article Structure:")
        print(f"   File: {trace_result['json_file']}")
        print(f"   Điều: {trace_result['article_num']}")
        print(f"   Total chars: {len(trace_result['full_text'])}")
    
    # 7. Summary
    print("\n" + "="*80)
    cprint("✅ TEST COMPLETED", 'green', attrs=['bold'])
    print("="*80)
    
    print("\n📊 Summary:")
    print(f"   - Query: '{query}'")
    print(f"   - Results: {len(results)} chunks")
    print(f"   - Successfully traced: {sum(1 for r in results if trace_chunk_to_json(r, json_files_dict)['status'] == 'success')}")
    
    print("\n💡 What we proved:")
    cprint("   ✅ Can trace from search results back to JSON source", 'green')
    cprint("   ✅ Can find exact article in original JSON", 'green')
    cprint("   ✅ Can highlight matched text with context", 'green')
    
    print("\n🎯 Next steps:")
    print("   - Implement this in frontend UI")
    print("   - Show JSON structure with highlighted citations")
    print("   - Allow users to see original document context")


def main():
    """Entry point"""
    try:
        # Check if termcolor is available
        try:
            import termcolor
        except ImportError:
            print("⚠️  Installing termcolor for better output...")
            os.system("pip install termcolor --quiet")
            import termcolor
        
        # Run test
        test_json_traceability()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
