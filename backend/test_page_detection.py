import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_utils import find_article_page

def test_page_detection():
    pdf_path = "data/domains/lao_dong/pdfs/luat_lao_dong.pdf"
    
    print(f"Testing page detection on {pdf_path}")
    
    # Test Article 16 (Known to exist)
    article_num = "16"
    page = find_article_page(pdf_path, article_num)
    print(f"Article {article_num} found on page: {page}")
    
    if page is None:
        print("❌ Failed to find Article 16")
    else:
        print("✅ Successfully found Article 16")

    # Test Article 1000 (Likely not exist)
    article_num = "1000"
    page = find_article_page(pdf_path, article_num)
    print(f"Article {article_num} found on page: {page}")
    
    if page is None:
        print("✅ Correctly returned None for missing article")
    else:
        print(f"❌ Unexpectedly found Article {article_num} on page {page}")

if __name__ == "__main__":
    test_page_detection()
