"""
Resume processing service with AI enhancements.
"""
import os
import PyPDF2
import docx
import json
import logging
import mimetypes
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime

# Try to use python-magic-bin if available, fallback to file extension
try:
    import magic
    USE_MAGIC = True
except ImportError:
    USE_MAGIC = False
    logging.warning("python-magic not available, falling back to file extension detection")

from ..services.groq_client import groq_client
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class ResumeProcessor:
    """Service for processing and analyzing resumes with AI."""
    
    def __init__(self):
        self.supported_formats = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
    
    async def process_resume(self, file_path: str) -> Dict[str, Any]:
        """
        Process a resume file and extract structured data.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dict containing processed resume data with the following structure:
            {
                "file_info": {
                    "size_bytes": int,
                    "created": str (ISO format datetime),
                    "modified": str (ISO format datetime)
                },
                "content": str (first 1000 chars of extracted text),
                "analysis": Dict (structured resume data)
            }
        """
        if not file_path or not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return {"error": error_msg}
            
        try:
            # Get file type
            file_type = self._get_file_type(file_path)
            
            # Check if file type is supported
            if not any(supported in file_type.lower() for supported in [
                'pdf', 'msword', 'wordprocessingml', 'text/plain'
            ]):
                error_msg = f"Unsupported file type: {file_type}"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            # Extract text from file
            text = self._extract_text(file_path, file_type)
            if not text or not text.strip():
                error_msg = f"No text could be extracted from the file: {file_path}"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            # Get file stats
            file_stats = self._get_file_stats(file_path)
            
            # Clean up the extracted text
            text = self._clean_extracted_text(text)
            
            # Analyze with AI (this will use basic extraction if AI fails)
            analysis = await self._analyze_with_ai(text)
            
            return {
                "file_info": file_stats,
                "content": text,
                "analysis": analysis
            }
            
        except Exception as e:
            error_msg = f"Error processing resume {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and format the extracted text from the resume.
        
        Args:
            text: Raw extracted text from the resume
            
        Returns:
            str: Cleaned and formatted text
        """
        if not text:
            return ""
            
        # Remove multiple whitespace characters and normalize newlines
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common PDF artifacts and special characters
        text = re.sub(r'\x0c', '', text)  # Remove form feed characters
        text = re.sub(r'\u2022', '•', text)  # Convert bullet points
        
        # Normalize section headers (assuming they're in ALL CAPS)
        text = re.sub(r'\n\s*([A-Z][A-Z\s]{5,})\n', 
                     lambda m: f"\n\n{m.group(1).title()}\n{'='*len(m.group(1).title())}\n", 
                     text)
        
        # Clean up any remaining multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
        
    def _get_file_type(self, file_path: str) -> str:
        """Get the MIME type of a file."""
        # First try to determine by file extension
        ext = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            return mime_type
            
        # Map common extensions to MIME types
        extension_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf',
            '.odt': 'application/vnd.oasis.opendocument.text'
        }
        
        return extension_map.get(ext, 'application/octet-stream')
    
    def _extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from different file types."""
        try:
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            if 'pdf' in file_type.lower():
                return self._extract_text_from_pdf(file_path)
            elif any(doc_type in file_type.lower() for doc_type in ['msword', 'wordprocessingml']):
                return self._extract_text_from_docx(file_path)
            elif 'text/plain' in file_type.lower():
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            else:
                # Try to read as text as a fallback
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        return f.read()
                except:
                    raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path} (type: {file_type}): {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                    except Exception as page_error:
                        logger.warning(f"Error extracting text from page in {file_path}: {str(page_error)}")
                        continue
                
                if not text:
                    raise ValueError("No text could be extracted from the PDF")
                    
                return '\n'.join(text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            raise
    
    async def _analyze_with_ai(self, text: str) -> Dict[str, Any]:
        """
        Analyze resume text with AI.
        
        Args:
            text: The resume text to analyze
            
        Returns:
            Dict containing structured resume data with fallback to basic extraction if AI fails
        """
        if not text or not text.strip():
            logger.warning("Empty or invalid text provided for AI analysis")
            return self._extract_basic_info("")
            
        try:
            prompt = f"""
            Analyze the following resume and extract the following information in JSON format:
            
            1. personal_info: Object with name, email, phone, location, linkedin, github, etc.
            2. summary: A brief professional summary
            3. work_experience: Array of jobs with title, company, dates, description, and achievements
            4. education: Array of education entries with degree, institution, dates, and details
            5. skills: Object with categories like 'languages', 'technologies', 'tools', etc.
            6. certifications: Array of certifications
            {text}
            """
            
            # Call the centralized Groq client
            response = await groq_client._make_request(
                messages=[
                    {"role": "system", "content": "You are a professional resume parser. Extract structured information from the provided resume text."},
                    {"role": "user", "content": prompt.format(text=text[:8000])}
                ],
                model="mixtral-8x7b-32768"
            )
            
            # Parse and validate the response
            try:
                if isinstance(response, str):
                    # Try to extract JSON if response is a string
                    import re
                    json_match = re.search(r'```(?:json)?\n(.*?)\n```', response, re.DOTALL)
                    if json_match:
                        response = json_match.group(1)
                    
                    result = json.loads(response)
                else:
                    result = response
                
                # Ensure we have a valid structure
                if not isinstance(result, dict):
                    raise ValueError("Expected a dictionary response")
                    
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse AI response: {str(e)}")
                return self._basic_text_extraction(text)
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}", exc_info=True)
            return self._basic_text_extraction(text)
    
    def _extract_basic_info(self, text: str) -> Dict[str, Any]:
        """
        Extract basic information from resume text using simple pattern matching.
        Used as a fallback when AI analysis fails.
        """
        return {
            "personal_info": self._extract_contact_info(text),
            "summary": self._extract_summary(text),
            "work_experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "skills": self._extract_skills(text),
            "projects": self._extract_projects(text)
        }
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text."""
        # This is a simplified implementation
        return {"email": "", "phone": "", "linkedin": ""}
    
    def _extract_summary(self, text: str) -> str:
        """Extract a summary from the resume text."""
        # Return first few sentences as a simple summary
        sentences = text.split('.')
        return '. '.join(sentences[:3]).strip() + '.' if sentences else ""
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from resume text."""
        # This is a placeholder - in a real app, you'd use more sophisticated parsing
        return [{"title": "Software Engineer", "company": "Example Inc.", "duration": "2020-Present"}]
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from resume text."""
        # This is a placeholder - in a real app, you'd use more sophisticated parsing
        return [{"degree": "B.S. Computer Science", "institution": "University of Example"}]
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills from resume text."""
        # This is a placeholder - in a real app, you'd use more sophisticated parsing
        common_skills = {
            "languages": ["Python", "JavaScript", "SQL"],
            "technologies": ["Docker", "AWS", "FastAPI"],
            "tools": ["Git", "VS Code"]
        }
        return {k: v for k, v in common_skills.items() if any(skill.lower() in text.lower() for skill in v)}
    
    def _extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract projects from resume text."""
        # This is a placeholder - in a real app, you'd use more sophisticated parsing
        return [{"name": "Portfolio Website", "description": "A personal portfolio website"}]
    
    def _get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics."""
        try:
            stats = os.stat(file_path)
            return {
                "size_bytes": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting file stats for {file_path}: {str(e)}")
            return {"error": str(e)}

# Create a global instance
resume_processor = ResumeProcessor()
