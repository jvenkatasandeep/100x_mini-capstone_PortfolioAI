"""Initialize the database with test data."""
import os
from sqlalchemy.orm import Session
from . import models, crud
from .config import SessionLocal, init_db

def create_test_user():
    """Create a test user if it doesn't exist."""
    db = SessionLocal()
    try:
        test_email = "test@example.com"
        if not crud.user.get_by_email(db, email=test_email):
            user_in = {
                "email": test_email,
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
                "full_name": "Test User",
                "is_active": True,
            }
            crud.user.create(db, obj_in=user_in)
            db.commit()
            print("✓ Created test user")
    finally:
        db.close()

def init_db_with_test_data():
    """Initialize database with test data."""
    print("Initializing database...")
    init_db()
    create_test_user()
    print("✓ Database initialized successfully")

if __name__ == "__main__":
    init_db_with_test_data()
