"""
PDF Converter - Convert legal PDF to structured JSON
Complements existing document_processor.py
"""

import re
import pdfplumber
from pathlib import Path
from typing import Dict, List, Tuple


class PDFConverter:
    """Convert PDF legal documents to JSON format compatible with build_domains_simple.py"""
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
        return "\n".join(parts)
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'(?m)^\s*(\d+|Trang\s*\d+)\s*$', '', text, flags=re.I)
        text = re.sub(r'([^\n])(Phần\s+thứ)', r'\1\n\2', text, flags=re.I)
        text = re.sub(r'([^\n])(Chương\s+[IVXLCDM]+)', r'\1\n\2', text, flags=re.I)
        text = re.sub(r'([^\n])(Điều\s+\d+[a-z]*\.)', r'\1\n\2', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)
        return text.strip()
    
    def extract_source(self, text: str) -> Tuple[str, str]:
        """Extract metadata"""
        patterns = [
            r'(?m)^Phần\s+thứ\s+(nhất|một|1)',
            r'(?m)^Chương\s+[I1]\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                nguon = text[:match.start()].strip()
                main = text[match.start():].strip()
                return re.sub(r'\s+', ' ', nguon), main
        return "", text
    
    def parse_structure(self, text: str, nguon: str) -> Dict:
        """Parse into JSON structure"""
        data = []
        sections = list(re.finditer(r'(?m)^(Phần\s+thứ\s+[^\n]+)', text, flags=re.I))
        
        if sections:
            section_blocks = [(s.group(1).strip(), 
                             text[s.start():sections[i+1].start() if i+1<len(sections) else len(text)].strip())
                            for i, s in enumerate(sections)]
        else:
            section_blocks = [("", text)]
        
        for section_title, section_content in section_blocks:
            chapters = list(re.finditer(r'(?m)^(Chương\s+[IVXLCDM\d]+[^\n]*)', section_content, flags=re.I))
            
            if chapters:
                for i, ch in enumerate(chapters):
                    ch_block = section_content[ch.start():chapters[i+1].start() if i+1<len(chapters) else len(section_content)].strip()
                    lines = ch_block.splitlines()
                    chuong_lines = [l.strip() for l in lines if not re.match(r'^Điều\s+\d+[a-z]*\.', l.strip())]
                    chuong_title = " ".join(" ".join(chuong_lines).split())
                    full_title = f"{section_title} {chuong_title}" if section_title else chuong_title
                    data.extend(self._parse_articles(ch_block, full_title))
            else:
                data.extend(self._parse_articles(section_content, section_title or "Nội dung chính"))
        
        return {"nguon": nguon, "du_lieu": data}
    
    def _parse_articles(self, text: str, chuong: str) -> List[Dict]:
        """Parse articles"""
        articles_data = []
        articles = list(re.finditer(r'(?m)^(Điều\s+(\d+[a-z]?)\..*)', text))
        
        for i, dieu in enumerate(articles):
            d_block = text[dieu.start():articles[i+1].start() if i+1<len(articles) else len(text)].strip()
            d_lines = d_block.splitlines()
            if not d_lines:
                continue
            
            m = re.match(r'(Điều\s+(\d+[a-z]?)\.)\s*(.*)', d_lines[0].strip())
            if not m:
                continue
            
            dieu_num = m.group(2)
            title = f"{m.group(1)}{m.group(3).strip()}"
            body = "\n".join(d_lines[1:]).strip()
            
            khoans = []
            k_matches = list(re.finditer(r'(?m)^(\d+)\.\s+(.*)', body))
            
            if k_matches:
                for k, km in enumerate(k_matches):
                    k_text = body[km.start():k_matches[k+1].start() if k+1<len(k_matches) else len(body)].strip()
                    khoans.append({"khoan_so": km.group(1), "noi_dung": re.sub(r'\s+', ' ', k_text)})
                mo_ta = ""
            else:
                mo_ta = re.sub(r'\s+', ' ', body).strip()
            
            articles_data.append({
                "chuong": chuong,
                "dieu_so": dieu_num,
                "tieu_de": title,
                "mo_ta": mo_ta,
                "khoan": khoans
            })
        
        return articles_data
    
    def convert(self, pdf_path: str, output_json: str = None) -> Dict:
        """
        Main conversion: PDF → JSON
        
        Args:
            pdf_path: Path to PDF file
            output_json: Optional output path, if None will auto-generate
            
        Returns:
            JSON data dict
        """
        print(f"[CONVERT] Processing: {Path(pdf_path).name}")
        
        raw_text = self.extract_text(pdf_path)
        cleaned = self.preprocess_text(raw_text)
        nguon, main = self.extract_source(cleaned)
        result = self.parse_structure(main, nguon)
        result["file_name"] = Path(pdf_path).name
        
        articles = len(result.get('du_lieu', []))
        print(f"[CONVERT] Extracted {articles} articles")
        
        if articles > 0:
            first, last = result['du_lieu'][0], result['du_lieu'][-1]
            print(f"[CONVERT] Range: Điều {first['dieu_so']} → Điều {last['dieu_so']}")
        
        # Auto-save if output path provided
        if output_json:
            import json
            Path(output_json).parent.mkdir(parents=True, exist_ok=True)
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"[CONVERT] Saved: {output_json}")
        
        return result