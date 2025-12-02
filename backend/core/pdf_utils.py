"""
PDF Utilities for Page Detection
"""
import re
from pathlib import Path
from typing import Optional, Dict
import pypdf

# Simple in-memory cache: {(pdf_path, article_num): page_num}
_page_cache: Dict[str, int] = {}

def find_article_page(pdf_path: str, article_num: str) -> Optional[int]:
    """
    Find the page number where a specific article starts in a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        article_num: Article number (e.g., "16", "100")
        
    Returns:
        Page number (1-based) or None if not found
    """
    cache_key = f"{pdf_path}:{article_num}"
    if cache_key in _page_cache:
        return _page_cache[cache_key]
    
    try:
        path = Path(pdf_path)
        if not path.exists():
            print(f"[PDF_UTILS] File not found: {pdf_path}")
            return None
            
        reader = pypdf.PdfReader(path)
        
        # Regex patterns to match article headers
        # Matches: "Điều 16", "Điều 16.", "Điều  16" (flexible whitespace)
        # Case insensitive handled by search logic
        patterns = [
            f"Điều {article_num}[^0-9]",  # Điều 16 followed by non-digit (avoid matching 160)
            f"Điều {article_num}$",       # Điều 16 at end of line
            f"Điều {article_num}\."       # Điều 16.
        ]
        
        print(f"[PDF_UTILS] Scanning {path.name} for Article {article_num}...")
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
                
            # Normalize text for easier matching
            # Replace multiple spaces/newlines with single space
            normalized_text = re.sub(r'\s+', ' ', text)
            
            # Check for matches
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    page_num = i + 1  # 1-based
                    print(f"[PDF_UTILS] Found Article {article_num} on page {page_num}")
                    _page_cache[cache_key] = page_num
                    return page_num
                    
        print(f"[PDF_UTILS] Article {article_num} not found in {path.name}")
        return None
        
    except Exception as e:
        print(f"[PDF_UTILS] Error scanning PDF: {e}")
        return None
