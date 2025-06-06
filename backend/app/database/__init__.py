"""Database package for PortfolioAI."""
# Use local configuration for development
from .local_config import get_db, init_db, Base
from . import models

# Initialize database tables
init_db()

__all__ = [
    "get_db",
    "init_db",
    "Base",
    "models"
]
