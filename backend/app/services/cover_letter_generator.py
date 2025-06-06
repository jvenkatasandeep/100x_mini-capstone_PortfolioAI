"""
Cover Letter Generation Service for PortfolioAI
"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

from fastapi import UploadFile, HTTPException
from pydantic import BaseModel

from .groq_client import GroqClient
from ..utils.file_utils import get_temp_file, save_upload_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoverLetterRequest(BaseModel):
    """Request model for cover letter generation."""
    resume_id: str
    job_title: str
    company_name: str
    tone: str = "Professional"
    length: str = "Medium"

class CoverLetterGenerator:
    """Service for generating cover letters using AI."""
    
    def __init__(self, groq_client: Optional[GroqClient] = None):
        """Initialize the cover letter generator with an optional Groq client."""
        self.groq_client = groq_client or GroqClient()
        self.upload_dir = Path("uploads/cover_letters")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_resume(self, file: UploadFile) -> Dict[str, str]:
        """
        Upload a resume file and return its ID.
        
        Args:
            file: Uploaded resume file
            
        Returns:
            Dict containing the resume_id
            
        Raises:
            HTTPException: If file upload fails
        """
        try:
            # Generate a unique ID for the resume
            resume_id = f"resume_{uuid.uuid4().hex}"
            
            # Ensure the upload directory exists
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a safe filename
            import re
            from urllib.parse import quote
            safe_filename = re.sub(r'[^\w\d.-]', '_', file.filename)
            file_path = self.upload_dir / f"{resume_id}_{safe_filename}"
            
            # Save the file
            logger.info(f"Saving uploaded file to: {file_path}")
            await save_upload_file(file, file_path)
            
            # Verify the file was saved
            if not file_path.exists() or file_path.stat().st_size == 0:
                raise Exception("Failed to save file or file is empty")
            
            logger.info(f"Successfully uploaded resume: {file.filename} as {resume_id} (saved as {file_path})")
            return {"resume_id": resume_id}
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Error uploading resume: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def generate_cover_letter(self, request: CoverLetterRequest) -> Dict[str, str]:
        """
        Generate a cover letter based on the provided information.
        
        Args:
            request: CoverLetterRequest containing resume_id, job details, and preferences
            
        Returns:
            Dict containing the generated cover letter text
            
        Raises:
            HTTPException: If cover letter generation fails
        """
        try:
            # In a real implementation, you would:
            # 1. Fetch the resume content using resume_id
            # 2. Generate the cover letter using AI
            # 3. Return the generated text
            
            # For now, we'll use a placeholder implementation
            cover_letter = await self._generate_with_groq(request)
            
            return {"cover_letter_text": cover_letter}
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate cover letter: {str(e)}"
            )
    
    async def _generate_with_groq(self, request: CoverLetterRequest) -> str:
        """
        Generate a cover letter using the Groq API.
        
        Args:
            request: CoverLetterRequest with generation parameters
            
        Returns:
            Generated cover letter text
            
        Raises:
            Exception: If cover letter generation fails
        """
        try:
            # Construct the prompt for the AI
            prompt = f"""
            Please generate a {request.tone.lower()} cover letter for the position of {request.job_title} at {request.company_name}.
            The cover letter should be {request.length.lower()} in length.
            
            Include the following sections:
            1. Professional greeting
            2. Introduction expressing interest in the position
            3. 2-3 paragraphs highlighting relevant skills and experiences
            4. Closing paragraph expressing enthusiasm and next steps
            5. Professional sign-off
            
            Make the letter sound natural and tailored to the role.
            """
            
            # Call the Groq API
            response = await self.groq_client.generate_text(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )
            
            if not response or not response.strip():
                raise ValueError("Empty response from Groq API")
                
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error with Groq API: {str(e)}", exc_info=True)
            # Fall back to a simple template if AI generation fails
            return self._generate_fallback_letter(request)
    
    async def _generate_with_groq(self, request: CoverLetterRequest) -> str:
        """
        Generate a cover letter using the Groq API with enhanced prompt engineering.
        
        Args:
            request: CoverLetterRequest with generation parameters
            
        Returns:
            Generated cover letter text
            
        Raises:
            Exception: If cover letter generation fails
        """
        try:
            # Get the resume content if resume_id is provided
            resume_content = ""
            if hasattr(request, 'resume_id') and request.resume_id:
                try:
                    resume_path = self.upload_dir / f"{request.resume_id}.txt"
                    if resume_path.exists():
                        with open(resume_path, 'r', encoding='utf-8') as f:
                            resume_content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read resume content: {str(e)}")
            
            # Enhanced prompt with more structure and guidance
            prompt = f"""
            Generate a professional cover letter with the following specifications:
            
            JOB DETAILS:
            - Position: {request.job_title}
            - Company: {request.company_name}
            - Tone: {request.tone.capitalize()}
            - Length: {request.length.capitalize()}
            
            {f'RESUME CONTENT:\n{resume_content[:2000]}' if resume_content else 'No resume content provided.'}
            
            INSTRUCTIONS:
            1. Start with a professional greeting (e.g., "Dear Hiring Manager" or specific name if available)
            2. First paragraph: Express interest and mention the specific position and company
            3. Middle paragraphs (2-3): Highlight relevant skills and experiences
               - Match qualifications to job requirements
               - Use specific examples and achievements
               - Show knowledge of the company
            4. Closing paragraph: Express enthusiasm and include a call to action
            5. Professional sign-off (e.g., "Sincerely," followed by full name)
            
            FORMATTING:
            - Use professional business letter format
            - Keep paragraphs concise (3-4 sentences each)
            - Use bullet points for key achievements if appropriate
            - Maintain consistent spacing and formatting
            - Ensure proper grammar and spelling
            
            TONE GUIDELINES:
            - {self._get_tone_guidelines(request.tone)}
            - Avoid clichés and generic statements
            - Be confident but not arrogant
            - Show enthusiasm for the specific role
            
            Please generate the cover letter now:
            """
            
            # Adjust generation parameters based on desired length
            length_params = self._get_length_parameters(request.length)
            
            # Call the Groq API with enhanced parameters
            response = await self.groq_client.generate_text(
                prompt=prompt,
                max_tokens=length_params['max_tokens'],
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5,
                stop=["\n\n"]  # Stop at double newlines to prevent run-on
            )
            
            if not response or not response.strip():
                raise ValueError("Empty response from Groq API")
                
            # Post-process the response
            return self._post_process_cover_letter(response.strip(), request.tone)
            
        except Exception as e:
            logger.error(f"Error with Groq API: {str(e)}", exc_info=True)
            # Fall back to a more detailed template if AI generation fails
            return self._generate_fallback_letter(request)
    
    def _get_tone_guidelines(self, tone: str) -> str:
        """Get specific tone guidelines for the AI."""
        tone_guidelines = {
            "professional": "Formal language, business-appropriate, polished and refined",
            "friendly": "Approachable and warm, while maintaining professionalism",
            "concise": "Direct and to the point, minimal fluff, clear and impactful",
            "enthusiastic": "Energetic and passionate, showing excitement about the role",
            "formal": "Highly structured, traditional business language, proper titles"
        }
        return tone_guidelines.get(tone.lower(), "Professional and polished")

    async def save_cover_letter(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Save a generated cover letter.
        
        Args:
            data: Dictionary containing cover letter data to save
            
        Returns:
            Success message
        """
        try:
            # In a real implementation, you would save this to a database
            # For now, we'll just log it
            logger.info(f"Saving cover letter for resume {data.get('resume_id')}")
            
            return {"message": "Cover letter saved successfully"}
            
        except Exception as e:
            logger.error(f"Error saving cover letter: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save cover letter: {str(e)}"
            )

# Singleton instance
cover_letter_generator = CoverLetterGenerator()
