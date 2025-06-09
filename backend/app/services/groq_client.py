"""
Groq client for handling AI interactions using the official Groq Python library.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from functools import partial
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Try to import Groq, but make it optional
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq library not available. Some features may be limited.")

class GroqClient:
    """Client for interacting with Groq's API using the official Python library."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Groq client.
        
        Args:
            api_key: Optional API key. If not provided, will use GROQ_API_KEY from environment.
            **kwargs: Additional arguments that might be passed from other services.
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.enabled = bool(self.api_key) and GROQ_AVAILABLE
        self.client = None

        logger.debug(f"GroqClient __init__ received kwargs: {kwargs}")
        logger.debug(f"GroqClient API Key: {'*' * 8 + self.api_key[-4:] if self.api_key else 'Not set'}")
        logger.debug(f"Groq available: {GROQ_AVAILABLE}")
        logger.debug(f"Environment variables: {os.environ.get('GROQ_API_KEY') and 'GROQ_API_KEY is set' or 'GROQ_API_KEY is not set'}")
        
        if not self.enabled:
            warning_msg = "Groq client is not enabled. "
            if not self.api_key:
                warning_msg += "GROQ_API_KEY is not set. "
            if not GROQ_AVAILABLE:
                warning_msg += "Groq Python package is not installed. "
            logger.warning(warning_msg)
            return
        
        try:
            api_key_to_use = self.api_key
            logger.debug(f"Preparing to initialize Groq library. API key is {'set' if api_key_to_use else 'not set'}.")

            if not api_key_to_use:
                logger.error("Groq API key is missing. Cannot initialize Groq client.")
                self.enabled = False
                return

            # Explicitly call Groq with only the api_key. This ensures no other kwargs are passed from this wrapper.
            logger.info(f"Initializing Groq library with api_key.")
            self.client = Groq(api_key=api_key_to_use)
            logger.info("Groq client initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            if hasattr(e, '__dict__'):
                logger.debug(f"Error details: {e.__dict__}")
            self.enabled = False
    
    async def _make_request(self, messages: List[Dict[str, str]], model: str = "llama-3.3-70b-versatile") -> Any:
        """
        Make a request to the Groq API with timeout and retry logic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use for the completion
            
        Returns:
            The parsed JSON response if possible, otherwise the raw text response
            
        Raises:
            RuntimeError: If the client is not properly configured
            asyncio.TimeoutError: If the request times out after all retries
            Exception: For other API errors
        """
        import asyncio
        from functools import partial
        import aiohttp
        import json
        
        if not self.enabled or not self.client:
            raise RuntimeError("Groq API is not properly configured. Please check your API key and client initialization.")
        
        max_retries = 2
        retry_delay = 1  # seconds
        
        # Ensure messages are properly formatted
        for msg in messages:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must have 'role' and 'content' keys")
        
        for attempt in range(max_retries + 1):
            task = None
            try:
                # Create a new event loop for this request to prevent hanging
                loop = asyncio.get_event_loop()
                
                # Log the request payload
                request_payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
                logger.info("\n=== GROQ API REQUEST ===")
                logger.info(json.dumps(request_payload, indent=2))
                logger.info("======================\n")
                
                # Create a task for the API call
                api_call = partial(
                    self.client.chat.completions.create,
                    **request_payload
                )
                
                # Use a timeout to prevent hanging
                task = asyncio.create_task(asyncio.to_thread(api_call))
                
                try:
                    # Wait for the task to complete with a timeout
                    chat_completion = await asyncio.wait_for(task, timeout=60)
                    
                    # Ensure we have a valid response
                    if not chat_completion or not hasattr(chat_completion, 'choices') or not chat_completion.choices:
                        raise ValueError("Invalid response from Groq API")
                    
                    response_content = chat_completion.choices[0].message.content
                    logger.info("\n=== GROQ API RESPONSE ===")
                    logger.info(response_content)
                    logger.info("=========================\n")
                    return response_content
                    
                except asyncio.TimeoutError:
                    # Cancel the task if it's still running
                    if task and not task.done():
                        task.cancel()
                        try:
                            await task  # This will raise a CancelledError
                        except asyncio.CancelledError:
                            pass  # Expected when cancelling
                            
                    if attempt == max_retries:
                        logger.error("Groq API request timed out after all retries")
                        raise
                        
                    logger.warning(f"Groq API request timed out, retrying... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    
                except Exception as e:
                    # Make sure to clean up the task if it's still running
                    if task and not task.done():
                        task.cancel()
                        try:
                            await task  # This will raise a CancelledError
                        except asyncio.CancelledError:
                            pass  # Expected when cancelling
                    raise
                    
            except asyncio.CancelledError:
                # If we're being cancelled, re-raise to the caller
                raise
                
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Error making request to Groq API after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Error in Groq API request, retrying... (attempt {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_delay * (attempt + 1))
        
        # If we've exhausted all retries
        raise RuntimeError("Failed to get a valid response from Groq API after all retries")
    
    async def generate_cv(self, cv_data: Dict[str, Any]) -> str:
        """
        Generate a CV by enhancing the provided content using Groq's AI.
        
        Args:
            cv_data: Dictionary containing CV data (personal_info, work_experience, education, skills, etc.)
            
        Returns:
            str: Enhanced CV content in markdown format
        """
        if not self.enabled or not self.client:
            raise RuntimeError("Groq client is not available")
        
        try:
            # Convert the input data to a clean format
            personal_info = cv_data.get("personal_info", {})
            work_exp = cv_data.get("work_experience", [])
            education = cv_data.get("education", [])
            skills = cv_data.get("skills", [])
            
            # Create a direct prompt that forces Groq to enhance the content
            prompt = """
            TASK: Completely rewrite and enhance the following CV information to be more professional and achievement-oriented.
            
            INSTRUCTIONS:
            1. DO NOT simply repeat the input. Significantly enhance and expand every section.
            2. For work experience, add 3-5 bullet points per role with specific achievements and metrics.
            3. Use strong action verbs (e.g., 'Spearheaded', 'Orchestrated', 'Optimized').
            4. Add quantifiable results wherever possible (e.g., 'Increased X by Y%', 'Reduced Z by W%').
            5. Include relevant technical skills and tools used in each role.
            6. Make the education section more detailed and professional.
            7. Organize skills into relevant categories.
            
            INPUT CV DATA:
            {input_data}
            
            OUTPUT FORMAT: Return ONLY the enhanced CV in markdown format with these sections:
            # [Full Name]
            [Contact Information]
            
            ## Professional Summary
            [3-4 sentence professional summary]
            
            ## Work Experience
            ### [Job Title] at [Company]
            [Date Range]
            - [Achievement 1 with metrics]
            - [Achievement 2 with metrics]
            
            ## Education
            ### [Degree] in [Field]
            [University Name], [Graduation Year]
            [Any honors or relevant coursework]
            
            ## Skills
            - **Category 1:** [Skill 1], [Skill 2]
            - **Category 2:** [Skill 3], [Skill 4]
            """.format(
                input_data=json.dumps({
                    "personal_info": personal_info,
                    "work_experience": work_exp,
                    "education": education,
                    "skills": skills
                }, indent=2, ensure_ascii=False)
            )
            
            messages = [
                {
                    "role": "system",
                    "content": """You are a professional CV writer with 10+ years of experience working with top tech companies. 
                    Your task is to completely rewrite and enhance the provided CV information to make it more professional and achievement-focused.
                    
                    IMPORTANT: Do NOT simply repeat the input. Significantly improve and expand upon every section with:
                    - Specific achievements and metrics
                    - Strong action verbs
                    - Relevant technical details
                    - Professional formatting
                    
                    The output should be a complete, ready-to-use CV that would impress hiring managers."""
                },
                {"role": "user", "content": prompt}
            ]
            
            # Get the enhanced CV content
            enhanced_cv = await self._make_request(messages)
            return enhanced_cv
            
        except Exception as e:
            logger.error(f"Error in generate_cv: {str(e)}")
            # Fallback to a simple format if enhancement fails
            return self._format_simple_cv(cv_data)
    
    def _format_simple_cv(self, cv_data: Dict[str, Any]) -> str:
        # Simple fallback CV formatting
        personal_info = cv_data.get("personal_info", {})
        work_exp = cv_data.get("work_experience", [])
        education = cv_data.get("education", [])
        skills = cv_data.get("skills", [])
        
        cv_text = "# Personal Information\n"
        cv_text += f"Name: {personal_info.get('name', '')}\n"
        cv_text += f"Email: {personal_info.get('email', '')}\n"
        cv_text += f"Phone: {personal_info.get('phone', '')}\n"
        cv_text += f"Location: {personal_info.get('location', '')}\n"
        cv_text += f"LinkedIn: {personal_info.get('linkedin', '')}\n"
        cv_text += f"Portfolio: {personal_info.get('portfolio', '')}\n"
        
        cv_text += "\n# Work Experience\n"
        for exp in work_exp:
            cv_text += f"### {exp.get('title', 'Position')} at {exp.get('company', 'Company')}\n"
            if "start_date" in exp or "end_date" in exp:
                start = exp.get("start_date", "")
                end = exp.get("end_date", "Present" if exp.get("current") else "")
                cv_text += f"{start} - {end}\n\n"
            
            if "description" in exp:
                if isinstance(exp["description"], list):
                    cv_text += "\n".join(f"- {item}" for item in exp["description"] if item)
                else:
                    cv_text += f"- {exp['description']}"
        
        cv_text += "\n# Education\n"
        for edu in education:
            cv_text += f"### {edu.get('degree', 'Degree')}\n"
            if "institution" in edu:
                cv_text += f"{edu['institution']}\n"
            
            if "start_date" in edu or "end_date" in edu:
                start = edu.get("start_date", "")
                end = edu.get("end_date", "")
                cv_text += f"{start} - {end}\n"
            
            if "gpa" in edu:
                cv_text += f"GPA: {edu['gpa']}\n"
        
        cv_text += "\n# Skills\n"
        cv_text += ", ".join(skills)
        
        return cv_text
        
    async def optimize_resume(self, resume_text: str, job_description: str = "") -> Dict[str, Any]:
        """
        Optimize a resume using Groq's AI based on general resume best practices.
        
        Args:
            resume_text: The text content of the resume to optimize
            job_description: Optional job description to optimize the resume for
            
        Returns:
            Dict containing the optimized resume, score, and suggestions
        """
        logger.info("=== STARTING RESUME OPTIMIZATION ===")
        logger.info(f"Resume length: {len(resume_text)} characters")
        logger.info(f"Job description provided: {'Yes' if job_description else 'No'}")
        logger.debug(f"Groq client enabled: {self.enabled}")
        logger.debug(f"Groq client initialized: {self.client is not None}")
        
        # Input validation
        if not resume_text or len(resume_text.strip()) < 50:
            error_msg = "Resume text is too short or empty"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "optimized_text": resume_text,
                "score": 0.0,
                "suggestions": [error_msg]
            }
            
        if not self.enabled or not self.client:
            error_msg = "Groq client is not enabled or not properly initialized"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "optimized_text": resume_text,
                "score": 0.0,
                "suggestions": [error_msg]
            }
            
        try:
            # Create a prompt for resume optimization
            try:
                logger.info("Creating optimization prompt...")
                prompt = """
                TASK: Optimize the following resume text following best practices for ATS (Applicant Tracking Systems)
                and modern resume standards.
                {job_description_section}
                RESUME TEXT:
                {resume_text}
                
                INSTRUCTIONS:
                1. Review the resume and suggest improvements based on ATS optimization best practices.
                {job_description_instruction}
                2. Generate an optimized version of the resume with improved formatting and content.
                3. Provide an ATS compatibility score (0-100).
                4. List 3-5 specific suggestions for improvement.
                5. Focus on clarity, action verbs, quantifiable achievements, and professional presentation.
                
                FORMAT YOUR RESPONSE AS A SINGLE JSON OBJECT with these fields:
                {{
                    "optimized_text": "The optimized resume text",
                    "score": 85,  # ATS compatibility score (0-100)
                    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
                    "keywords_matched": ["keyword1", "keyword2", ...],
                    "missing_keywords": ["keyword3", "keyword4", ...]
                }}
                """.format(
                    resume_text=resume_text[:8000],  # Limit size to prevent token limit issues
                    job_description_section=f"\nJOB DESCRIPTION TO MATCH:\n{job_description[:2000]}\n" if job_description else "",
                    job_description_instruction="1a. Tailor the resume to match the job description if relevant." if job_description else ""
                )
                
                messages = [
                    {
                        "role": "system",
                        "content": """You are an expert resume optimizer with deep knowledge of ATS systems and hiring practices. 
                        Your task is to help job seekers optimize their resumes following best practices.
                        
                        IMPORTANT: You MUST return a single valid JSON object with the specified fields.
                        The response must be valid JSON that can be parsed by Python's json.loads()."""
                    },
                    {"role": "user", "content": prompt}
                ]
                
                logger.debug("Sending request to Groq API...")
                # Get the optimization results with timeout
                response = await asyncio.wait_for(
                    self._make_request(messages, model="llama-3.3-70b-versatile"),
                    timeout=120  # 2 minutes timeout
                )
                logger.info("Received response from Groq API")
                
            except asyncio.TimeoutError:
                error_msg = "Request to Groq API timed out after 2 minutes"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Error creating prompt or making request: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise
            
            try:
                logger.debug("Parsing response from Groq API...")
                # Clean up the response first - remove control characters except newlines and tabs
                response = ''.join(char for char in response if ord(char) >= 32 or char in '\n\r\t')
                response = response.strip()
                
                # Try to parse the response as JSON directly
                try:
                    # First try direct JSON parse
                    result = json.loads(response)
                    logger.debug("Successfully parsed direct JSON response")
                except json.JSONDecodeError as e:
                    logger.debug(f"Direct JSON parse failed: {str(e)}. Trying to clean and extract JSON...")
                    
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response, re.DOTALL) 
                    if not json_match:
                        # If no code block, try to find JSON object directly
                        json_match = re.search(r'(\{[\s\S]*\})', response)
                    
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            # Clean the JSON string
                            json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')
                            # Try to fix common JSON issues
                            json_str = json_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                            json_str = re.sub(r'([\{\[,])\s*([}\],])', r'\1""\2', json_str)  # Add empty strings for missing values
                            
                            # Try to parse the cleaned JSON
                            result = json.loads(json_str)
                            logger.debug("Successfully parsed JSON after cleaning")
                        except json.JSONDecodeError as e2:
                            logger.error(f"Failed to parse JSON after cleaning: {str(e2)}")
                            # Try to salvage what we can by extracting key-value pairs
                            try:
                                result = {}
                                # Extract optimized_text
                                text_match = re.search(r'"optimized_text"\s*:\s*"(.*?)(?<!\\)"', json_str, re.DOTALL)
                                if text_match:
                                    result['optimized_text'] = text_match.group(1).replace('\\"', '"')
                                
                                # Extract score
                                score_match = re.search(r'"score"\s*:\s*(\d+(?:\.\d+)?)', json_str)
                                if score_match:
                                    result['score'] = float(score_match.group(1))
                                
                                # Extract suggestions
                                suggestions_match = re.search(r'"suggestions"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                if suggestions_match:
                                    suggestions_str = suggestions_match.group(1)
                                    suggestions = [s.strip(' "\'') for s in re.findall(r'"(.*?)(?<!\\)"', suggestions_str)]
                                    result['suggestions'] = suggestions
                                
                                if not result:
                                    raise ValueError("Could not extract any fields from response")
                                
                                logger.debug("Partially parsed JSON using regex extraction")
                                
                            except Exception as e3:
                                logger.error(f"Failed to extract fields using regex: {str(e3)}")
                                raise ValueError("Could not parse response as valid JSON")
                
                # Validate the result structure
                required_fields = ["optimized_text", "score", "suggestions"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field in response: {field}")
                
                # Ensure score is a number between 0 and 100
                try:
                    result["score"] = max(0, min(100, float(result["score"])))
                except (ValueError, TypeError):
                    result["score"] = 0.0
                
                # Ensure suggestions is a list
                if not isinstance(result.get("suggestions"), list):
                    result["suggestions"] = [str(s) for s in result.get("suggestions", "").split("\n") if s.strip()]
                
                # Add missing fields if not present
                result["keywords_matched"] = result.get("keywords_matched", [])
                result["missing_keywords"] = result.get("missing_keywords", [])
                result["status"] = "success"
                
                logger.info(f"Optimization completed successfully. Score: {result.get('score')}")
                return result
                
            except Exception as e:
                error_msg = f"Failed to parse Groq API response: {str(e)}"
                logger.error(f"{error_msg}. Response: {response[:500]}...")  # Log first 500 chars of response
                
                # If we can't parse JSON, return the original with an error
                return {
                    "optimized_text": resume_text,
                    "score": 0.0,
                    "suggestions": [f"Failed to parse optimization response: {str(e)}. Showing original resume."],
                    "status": "error",
                    "error": error_msg,
                    "keywords_matched": [],
                    "missing_keywords": []
                }
        except Exception as e:
            logger.error(f"Error in optimize_resume: {str(e)}", exc_info=True)
            return {
                "optimized_text": resume_text,
                "score": 0.0,
                "suggestions": [f"Error during optimization: {str(e)}"],
                "status": "error"
            }

    async def generate_cover_letter(self, resume_text: str, job_description: str, tone: str = "professional") -> str:
        """
        Generate a cover letter based on resume and job description.
        
        Args:
            resume_text: The resume text
            job_description: The job description
            tone: The desired tone (e.g., professional, enthusiastic, formal)
            
        Returns:
            Generated cover letter text
        """
        if not self.enabled:
            return "Groq client is not enabled. Unable to generate cover letter."
            
        try:
            prompt = f"""
            Write a {tone} cover letter based on the following resume and job description.
            
            Resume:
            {resume_text}
            
            Job Description:
            {job_description}
            
            Please generate a well-structured cover letter that highlights the candidate's
            relevant experience and skills for this position. Focus on how their background
            makes them a strong fit for the role.
            """
            
            # Call Groq API
            
            response = await self._make_request(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192"
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}", exc_info=True)
            return f"Error generating cover letter: {str(e)}"

    async def generate_portfolio(
        self,
        resume_data: Dict[str, Any],
        sections: List[str]
    ) -> Dict[str, Any]:
        """
        Generate portfolio content based on resume data and selected sections.
        
        Args:
            resume_data: Processed resume data
            sections: List of sections to include in the portfolio
            
        Returns:
            Dict containing the generated portfolio content
        """
        if not self.enabled or not self.client:
            raise RuntimeError("Groq client is not enabled. Please check your API key.")
            
        try:
            # Prepare the prompt for Groq
            prompt = self._build_portfolio_prompt(resume_data, sections)
            
            # Prepare messages for the API call
            messages = [
                {
                    "role": "system", 
                    "content": """You are a professional portfolio generator. Create a well-structured, 
                    professional portfolio based on the provided resume data. Focus on creating clear, 
                    engaging content that highlights the person's skills and experience."""
                },
                {"role": "user", "content": prompt}
            ]
            
            # Call Groq API using the async _make_request method
            content = await self._make_request(
                messages=messages,
                model="mixtral-8x7b-32768"
            )
            
            # Try to parse the response as JSON
            try:
                # Clean up the response first
                content = content.strip()
                if content.startswith('```json'):
                    content = content[content.find('{'):content.rfind('}')+1]
                elif content.startswith('```'):
                    content = content[content.find('\n')+1:content.rfind('```')].strip()
                
                portfolio_data = json.loads(content)
                return portfolio_data
                
            except json.JSONDecodeError:
                # If we can't parse as JSON, return as plain text
                logger.warning("Could not parse portfolio response as JSON, returning as plain text")
                return {"content": content}
            
        except Exception as e:
            logger.error(f"Error generating portfolio with Groq: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to generate portfolio: {str(e)}")
    
    def _build_portfolio_prompt(self, resume_data: Dict[str, Any], sections: List[str]) -> str:
        """Build the prompt for portfolio generation."""
        # Extract the actual resume content from the resume_data
        resume_content = resume_data.get('content', '')
        analysis = resume_data.get('analysis', {})
        
        # Build a more structured prompt
        prompt = """# Portfolio Generation Task

## Instructions:
Create a professional portfolio based on the following resume information. The portfolio should be well-structured, 
engaging, and highlight the person's skills and experience in a professional manner.

## Required Sections:
- {sections}

## Resume Content:
{resume_content}

## Additional Analysis:
{analysis}

## Output Format:
Return a JSON object with the following structure:
{{
  "sections": [
    {{
      "name": "section_name",
      "content": "Formatted content with proper markdown formatting"
    }}
  ]
}}

## Guidelines:
1. Use professional language and tone
2. Include relevant details from the resume
3. Structure the content for easy reading
4. Use markdown for formatting (headings, lists, etc.)
5. Ensure all provided sections are included
6. Generate appropriate content for each section based on the resume data
"""
        return prompt.format(
            sections="\n- ".join([""] + sections),  # Add bullet points
            resume_content=resume_content[:5000],  # Limit length to avoid token limits
            analysis=json.dumps(analysis, indent=2) if isinstance(analysis, dict) else str(analysis)
        )

    async def generate_portfolio(self, resume_text: str, sections: List[str]) -> Dict[str, Any]:
        """
        Generate portfolio content based on resume text and selected sections.
        
        Args:
            resume_text: The text content of the resume
            sections: List of section names to include in the portfolio
            
        Returns:
            Dict containing the generated portfolio content and metadata
        """
        if not self.enabled or not self.client:
            raise RuntimeError("Groq client is not properly configured")
            
        try:
            # Prepare the prompt for portfolio generation
            prompt = f"""
            Based on the following resume, generate a professional portfolio with these sections: {', '.join(sections)}.
            
            Resume:
            {resume_text}
            
            For each section, provide well-formatted markdown content that highlights the person's qualifications.
            Make the content professional, concise, and impactful.
            """
            
            messages = [
                {"role": "system", "content": "You are a professional resume and portfolio writer. Create a well-structured portfolio based on the provided resume."},
                {"role": "user", "content": prompt}
            ]
            
            # Generate content using Groq
            response = await self._make_request(messages)
            
            # Process the response
            if response and 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0].get('message', {}).get('content', '')
                return {
                    'status': 'success',
                    'content': content,
                    'sections': sections,
                    'model': response.get('model', 'unknown'),
                    'usage': response.get('usage', {})
                }
            else:
                raise ValueError("Failed to generate portfolio content")
                
        except Exception as e:
            logger.error(f"Error generating portfolio: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'details': 'Failed to generate portfolio content'
            }

# Create a global instance of the GroqClient
groq_client = GroqClient()
