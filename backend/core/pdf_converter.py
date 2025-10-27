"""
PDF to JSON Converter
Converts legal PDF documents to structured JSON format
"""

import re
import pdfplumber
from typing import Dict
from pathlib import Path


class PDFConverter:
    """Convert PDF legal documents to structured JSON"""
    
    def __init__(self):
        """Initialize converter"""
        pass
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
        
        return "\n".join(parts)
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove page numbers
        text = re.sub(r'(?m)^\s*(\d+|Trang\s*\d+)\s*$', '', text, flags=re.I)
        
        # Add newlines before chapters and articles
        text = re.sub(r'\s*(Chương\s+[IVXLCDM]+\b)', r'\n\1', text, flags=re.I)
        text = re.sub(r'\s*(Điều\s+\d+\.)', r'\n\1', text, flags=re.I)
        
        # Clean whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)
        
        return text.strip()
    
    def extract_source(self, text: str):
        """Extract metadata before Chương I"""
        match = re.search(r'(?m)^Chương\s+I\b', text)
        
        if match:
            nguon = text[:match.start()].strip()
            main = text[match.start():].strip()
        else:
            nguon = ""
            main = text
        
        nguon = re.sub(r'\s+', ' ', nguon).strip()
        return nguon, main
    
    def parse_structure(self, text: str, nguon: str) -> Dict:
        """Parse text into structured JSON"""
        data = []
        
        # Find chapters
        chapters = list(re.finditer(r'(?m)^Chương\s+[IVXLCDM]+[^\n]*', text, flags=re.I))
        
        for i, ch in enumerate(chapters):
            start = ch.start()
            end = chapters[i + 1].start() if i + 1 < len(chapters) else len(text)
            ch_block = text[start:end].strip()
            lines = ch_block.splitlines()
            
            # Extract chapter title
            chuong = ""
            for line in lines:
                if line.strip().startswith("Điều"):
                    break
                chuong += " " + line.strip()
            chuong = " ".join(chuong.split())
            
            # Find articles
            articles = list(re.finditer(r'(?m)^(Điều\s+\d+\..*)', ch_block))
            
            for j, art in enumerate(articles):
                a_start = art.start()
                a_end = articles[j + 1].start() if j + 1 < len(articles) else len(ch_block)
                a_block = ch_block[a_start:a_end].strip()
                
                a_lines = a_block.splitlines()
                header = a_lines[0].strip()
                
                m = re.match(r'(Điều\s+(\d+)\.)(.*)', header)
                if not m:
                    continue
                
                dieu_num = m.group(2)
                title = (m.group(1) + m.group(3).strip()).strip()
                body = "\n".join(a_lines[1:]).strip()
                
                # Parse clauses
                khoans = []
                k_matches = list(re.finditer(r'(?m)^(\d+)\.\s+(.*)', body))
                
                if k_matches:
                    for k, km in enumerate(k_matches):
                        k_start = km.start()
                        k_end = k_matches[k + 1].start() if k + 1 < len(k_matches) else len(body)
                        k_text = body[k_start:k_end].strip()
                        k_text = re.sub(r'\s+', ' ', k_text).strip()
                        
                        khoans.append({
                            "khoan_so": km.group(1),
                            "noi_dung": k_text
                        })
                    mo_ta = ""
                else:
                    mo_ta = re.sub(r'\s+', ' ', body).strip()
                
                data.append({
                    "chuong": chuong,
                    "dieu_so": dieu_num,
                    "tieu_de": title,
                    "mo_ta": mo_ta,
                    "khoan": khoans
                })
        
        return {"nguon": nguon, "du_lieu": data}
    
    def convert(self, pdf_path: str) -> Dict:
        """
        Main conversion function
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Structured JSON dict
        """
        print(f"[CONVERT] Processing: {Path(pdf_path).name}")
        
        # Extract and process
        raw_text = self.extract_text(pdf_path)
        cleaned = self.preprocess_text(raw_text)
        nguon, main = self.extract_source(cleaned)
        result = self.parse_structure(main, nguon)
        
        # Add metadata
        result["file_name"] = Path(pdf_path).name
        
        articles = len(result.get('du_lieu', []))
        print(f"[CONVERT] ✅ Extracted {articles} articles")
        
        return result