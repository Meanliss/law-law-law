import requests
import sys

# Encoding fix for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def print_step(step, msg):
    print(f"\n[STEP {step}] {msg}")

def simulate_flow():
    print("🚀 STARTING WEB SIMULATION...")
    
    # 1. Register
    print_step(1, "User clicks 'Dang ky ngay'...")
    username = "sim_user_03"  # Unique user
    email = "sim03@example.com"
    password = "password123"
    
    try:
        register_payload = {
            "username": username,
            "email": email,
            "password": password
        }
        print(f"   Submitting form: {register_payload}")
        
        # NOTE: Frontend sends JSON to /register
        resp = requests.post(f"{BASE_URL}/register", json=register_payload)
        
        if resp.status_code == 200:
            print(f"   ✅ SUCCESS: Account created! ID: {resp.json().get('id')}")
        elif resp.status_code == 400 and "already registered" in resp.text:
            print("   ⚠️  User already exists (Expected if running multiple times)")
        else:
            print(f"   ❌ FAILED: {resp.status_code} - {resp.text}")
            return

        # 2. Login
        print_step(2, "User clicks 'Dang nhap'...")
        
        # NOTE: Frontend sends Form Data to /token
        login_data = {
            "username": username,
            "password": password
        }
        print(f"   Submitting login credentials: {login_data}")
        resp = requests.post(f"{BASE_URL}/token", data=login_data)
        
        if resp.status_code != 200:
            print(f"   ❌ LOGIN FAILED: {resp.status_code} - {resp.text}")
            return
            
        token_data = resp.json()
        access_token = token_data["access_token"]
        print(f"   ✅ LOGIN SUCCESS! Token received: {access_token[:20]}...")

        # 3. Verify Session (Get User Profile)
        print_step(3, "Frontend fetches user profile (/users/me)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
        
        if resp.status_code == 200:
            user_info = resp.json()
            print(f"   ✅ PROFILE LOADED: Hello, {user_info['username']}!")
            print("\n🎉 SIMULATION COMPLETED SUCCESSFULLY! The backend is working perfectly.")
        else:
            print(f"   ❌ PROFILE FETCH FAILED: {resp.status_code} - {resp.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ CRITICAL ERROR: Could not connect to localhost:8000")
        print("   -> Is the backend server running?")
        print("   -> Run 'python app.py' in the backend/ directory.")

if __name__ == "__main__":
    simulate_flow()
