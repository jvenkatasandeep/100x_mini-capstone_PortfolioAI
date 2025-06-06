"""Dependencies for database operations."""
from typing import Generator
from sqlalchemy.orm import Session
from ..db.config import get_db, get_supabase
from ..services.supabase_service import SupabaseService

def get_db_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = get_db()
    try:
        yield db
    finally:
        db.close()

def get_supabase_service() -> SupabaseService:
    """Dependency that provides a Supabase service instance."""
    return SupabaseService()
