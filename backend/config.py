"""
Configuration and Constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Model Names
GEMINI_FLASH_MODEL = 'gemini-2.5-flash'  # Fast mode - answer generation
GEMINI_PRO_MODEL = 'gemini-2.5-pro'  # Quality mode - answer generation
GEMINI_LITE_MODEL = 'gemini-2.5-flash-lite'  # Intent detection, decomposition

# Embedding Model
# PhoBERT requires special handling, use multilingual model optimized for Vietnamese
# EMBEDDING_MODEL = 'vinai/phobert-base'  # PhoBERT (not compatible with SentenceTransformers directly)
# EMBEDDING_MODEL = 'keepitreal/vietnamese-sbert'  # Vietnamese-optimized SBERT (768-dim, better than MiniLM)
EMBEDDING_MODEL = 'models/embedding-001'  # Gemini Embedding (768-dim)

# Search Parameters
DEFAULT_TOP_K = 8
BM25_WEIGHT = 0.7
FAISS_WEIGHT = 0.3

# Cache Paths
CACHE_DIR = 'cache'
BM25_CACHE = f'{CACHE_DIR}/bm25_index.pkl'
FAISS_CACHE = f'{CACHE_DIR}/embeddings.pkl'

# Data Path
DATA_DIR = 'data'

# ============================================================================
# ⚠️ LEGACY: Intent Detection Keywords (KHÔNG DÙNG NỮA - Đã chuyển sang LLM)
# ============================================================================
# LEGAL_KEYWORDS = {
#     'primary': [...],
#     'secondary': [...]
# }
# IRRELEVANT_PATTERNS = [...]
# INTENT_KEYWORD_ACCEPT_THRESHOLD = 0.4
# INTENT_KEYWORD_UNCERTAIN_THRESHOLD = 0.2
# ============================================================================

# Intent Detection Thresholds (chỉ dùng cho LLM)
INTENT_CONFIDENCE_REJECT_THRESHOLD = 0.7  # Reject nếu confidence >= threshold và is_legal=False

# Query Expansion Rules
QUERY_EXPANSION_RULES = {
    # Marriage law
    r'(độ )?tuổi\s+kết\s*hôn': [
        'độ tuổi kết hôn',
        'điều kiện kết hôn', 
        'quy định về kết hôn',
        'yêu cầu kết hôn'
    ],
    r'ly\s*hôn': [
        'ly hôn',
        'chia tài sản khi ly hôn',
        'thủ tục ly hôn',
        'quyền nuôi con khi ly hôn'
    ],
    
    # Labor law
    r'quyền\s+(lợi\s+)?lao\s*động': [
        'quyền lợi người lao động',
        'nghĩa vụ người lao động',
        'hợp đồng lao động',
        'chế độ lao động'
    ],
    r'thai\s*sản': [
        'chế độ thai sản',
        'nghỉ thai sản',
        'quyền lợi thai sản',
        'bảo vệ lao động nữ'
    ],
    r'sa\s*thải|đuổi\s*việc': [
        'sa thải lao động',
        'quyền lợi khi bị sa thải',
        'điều kiện sa thải hợp pháp',
        'bồi thường sa thải'
    ],
    
    # Land law
    r'(mua\s*bán|chuyển\s*nhượng)\s+đất': [
        'mua bán đất đai',
        'điều kiện chuyển nhượng đất',
        'thủ tục mua bán đất',
        'quyền sử dụng đất'
    ],
    r'thừa\s*kế\s+đất': [
        'thừa kế đất đai',
        'điều kiện thừa kế',
        'thủ tục thừa kế',
        'chia thừa kế'
    ],
    
    # Contract law
    r'hợp\s*đồng': [
        'hợp đồng hợp pháp',
        'điều kiện hợp đồng',
        'vi phạm hợp đồng',
        'chấm dứt hợp đồng'
    ],
    
    # Criminal law
    r'hình\s*sự|tội\s+phạm': [
        'quy định hình sự',
        'mức án',
        'tình tiết giảm nhẹ',
        'tình tiết tăng nặng'
    ],
    
    # Bidding law
    r'đấu\s*thầu': [
        'quy định đấu thầu',
        'điều kiện tham gia đấu thầu',
        'thủ tục đấu thầu',
        'vi phạm trong đấu thầu'
    ],
    
    # Technology transfer
    r'chuyển\s*giao\s+công\s*nghệ': [
        'chuyển giao công nghệ',
        'hợp đồng chuyển giao công nghệ',
        'điều kiện chuyển giao',
        'quyền sở hữu trí tuệ'
    ],
}

# ⚠️ LEGACY: Không dùng nữa (đã chuyển sang LLM)
# INTENT_KEYWORD_ACCEPT_THRESHOLD = 0.4
# INTENT_KEYWORD_UNCERTAIN_THRESHOLD = 0.15
