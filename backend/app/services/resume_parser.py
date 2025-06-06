"""
Resume Parser for PortfolioAI
Handles text extraction from various file formats.
"""
import os
import logging
import sys
import mimetypes
from typing import Optional, Tuple
from pathlib import Path

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for required dependencies
try:
    from pypdf import PdfReader
    import docx
    import filetype  # Pure Python alternative to python-magic
    HAS_REQUIRED_DEPS = True
except ImportError as e:
    logger.error(f"Missing required dependencies: {e}")
    logger.error("Please install the required packages: pip install pypdf python-docx filetype")
    HAS_REQUIRED_DEPS = False
    
    # Print to stderr as well since logging might not be fully configured
    print("Error: Missing required dependencies. Please check the logs for details.", file=sys.stderr)

def get_file_type(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Determine the file type using filetype and fallback to mimetypes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (mime_type, extension) or (None, None) if unknown
    """
    try:
        # First try filetype which is more accurate
        kind = filetype.guess(file_path)
        if kind:
            return kind.mime, kind.extension
            
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            ext = mimetypes.guess_extension(mime_type)
            return mime_type, ext[1:] if ext else None
            
    except Exception as e:
        logger.warning(f"Error determining file type: {e}")
        
    return None, None

def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text or None if extraction fails
    """
    if not HAS_REQUIRED_DEPS:
        logger.error("Required dependencies (pypdf) not installed")
        return None
        
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def extract_text_from_docx(file_path: str) -> Optional[str]:
    """Extract text from a DOCX file.
    
    Args:
        file_path: Path to the DOCX file
        
    Returns:
        Extracted text or None if extraction fails
    """
    if not HAS_REQUIRED_DEPS:
        logger.error("Required dependencies (python-docx) not installed")
        return None
        
    try:
        doc = docx.Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return None

def extract_text_from_file(file_path: str) -> Optional[str]:
    """Extract text from a file based on its MIME type or extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text or None if extraction fails or format is not supported
    """
    if not HAS_REQUIRED_DEPS:
        logger.error("Required dependencies are not installed")
        return None
        
    try:
        # Get file type
        mime_type, extension = get_file_type(file_path)
        
        # If we couldn't determine the type, try by extension
        if not mime_type and not extension:
            extension = Path(file_path).suffix.lower().lstrip('.')
        
        # Process based on file type
        if mime_type == 'application/pdf' or extension == 'pdf':
            logger.info("Processing as PDF file")
            return extract_text_from_pdf(file_path)
        elif (mime_type and 'word' in mime_type.lower()) or extension in ['docx', 'doc']:
            logger.info("Processing as Word document")
            return extract_text_from_docx(file_path)
        elif mime_type == 'text/plain' or extension == 'txt':
            logger.info("Processing as plain text file")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Read {len(content)} characters from text file")
                return content
        else:
            logger.warning(f"Unsupported file type: {mime_type or 'unknown'}, extension: {extension or 'unknown'}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
        return None
