"""
Test script cho API
Chạy: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    

def test_simple_question():
    print("\n" + "="*60)
    print("TEST 2: Simple Question")
    print("="*60)
    
    payload = {
        "question": "Quy định độ tuổi kết hôn ở Việt Nam?",
        "use_advanced": False
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    result = response.json()
    
    print(f"Question: {result.get('answer', 'N/A')[:200]}...")
    print(f"Sources: {len(result.get('sources', []))}")


def test_advanced_question():
    print("\n" + "="*60)
    print("TEST 3: Advanced Question")
    print("="*60)
    
    payload = {
        "question": "Quy định về ly hôn và chia tài sản?",
        "use_advanced": True
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    result = response.json()
    
    print(f"Answer: {result.get('answer', 'N/A')[:200]}...")
    print(f"Search mode: {result.get('search_mode')}")


def test_stats():
    print("\n" + "="*60)
    print("TEST 4: Statistics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/stats")
    stats = response.json()
    
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Laws: {list(stats['laws'].keys())}")


if __name__ == "__main__":
    try:
        test_health()
        test_simple_question()
        test_advanced_question()
        test_stats()
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("Make sure backend is running: cd backend && python app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
