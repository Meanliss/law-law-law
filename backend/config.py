"""
Configuration and Constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Model Names
GEMINI_FULL_MODEL = 'gemini-2.5-flash'
GEMINI_LITE_MODEL = 'gemini-2.5-flash-lite'
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'

# Search Parameters
DEFAULT_TOP_K = 8
BM25_WEIGHT = 0.4
FAISS_WEIGHT = 0.6

# Cache Paths
CACHE_DIR = 'cache'
BM25_CACHE = f'{CACHE_DIR}/bm25_index.pkl'
FAISS_CACHE = f'{CACHE_DIR}/embeddings.pkl'

# Data Path
DATA_DIR = 'data'

# Intent Detection Keywords
LEGAL_KEYWORDS = {
    'primary': [
        'luật', 'pháp luật', 'quy định', 'điều', 'khoản', 'điểm', 
        'nghị định', 'thông tư', 'bộ luật', 'quyền', 'nghĩa vụ',
        'hợp đồng', 'tài sản', 'kết hôn', 'ly hôn', 'lao động',
        'đất đai', 'hình sự', 'dân sự', 'tố tụng', 'hành chính',
        'đấu thầu', 'chuyển giao công nghệ', 'vi phạm', 'xử phạt',
        'tuổi', 'độ tuổi'
    ],
    'secondary': [
        'khiếu nại', 'tố cáo', 'án', 'tòa', 'bồi thường', 'trách nhiệm',
        'hợp pháp', 'quy trình', 'đăng ký', 'cấp phép', 'thuế', 'phí',
        'lệ phí', 'thủ tục', 'điều kiện', 'tiêu chuẩn', 'quyết định',
        'gia đình', 'con cái', 'cha mẹ', 'vợ chồng', 'di sản'
    ]
}

IRRELEVANT_PATTERNS = [
    r'\b(thời tiết|bóng đá|game|phim|nhạc|ăn uống|du lịch)\b',
    r'\b(nấu ăn|công thức|món ăn|quán|nhà hàng|cafe)\b',
    r'\b(bệnh|thuốc|chữa|triệu chứng|y tế)\b',
    r'\b(laptop|điện thoại|máy tính|cấu hình|smartphone)\b',
    r'\b(toán|vật lý|hóa học|sinh học|lịch sử|địa lý)\b',
    r'\b(chào|xin chào|hello|hi|hey)\b'
]

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

# Intent Detection Thresholds
INTENT_KEYWORD_ACCEPT_THRESHOLD = 0.4
INTENT_KEYWORD_UNCERTAIN_THRESHOLD = 0.15
INTENT_CONFIDENCE_REJECT_THRESHOLD = 0.7
