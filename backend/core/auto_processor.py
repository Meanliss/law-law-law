"""
Auto Processor - Automatically detect and convert new PDFs
Uses file count and modification date tracking
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class AutoProcessor:
    """Automatically process new PDF files"""
    
    def __init__(
        self, 
        pdf_dir: str = "data/pdf",
        json_dir: str = "data/json_auto",
        registry_file: str = "data/.conversion_registry.json"
    ):
        """
        Initialize auto-processor
        
        Args:
            pdf_dir: Directory containing source PDFs
            json_dir: Directory to save converted JSONs
            registry_file: File tracking conversion history
        """
        self.pdf_dir = Path(pdf_dir)
        self.json_dir = Path(json_dir)
        self.registry_file = Path(registry_file)
        
        # Create directories
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        
        # Load registry
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load conversion registry"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_registry(self):
        """Save conversion registry"""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _normalize_filename(self, pdf_name: str) -> str:
        """
        Convert PDF name to JSON name
        
        Examples:
            "luat_hon_nhan.pdf" → "luat_hon_nhan_hopnhat.json"
            "Luật Hôn nhân 2014.pdf" → "luat_hon_nhan_2014_hopnhat.json"
        """
        import re
        
        # Remove extension
        name = Path(pdf_name).stem.lower()
        
        # Vietnamese to ASCII
        vn_map = {
            'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd'
        }
        
        for vn, ascii in vn_map.items():
            name = name.replace(vn, ascii)
        
        # Clean up
        name = re.sub(r'[^\w\d]+', '_', name)
        name = re.sub(r'_+', '_', name).strip('_')
        
        # Add suffix
        if 'luat' in name and 'hopnhat' not in name:
            name += '__hopnhat'
        
        return name + '.json'
    
    def detect_new_files(self) -> List[Tuple[Path, Path]]:
        """
        Detect PDFs that need conversion
        
        Returns:
            List of (pdf_path, json_path) tuples
        """
        to_convert = []
        
        # Get all PDFs
        pdf_files = sorted(self.pdf_dir.glob('*.pdf'))
        
        print(f"\n[SCAN] Found {len(pdf_files)} PDF files")
        print(f"[SCAN] Registry has {len(self.registry)} entries")
        
        for pdf_file in pdf_files:
            pdf_name = pdf_file.name
            json_name = self._normalize_filename(pdf_name)
            json_path = self.json_dir / json_name
            
            # Check 1: Is it in registry?
            if pdf_name not in self.registry:
                print(f"[NEW] {pdf_name} → {json_name}")
                to_convert.append((pdf_file, json_path))
                continue
            
            # Check 2: Was PDF modified?
            entry = self.registry[pdf_name]
            current_hash = self._get_file_hash(pdf_file)
            
            if current_hash != entry.get('hash'):
                print(f"[MODIFIED] {pdf_name} → {json_name}")
                to_convert.append((pdf_file, json_path))
                continue
            
            # Check 3: Was JSON deleted?
            if not json_path.exists():
                print(f"[MISSING] {pdf_name} → {json_name} (JSON deleted)")
                to_convert.append((pdf_file, json_path))
                continue
            
            # Already processed and up-to-date
            print(f"[SKIP] {pdf_name}")
        
        return to_convert
    
    def convert_file(self, pdf_path: Path, json_path: Path) -> bool:
        """
        Convert a single PDF to JSON
        
        Args:
            pdf_path: Source PDF path
            json_path: Target JSON path
            
        Returns:
            True if successful
        """
        try:
            from core.pdf_converter import PDFConverter
            
            # Convert
            converter = PDFConverter()
            result = converter.convert(str(pdf_path))
            
            # Save JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # Update registry
            self.registry[pdf_path.name] = {
                'hash': self._get_file_hash(pdf_path),
                'json_file': json_path.name,
                'converted_at': datetime.now().isoformat(),
                'pdf_size': pdf_path.stat().st_size,
                'json_size': json_path.stat().st_size,
                'articles': len(result.get('du_lieu', []))
            }
            self._save_registry()
            
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to convert {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_all(self) -> Dict:
        """
        Process all new/modified PDFs
        
        Returns:
            Summary dict
        """
        to_convert = self.detect_new_files()
        
        if not to_convert:
            print("[PROCESS] ✅ All files up-to-date\n")
            return {'total': 0, 'converted': 0, 'failed': 0}
        
        print(f"\n{'='*70}")
        print(f"[PROCESS] Converting {len(to_convert)} files")
        print(f"{'='*70}")
        
        converted = 0
        failed = 0
        
        for pdf_path, json_path in to_convert:
            if self.convert_file(pdf_path, json_path):
                converted += 1
            else:
                failed += 1
        
        print(f"{'='*70}")
        print(f"[PROCESS] ✅ Done: {converted} converted, {failed} failed")
        print(f"[PROCESS] Registry: {self.registry_file}\n")
        
        return {
            'total': len(to_convert),
            'converted': converted,
            'failed': failed
        }


# Helper function for app.py
def get_pdf_for_json(json_filename: str) -> str:
    """
    Get PDF filename from JSON filename
    
    Args:
        json_filename: JSON file name
        
    Returns:
        Corresponding PDF filename
    """
    # Standard mappings
    mapping = {
        'luat_hon_nhan_hopnhat.json': 'luat_hon_nhan.pdf',
        'luat_dat_dai_hopnhat.json': 'luat_dat_dai.pdf',
        'luat_lao_donghopnhat.json': 'luat_lao_dong.pdf',
        'chuyen_giao_cong_nghe_hopnhat.json': 'luat_chuyen_giao_cong_nghe.pdf',
        'luat_dauthau_hopnhat.json':' luat_dau_thau.pdf',
        'nghi_dinh_214_2025.json': 'nghi_dinh_214_2025.pdf',
        'luat_so_huu_tri_tue_hopnhat.json': 'luat_so_huu_tri_tue.pdf',

        # Add your existing files here
    }
    
    if json_filename in mapping:
        return mapping[json_filename]
    
    # Fallback: simple replacement
    return json_filename.replace('_hopnhat.json', '.pdf').replace('.json', '.pdf')