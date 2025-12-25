"""
PDF to JSON Converter (with Table Support)
Converts legal PDF documents to structured JSON format
Supports extraction of tables and converts them to Markdown format

Usage:
    python scripts/pdf_to_json.py <domain_id>
    
Example:
    python scripts/pdf_to_json.py thue_tncn
    
Prerequisites:
    - PDF file must exist in: data/domains/{domain_id}/pdfs/*.pdf
    - Output will be saved to: data/domains/{domain_id}/raw/*.json
"""

import sys
import os
import json
import re
from pathlib import Path

# Force UTF-8 on Windows (only if not already wrapped)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("[ERROR] pdfplumber not installed!")
    print("        Install: pip install pdfplumber")
    sys.exit(1)


class PDFToJSONConverter:
    """Convert legal PDF to structured JSON with table support"""
    
    def table_to_markdown(self, table: list) -> str:
        """Convert a table (list of rows) to Markdown format"""
        if not table or len(table) < 1:
            return ""
        
        # Clean cells - replace None with empty string
        cleaned_table = []
        for row in table:
            if row:
                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                # Skip empty rows
                if any(cleaned_row):
                    cleaned_table.append(cleaned_row)
        
        if len(cleaned_table) < 1:
            return ""
        
        # Find max columns
        max_cols = max(len(row) for row in cleaned_table)
        
        # Normalize all rows to same length
        normalized = []
        for row in cleaned_table:
            normalized.append(row + [""] * (max_cols - len(row)))
        
        # Build markdown table
        lines = []
        
        # Header row
        header = normalized[0]
        lines.append("| " + " | ".join(header) + " |")
        
        # Separator
        lines.append("|" + "|".join(["---"] * max_cols) + "|")
        
        # Data rows
        for row in normalized[1:]:
            lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(lines)
    
    def extract_text_with_tables(self, pdf_path: str) -> str:
        """Extract text from PDF, converting tables to Markdown"""
        parts = []
        table_count = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_parts = []
                
                # Extract tables from this page
                tables = page.extract_tables()
                
                if tables:
                    # Get text without table areas
                    table_bboxes = []
                    if hasattr(page, 'find_tables'):
                        found_tables = page.find_tables()
                        for t in found_tables:
                            table_bboxes.append(t.bbox)
                    
                    # Extract text outside tables
                    if table_bboxes:
                        # Create page without table regions
                        filtered_page = page
                        for bbox in table_bboxes:
                            # Crop out table area by getting text from non-table regions
                            pass
                    
                    # Get full text first
                    text = page.extract_text()
                    if text:
                        page_parts.append(text)
                    
                    # Append tables as markdown
                    for table in tables:
                        md_table = self.table_to_markdown(table)
                        if md_table:
                            table_count += 1
                            page_parts.append(f"\n[BẢNG {table_count}]\n{md_table}\n")
                else:
                    # No tables, just extract text
                    text = page.extract_text()
                    if text:
                        page_parts.append(text)
                
                if page_parts:
                    parts.append("\n".join(page_parts))
        
        if table_count > 0:
            print(f"  📊 Found {table_count} table(s), converted to Markdown")
        
        return "\n".join(parts)
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF (legacy, now uses table-aware version)"""
        return self.extract_text_with_tables(pdf_path)
    
    def normalize_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove page numbers
        text = re.sub(r'(?m)^\s*(\d+|Trang\s*\d+)\s*$', '', text, flags=re.I)
        
        # Add newlines before sections/chapters/articles
        text = re.sub(r'([^\n])(Phần\s+thứ)', r'\1\n\2', text, flags=re.I)
        text = re.sub(r'([^\n])(Chương\s+[IVXLCDM]+)', r'\1\n\2', text, flags=re.I)
        text = re.sub(r'([^\n])(Điều\s+\d+[a-z]*\.)', r'\1\n\2', text)
        
        # Normalize spaces
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)
        
        return text.strip()
    
    def extract_metadata(self, text: str) -> tuple:
        """Extract law source and main content"""
        patterns = [
            r'(?m)^Phần\s+thứ\s+(nhất|một|1)',
            r'(?m)^Chương\s+[I1]\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                source = text[:match.start()].strip()
                content = text[match.start():].strip()
                source = re.sub(r'\s+', ' ', source)
                return source, content
        
        return "", text
    
    def parse_structure(self, text: str, source: str) -> dict:
        """Parse text into structured JSON"""
        data = []
        
        # Find sections
        sections = list(re.finditer(r'(?m)^(Phần\s+thứ\s+[^\n]+)', text, flags=re.I))
        
        if sections:
            section_blocks = []
            for i, sec in enumerate(sections):
                sec_start = sec.start()
                sec_end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
                section_blocks.append((sec.group(1).strip(), text[sec_start:sec_end].strip()))
        else:
            section_blocks = [("", text)]
        
        for section_title, section_content in section_blocks:
            # Find chapters
            chapters = list(re.finditer(r'(?m)^(Chương\s+[IVXLCDM\d]+[^\n]*)', section_content, flags=re.I))
            
            if chapters:
                for i, ch in enumerate(chapters):
                    ch_start = ch.start()
                    ch_end = chapters[i + 1].start() if i + 1 < len(chapters) else len(section_content)
                    ch_block = section_content[ch_start:ch_end].strip()
                    
                    # Extract chapter title
                    lines = ch_block.splitlines()
                    ch_lines = []
                    for line in lines:
                        if re.match(r'^Điều\s+\d+[a-z]*\.', line.strip()):
                            break
                        ch_lines.append(line.strip())
                    
                    ch_title = " ".join(" ".join(ch_lines).split())
                    full_title = f"{section_title} {ch_title}" if section_title else ch_title
                    
                    data.extend(self._parse_articles(ch_block, full_title))
            else:
                data.extend(self._parse_articles(section_content, section_title or "Nội dung chính"))
        
        return {"nguon": source, "du_lieu": data}
    
    def _parse_articles(self, text: str, chapter: str) -> list:
        """Parse articles within a block"""
        articles = []
        article_matches = list(re.finditer(r'(?m)^(Điều\s+(\d+[a-z]?)\..*)', text))
        
        for i, match in enumerate(article_matches):
            start = match.start()
            end = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(text)
            block = text[start:end].strip()
            
            lines = block.splitlines()
            if not lines:
                continue
            
            header = lines[0].strip()
            m = re.match(r'(Điều\s+(\d+[a-z]?)\.)\s*(.*)', header)
            if not m:
                continue
            
            article_num = m.group(2)
            title_text = m.group(3).strip()
            title = f"{m.group(1)} {title_text}" if title_text else m.group(1)
            
            body = "\n".join(lines[1:]).strip()
            
            # Extract clauses
            clauses = []
            clause_matches = list(re.finditer(r'(?m)^(\d+)\.\s+(.*)', body))
            
            if clause_matches:
                for j, cm in enumerate(clause_matches):
                    c_start = cm.start()
                    c_end = clause_matches[j + 1].start() if j + 1 < len(clause_matches) else len(body)
                    c_text = body[c_start:c_end].strip()
                    c_text = re.sub(r'\s+', ' ', c_text).strip()
                    
                    clauses.append({
                        "khoan_so": cm.group(1),
                        "noi_dung": c_text
                    })
                description = ""
            else:
                description = re.sub(r'\s+', ' ', body).strip()
            
            articles.append({
                "chuong": chapter,
                "dieu_so": article_num,
                "tieu_de": title,
                "mo_ta": description,
                "khoan": clauses
            })
        
        return articles
    
    def convert(self, pdf_path: str, output_path: str):
        """Main conversion function"""
        print(f"\n[PDF→JSON] Processing: {Path(pdf_path).name}")
        
        # Extract and parse
        raw_text = self.extract_text(pdf_path)
        cleaned = self.normalize_text(raw_text)
        source, content = self.extract_metadata(cleaned)
        result = self.parse_structure(content, source)
        result["file_name"] = Path(pdf_path).name
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        articles = len(result.get('du_lieu', []))
        print(f"[PDF→JSON] ✓ Extracted {articles} articles")
        print(f"[PDF→JSON] ✓ Saved to: {output_path}")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                   PDF to JSON Converter                          ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    python scripts/pdf_to_json.py <domain_id>

Example:
    python scripts/pdf_to_json.py hinh_su

Prerequisites:
    - PDF file in: data/domains/{domain_id}/pdfs/*.pdf

Output:
    - JSON file in: data/domains/{domain_id}/raw/*.json
        """)
        sys.exit(1)
    
    domain_id = sys.argv[1]
    
    # Find PDF
    pdfs_dir = Path(f"data/domains/{domain_id}/pdfs")
    if not pdfs_dir.exists():
        print(f"[ERROR] Directory not found: {pdfs_dir}")
        sys.exit(1)
    
    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {pdfs_dir}")
        sys.exit(1)
    
    pdf_file = pdf_files[0]
    
    # Prepare output
    raw_dir = Path(f"data/domains/{domain_id}/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    json_file = raw_dir / f"{pdf_file.stem}.json"
    
    # Convert
    converter = PDFToJSONConverter()
    converter.convert(str(pdf_file), str(json_file))
    
    print(f"\n✅ SUCCESS!")
    print(f"   Domain: {domain_id}")
    print(f"   JSON: {json_file.name}")
    print(f"\nNext step:")
    print(f"   python scripts/build_domains_simple.py")


if __name__ == "__main__":
    main()