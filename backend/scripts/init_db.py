import sys
import os

# Add parent directory to path to allow importing from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base
import models_db

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
