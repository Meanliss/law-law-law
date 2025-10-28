"""
Prepare Domain - Complete workflow: PDF → JSON → Domain
Usage: python scripts/prepare_domain.py <domain_id> <pdf_file>
"""
import sys
import os

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pdf_converter import PDFConverter


def prepare_domain(domain_id: str, pdf_path: str):
    """Complete workflow to add a new law"""
    
    print(f"\n{'='*70}")
    print(f"PREPARE DOMAIN: {domain_id}")  # Bỏ emoji
    print(f"{'='*70}\n")
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"ERROR: PDF file not found: {pdf_path}")  # Bỏ emoji
        sys.exit(1)
    
    # Step 1: Create domain structure
    domain_dir = Path(f"data/domains/{domain_id}")
    raw_dir = domain_dir / "raw"
    pdfs_dir = domain_dir / "pdfs"
    
    print(f"Creating domain structure...")  # Bỏ emoji
    raw_dir.mkdir(parents=True, exist_ok=True)
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    print(f"   [OK] {raw_dir}/")  # ✓ → OK
    print(f"   [OK] {pdfs_dir}/")  # ✓ → OK
    
    # Step 2: Convert PDF → JSON
    print(f"\nConverting PDF to JSON...")  # Bỏ emoji
    converter = PDFConverter()
    
    json_filename = f"{pdf_file.stem}_hopnhat.json"
    json_output = raw_dir / json_filename
    
    result = converter.convert(str(pdf_file), str(json_output))
    
    if not result or not result.get('du_lieu'):
        print("ERROR: Conversion failed")  # Bỏ emoji
        sys.exit(1)
    
    # Step 3: Copy PDF
    import shutil
    pdf_dest = pdfs_dir / pdf_file.name
    shutil.copy(pdf_file, pdf_dest)
    print(f"\nCopied PDF: {pdf_dest}")  # Bỏ emoji
    
    # Step 4: Update registry
    registry_path = Path("data/domain_registry.json")
    
    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {}
    
    law_name = result.get('nguon', '')
    if 'LUẬT' in law_name.upper():
        import re
        match = re.search(r'LUẬT\s+([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ\s]+)', law_name, re.I)
        if match:
            law_name = match.group(0).strip()
    
    if domain_id not in registry:
        print(f"\nAdding to registry...")  # Bỏ emoji
        registry[domain_id] = {
            "name": law_name,
            "description": law_name,
            "keywords": _extract_keywords(law_name)
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        print(f"   [OK] Updated registry")  # ✓ → OK
    
    # Step 5: Build indices
    print(f"\nBuilding domain indices...")  # Bỏ emoji
    
    from build_domains_simple import build_domain
    build_domain(domain_id)
    
    print(f"\n{'='*70}")
    print(f"DOMAIN READY: {domain_id}")  # Bỏ emoji
    print(f"{'='*70}")
    print(f"\nLocation: {domain_dir}")
    print(f"\nNext: Restart app.py")


def _extract_keywords(law_name: str) -> list:
    """Extract keywords"""
    patterns = {
        'hôn nhân': ['hôn nhân', 'kết hôn', 'ly hôn'],
        'lao động': ['lao động', 'làm việc'],
        'đất đai': ['đất đai', 'quyền sử dụng đất'],
        'sở hữu trí tuệ': ['sở hữu trí tuệ', 'tác giả', 'bản quyền'],
    }
    
    name_lower = law_name.lower()
    for key, kws in patterns.items():
        if key in name_lower:
            return kws
    
    return [w for w in name_lower.split() if len(w) > 3][:5]


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/prepare_domain.py <domain_id> <pdf_file>")
        print("\nExample:")
        print("  python scripts/prepare_domain.py lshtt data/pdf/luat_so_huu_tri_tue.pdf")
        sys.exit(1)
    
    domain_id = sys.argv[1]
    pdf_path = sys.argv[2]
    
    prepare_domain(domain_id, pdf_path)


if __name__ == "__main__":
    main()