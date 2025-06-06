"""Database configuration for PortfolioAI."""
import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Supabase database URL from environment
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
if not SUPABASE_DB_URL:
    raise ValueError("SUPABASE_DB_URL environment variable is not set")

# Parse the URL to ensure it's valid
try:
    db_url_parts = urlparse(SUPABASE_DB_URL)
    if not all([db_url_parts.scheme, db_url_parts.hostname, db_url_parts.path]):
        raise ValueError("Invalid SUPABASE_DB_URL format")
except Exception as e:
    logger.error(f"Error parsing database URL: {e}")
    raise

# Database engine configuration
engine = create_engine(
    SUPABASE_DB_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=5,         # Number of connections to keep open
    max_overflow=10,     # Max number of connections beyond pool_size
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables in Supabase."""
    from .models import models  # noqa: F401
    
    try:
        # Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully in Supabase")
        
        # Verify connection by running a simple query
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            logger.info("Successfully connected to Supabase PostgreSQL")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def init_db():
    """Initialize database tables."""
    try:
        # Import models to register them with SQLAlchemy
        from .models import models  # noqa: F401
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create initial data
        db = SessionLocal()
        try:
            # Add any initial data here if needed
            db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        # In production, you might want to use Supabase migrations instead
        pass
