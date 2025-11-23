
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_domains_simple import build_domain

if __name__ == "__main__":
    if len(sys.argv) > 1:
        domain_id = sys.argv[1]
        build_domain(domain_id)
    else:
        print("Usage: python build_one.py <domain_id>")
