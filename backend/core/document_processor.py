"""
Document Processor - Load and process legal JSON documents
"""

import json
import os
from typing import List, Dict, Tuple


def xu_ly_van_ban_phap_luat_json(file_path: str) -> Tuple[List[Dict], str]:
    """
    Process legal document JSON file into chunks
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Tuple of (chunks list, law source name)
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f'[ERROR] Khong tim thay file: {file_path}')
        return [], ''
    except json.JSONDecodeError:
        print(f'[ERROR] File khong hop le: {file_path}')
        return [], ''

    nguon_luat = data.get('nguon', 'Khong ro nguon')
    
    # Extract filename for tracking
    json_filename = os.path.basename(file_path)

    for dieu in data.get('du_lieu', []):
        dieu_so = dieu.get('dieu_so')
        if not dieu_so or not str(dieu_so).strip().isdigit():
            continue

        base_source = f'{nguon_luat}, Dieu {dieu_so}'
        base_content = dieu.get('noi_dung_hien_hanh', f"{dieu.get('tieu_de', '')}. {dieu.get('mo_ta', '')}".strip())
        
        base_metadata = {
            'law_name': nguon_luat,
            'article_num': dieu_so,
            'level': 'article',
            'json_file': json_filename  # Add JSON filename for tracking
        }
        
        if 'nguon_sua_doi' in dieu:
            base_source += f' (sua doi boi {dieu["nguon_sua_doi"]})'
            base_metadata['modified_by'] = dieu['nguon_sua_doi']

        # Process article without clauses
        if not dieu.get('khoan'):
            chunks.append({
                'source': base_source,
                'content': base_content,
                'metadata': base_metadata
            })
            continue

        # Process clauses
        for khoan in dieu['khoan']:
            khoan_source = f'{base_source}, Khoan {khoan.get("khoan_so", "")}'
            khoan_content = khoan.get('noi_dung_hien_hanh', khoan.get('noi_dung', ''))
            
            khoan_metadata = base_metadata.copy()
            khoan_metadata.update({
                'clause_num': khoan.get('khoan_so', ''),
                'level': 'clause'
            })
            
            if 'nguon_sua_doi' in khoan:
                khoan_source += f' (sua doi boi {khoan["nguon_sua_doi"]})'
                khoan_metadata['modified_by'] = khoan['nguon_sua_doi']

            # Process clause without points
            if not khoan.get('diem'):
                chunks.append({
                    'source': khoan_source,
                    'content': khoan_content,
                    'metadata': khoan_metadata
                })
                continue
            
            # Process points
            for diem in khoan.get('diem', []):
                diem_source = f'{khoan_source}, Diem {diem.get("diem_so", "")}'
                diem_content = diem.get('noi_dung_hien_hanh', diem.get('noi_dung', ''))
                
                diem_metadata = khoan_metadata.copy()
                diem_metadata.update({
                    'point_num': diem.get('diem_so', ''),
                    'level': 'point'
                })
                
                if 'nguon_sua_doi' in diem:
                    diem_source += f' (sua doi boi {diem["nguon_sua_doi"]})'
                    diem_metadata['modified_by'] = diem['nguon_sua_doi']
                
                chunks.append({
                    'source': diem_source,
                    'content': diem_content,
                    'metadata': diem_metadata
                })
                        
    return chunks, nguon_luat
