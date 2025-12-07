import sys
import os

# Add parent directory to path to allow importing from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models_db import User
from core.auth import get_password_hash

def create_admin_user(username, password, email):
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"User {username} already exists. Skipping.")
            return

        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            full_name="Admin User"
        )
        db.add(admin_user)
        db.commit()
        print(f"Successfully created admin user: {username}")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user("admin", "admin123", "admin@law.com")
