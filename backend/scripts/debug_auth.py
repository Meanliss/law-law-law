
import requests
import sys
from database import SessionLocal
from models_db import User
from core.auth import verify_password
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:7860"

def test_backend():
    print("DOT_Checking Backend Health...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"Health: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Health Check FAILED: {e}")
        return

    print("\nDOT_Checking Register Route (/register)...")
    try:
        # Try a dummy register to see if route exists (expect 400 or 422, NOT 404)
        r = requests.post(f"{BASE_URL}/register", json={}) 
        if r.status_code == 404:
            print("❌ Register Route NOT FOUND (404). The server running on 7860 does not have /register.")
        else:
            print(f"✅ Register Route Exists. Response: {r.status_code} (Expected 422 for empty body)")
            
    except Exception as e:
        print(f"Register Check FAILED: {e}")

    print("\nDOT_Checking Login Route (/token)...")
    try:
        # Try login with admin
        payload = {"username": "admin", "password": "admin123"}
        r = requests.post(f"{BASE_URL}/token", data=payload)
        
        if r.status_code == 200:
            print("✅ Login SUCCESS for admin/admin123")
        elif r.status_code == 404:
            print("❌ Login Route NOT FOUND (404).")
        else:
            print(f"❌ Login Failed: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"Login Check FAILED: {e}")

    print("\nDOT_Verifying DB Password...")
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    if user:
        is_valid = verify_password("admin123", user.hashed_password)
        print(f"DB User 'admin' exists. Password 'admin123' match? {is_valid}")
    else:
        print("DB User 'admin' does not exist.")
    db.close()

if __name__ == "__main__":
    test_backend()
