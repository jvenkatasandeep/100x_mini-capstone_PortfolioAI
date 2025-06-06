"""
Resume Optimization Service for PortfolioAI
"""
import logging
from typing import Dict, Any, Tuple, List

from .groq_client import GroqClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeOptimizer:
    """Service for optimizing resumes and providing ATS feedback."""
    
    def __init__(self, groq_client: GroqClient):
        """Initialize the resume optimizer with a Groq client."""
        if not groq_client or not groq_client.enabled:
            logger.warning("Groq client is not enabled. Resume optimization will be limited.")
        self.groq_client = groq_client
    
    async def optimize_resume(
        self, 
        resume_text: str,
        job_description: str = ""
    ) -> Dict[str, Any]:
        """
        Optimize a resume following best practices.
        
        Args:
            resume_text: The text content of the resume to optimize
            job_description: Optional job description to optimize the resume for
            
        Returns:
            Dict containing optimized text, score, and suggestions
        """
        logger.info("Starting resume optimization...")
        logger.debug(f"Resume length: {len(resume_text)} characters")
        logger.debug(f"Job description provided: {'Yes' if job_description else 'No'}")
        
        # Validate input
        if not resume_text or len(resume_text.strip()) < 50:
            error_msg = "Resume text is too short or empty"
            logger.error(error_msg)
            return {
                "optimized_text": resume_text,
                "score": 0.0,
                "suggestions": [error_msg],
                "status": "error",
                "error": error_msg
            }
            
        if not self.groq_client or not hasattr(self.groq_client, 'optimize_resume'):
            error_msg = "Resume optimization service is not properly configured"
            logger.error(error_msg)
            return {
                "optimized_text": resume_text,
                "score": 0.0,
                "suggestions": [error_msg],
                "status": "error",
                "error": error_msg
            }
            
        try:
            logger.info("Sending request to Groq API...")
            # Get optimization from Groq
            result = await self.groq_client.optimize_resume(resume_text, job_description)
            logger.info("Received response from Groq API")
            
            # Ensure we have all required fields
            if not all(key in result for key in ["optimized_text", "score", "suggestions"]):
                raise ValueError("Invalid response from optimization service")
                
            return {
                "optimized_text": result["optimized_text"],
                "score": min(max(float(result["score"]), 0), 100),  # Ensure score is between 0-100
                "suggestions": result["suggestions"][:5],  # Limit to 5 suggestions
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing resume: {str(e)}", exc_info=True)
            return {
                "optimized_text": resume_text,  # Return original on error
                "score": 0.0,
                "suggestions": ["Error during optimization. Please try again."],
                "status": "error",
                "error": str(e)
            }
    
    async def get_ats_score(
        self, 
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Get an ATS score for a resume based on general best practices.
        
        Args:
            resume_text: The text content of the resume to score
            
        Returns:
            Dict containing ATS score and feedback
        """
        if not self.groq_client or not self.groq_client.enabled:
            error_msg = "ATS scoring service is not available"
            logger.error(error_msg)
            return {
                "score": 0.0,
                "suggestions": [error_msg],
                "status": "error",
                "error": error_msg
            }
            
        try:
            # Create a prompt to get just the score and feedback
            prompt = f"""
            Analyze this resume and provide:
            1. An ATS compatibility score (0-100) based on general resume best practices
            2. A list of 3-5 key suggestions for improvement
            
            Resume:
            {resume_text}
            
            Format your response as JSON with these keys: score, suggestions
            """
            
            messages = [
                {
                    "role": "system", 
                    "content": "You are an ATS (Applicant Tracking System) expert. Analyze resumes and provide optimization feedback."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = await self.groq_client._make_request(messages)
            
            try:
                result = json.loads(response)
                return {
                    "score": result.get("score", 0),
                    "suggestions": result.get("suggestions", []),
                    "missing_keywords": result.get("missing_keywords", []),
                    "status": "success"
                }
            except json.JSONDecodeError:
                # Fallback if response isn't valid JSON
                return {
                    "score": 0,
                    "suggestions": ["Could not parse ATS feedback"],
                    "missing_keywords": [],
                    "status": "error",
                    "error": "Invalid response format from AI"
                }
                
        except Exception as e:
            logger.error(f"Error getting ATS score: {str(e)}")
            return {
                "score": 0,
                "suggestions": ["Error during ATS analysis. Please try again."],
                "missing_keywords": [],
                "status": "error",
                "error": str(e)
            }

# This will be initialized in main.py with the proper GroqClient instance
resume_optimizer = None
