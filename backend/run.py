#!/usr/bin/env python3
"""
Run the FastAPI application with Uvicorn.
"""
import uvicorn
from app.database.local_config import init_db

if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=["*.db"],
    )
