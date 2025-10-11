"""
Vietnamese Tokenization Module
"""

import re
from typing import List
from underthesea import word_tokenize


def tokenize_vi(text: str) -> List[str]:
    """
    Tokenize Vietnamese text using underthesea
    
    Args:
        text: Input Vietnamese text
    
    Returns:
        List of tokens
    """
    try:
        # Lowercase
        text = text.lower()
        
        # Remove special characters but keep Vietnamese marks
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', ' ', text)
        
        # Tokenize with underthesea
        tokens = word_tokenize(text, format="text").split()
        
        return tokens
    except Exception as e:
        print(f'[WARN] Tokenization error: {e}, fallback to split()')
        return text.lower().split()
