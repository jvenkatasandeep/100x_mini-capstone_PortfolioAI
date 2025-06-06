"""
File handling utilities for PortfolioAI.
"""
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, BinaryIO, Union, Dict, Any
import logging
import mimetypes

# Try to import python-magic, fallback to mimetypes
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    import subprocess
    import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported file types and their extensions
SUPPORTED_FILE_TYPES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/html": "html"
}

def get_temp_dir() -> Path:
    """Get or create the temporary directory."""
    temp_dir = Path(tempfile.gettempdir()) / "portfolioai"
    temp_dir.mkdir(exist_ok=True, parents=True)
    return temp_dir

def get_temp_file(ext: str = "") -> str:
    """
    Create a temporary file and return its path.
    
    Args:
        ext: File extension (e.g., '.pdf', '.docx')
        
    Returns:
        str: Path to the temporary file
    """
    temp_dir = get_temp_dir()
    return str(temp_dir / f"{uuid.uuid4()}{ext}")

def cleanup_file(file_path: Union[str, Path]) -> None:
    """
    Remove a file if it exists.
    
    Args:
        file_path: Path to the file to remove
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.warning(f"Failed to clean up {file_path}: {e}")

def cleanup_old_files(max_age_hours: int = 24) -> None:
    """
    Clean up files older than the specified hours.
    
    Args:
        max_age_hours: Maximum age of files to keep (in hours)
    """
    import time
    from datetime import datetime, timedelta
    
    try:
        temp_dir = get_temp_dir()
        now = datetime.now()
        max_age = timedelta(hours=max_age_hours)
        
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if now - file_time > max_age:
                    cleanup_file(file_path)
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")

def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    Get the file extension from a file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: File extension in lowercase (without the dot)
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    return path.suffix.lower()[1:] if path.suffix else ""

def get_mime_type(file_path: Union[str, Path]) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MIME type of the file
    """
    if HAS_MAGIC:
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    else:
        # Fallback using mimetypes and file command
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type
            
        # Try using the file command
        try:
            if shutil.which('file'):
                result = subprocess.run(
                    ['file', '--mime-type', '-b', str(file_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Could not determine MIME type using file command: {e}")
        
        # Default to application/octet-stream if we can't determine the type
        return 'application/octet-stream'

def is_file_supported(file_path: Union[str, Path]) -> bool:
    """
    Check if a file is of a supported type.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file type is supported, False otherwise
    """
    try:
        mime_type = get_mime_type(file_path)
        return mime_type in SUPPORTED_FILE_TYPES
    except Exception as e:
        logger.error(f"Error checking file type: {e}")
        return False

async def save_upload_file(upload_file, destination: Union[str, Path]) -> None:
    """
    Save an uploaded file to the specified destination.
    
    Args:
        upload_file: FastAPI UploadFile object
        destination: Path where to save the file
    """
    try:
        with open(destination, "wb") as buffer:
            while True:
                chunk = await upload_file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise
