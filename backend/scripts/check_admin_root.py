
from database import SessionLocal
from models_db import User

def check_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print(f"User 'admin' FOUND. ID: {user.id}, Active: {user.is_active}, Password Hash: {user.hashed_password[:10]}...")
        else:
            print("User 'admin' NOT FOUND.")
            
        # List all users
        users = db.query(User).all()
        print(f"Total users in DB: {len(users)}")
        for u in users:
            print(f" - {u.username} (ID: {u.id})")
            
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
