import os
import base64
import requests
import json
import logging
import streamlit as st
from typing import Optional, Dict, Any
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Backend API configuration
BACKEND_URL = "http://localhost:8000"  # Update this in production to your backend URL

class APIService:
    """Service class to handle all API calls to the backend."""
    
    @staticmethod
    def _get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
        """Generate headers with authorization if token is provided."""
        headers = {"Content-Type": "application/json"}
        
        # Add API key for backend authentication
        headers["X-API-Key"] = "test-key"  # This should be moved to environment variables in production
        
        # Try to get token from session state if not provided
        if token is None and hasattr(st, 'session_state') and 'jwt_token' in st.session_state:
            token = st.session_state.jwt_token
        
        # Add JWT token if available (for future use)
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        return headers
        
    @staticmethod
    def _make_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the backend API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/api/portfolio/generate')
            **kwargs: Additional arguments to pass to requests.request()
            
        Returns:
            Dict containing the response data or error information
        """
        url = f"{BACKEND_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Get auth headers
        headers = kwargs.pop('headers', {})
        token = kwargs.pop('token', None)
        auth_headers = APIService._get_auth_headers(token)
        headers.update(auth_headers)
        
        # Log the request
        logger.info(f"Making {method} request to {url}")
        if 'json' in kwargs:
            logger.debug(f"Request data: {kwargs['json']}")
            
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            return APIService._handle_response(response)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
        
    @staticmethod
    def _handle_response(response: requests.Response) -> Dict[str, Any]:
        """Handle API response and return JSON data or raise an exception."""
        try:
            # First, log the raw response for debugging
            logger.info(f"Raw API response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
            
            # Log the raw response content
            raw_content = response.text
            logger.info(f"Raw response content: {raw_content[:1000]}...")
            
            # Try to parse JSON
            try:
                json_data = response.json()
                logger.info(f"Parsed JSON response: {json.dumps(json_data, indent=2)[:1000]}...")
                return json_data
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON response: {str(json_err)}")
                logger.error(f"Response content type: {response.headers.get('content-type')}")
                logger.error(f"Response content (first 1000 chars): {raw_content[:1000]}")
                return {"status": "error", "message": f"Invalid JSON response: {str(json_err)}"}
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            logger.error(f"Response status code: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response text: {response.text}")
            
            try:
                error_data = response.json()
                logger.error(f"Error data from JSON response: {error_data}")
                return {
                    "status": "error", 
                    "message": error_data.get("detail", str(e)), 
                    "details": error_data,
                    "status_code": response.status_code
                }
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from error response.")
                return {
                    "status": "error", 
                    "message": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                    
        except Exception as e:
            logger.error(f"An unexpected error occurred while handling API response: {str(e)}", exc_info=True)
            return {
                "status": "error", 
                "message": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def health_check() -> Dict[str, Any]:
        """Check if the backend is running."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health")
            return {"status": response.status_code == 200, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"status": False, "error": str(e)}
    
    @staticmethod
    def process_resume(file_path: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Process a resume file through the backend."""
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
                response = requests.post(
                    f"{BACKEND_URL}/api/portfolio/upload",
                    files=files,
                    headers=APIService._get_auth_headers(token)
                )
                return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    @staticmethod
    def get_resume_data(resume_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch resume data from the backend using resume_id.
        
        Args:
            resume_id: The ID of the resume to fetch
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the resume data or error information
        """
        try:
            if not resume_id:
                return {"status": "error", "message": "No resume ID provided"}
                
            # Use the _make_request method to handle the API call
            return APIService._make_request(
                method="GET",
                endpoint=f"/api/resumes/{resume_id}",
                headers={"Content-Type": "application/json"},
                token=token
            )
            
        except Exception as e:
            error_msg = f"Failed to fetch resume data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
            
    @staticmethod
    def generate_ai_content(data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AI-enhanced content for portfolio sections.
        
        Args:
            data: Dictionary containing:
                - prompt: The prompt for the AI
                - section: The portfolio section being enhanced
                - resume_data: The parsed resume data
                - existing_content: Any existing content to refine
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the generated content or error information
        """
        try:
            return APIService._make_request(
                method="POST",
                endpoint="/api/portfolio/ai/enhance",
                json=data,
                token=token
            )
        except Exception as e:
            error_msg = f"Failed to generate AI content: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
            
    @staticmethod
    def suggest_portfolio_sections(resume_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get AI-suggested sections for a portfolio based on resume data.
        
        Args:
            resume_data: The parsed resume data
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing suggested sections or error information
        """
        try:
            return APIService._make_request(
                method="POST",
                endpoint="/api/portfolio/ai/suggest-sections",
                json={"resume_data": resume_data},
                token=token
            )
        except Exception as e:
            error_msg = f"Failed to get section suggestions: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
            
    @staticmethod
    def generate_portfolio(data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a portfolio with AI enhancements.
        
        Args:
            data: Dictionary containing portfolio generation parameters:
                - resume_id: The ID of the resume to use
                - template: The template to use
                - color_theme: The color theme to apply
                - sections: List of sections to include
                - use_ai_enhancement: Whether to use AI enhancement
                - personal_info: Dictionary of personal information
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the generated portfolio or error information
        """
        try:
            return APIService._make_request(
                method="POST",
                endpoint="/api/portfolio/generate",
                json=data,
                token=token
            )
        except Exception as e:
            error_msg = f"Failed to generate portfolio: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
            
    @staticmethod
    def generate_cover_letter(data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a cover letter using the backend API.
        
        Args:
            data: Dictionary containing:
                - resume_text: The text content of the resume
                - job_description: The job description to target
                - tone: The desired tone (professional, friendly, formal, enthusiastic)
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the generated cover letter or error information
        """
        try:
            # Ensure required fields are present
            required_fields = ['resume_text', 'job_description']
            for field in required_fields:
                if field not in data or not data[field].strip():
                    error_msg = f"Missing required field: {field}"
                    logger.error(error_msg)
                    return {"status": "error", "message": error_msg}
            
            # Set default tone if not provided
            if 'tone' not in data or not data['tone'].strip():
                data['tone'] = 'professional'
            
            # Log the request data (excluding potentially large resume text)
            log_data = data.copy()
            if 'resume_text' in log_data:
                log_data['resume_text'] = f"[RESUME_TEXT_LENGTH: {len(log_data['resume_text'])} chars]"
            logger.info(f"Sending cover letter generation request: {log_data}")
            
            # Make the API request with JSON data
            headers = APIService._get_auth_headers(token)
            
            # Prepare JSON data
            json_data = {
                'resume_text': data['resume_text'],
                'job_description': data['job_description'],
                'tone': data['tone'].lower()
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/cover-letter/legacy-generate",
                json=json_data,  # Use json= to send as JSON
                headers=headers,
                timeout=60  # 60 seconds timeout
            )
            
            # Process the response
            result = APIService._handle_response(response)
            
            # Log the result status
            if result.get('status') == 'success':
                logger.info("Successfully generated cover letter")
            else:
                logger.error(f"Failed to generate cover letter: {result.get('message', 'Unknown error')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while generating cover letter: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error generating cover letter: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    @staticmethod
    def generate_cv(cv_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a CV with the provided data.
        
        Args:
            cv_data: Dictionary containing CV data (personal_info, work_experience, education, skills, etc.)
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the CV generation result or error information
        """
        try:
            # Debug: Print the data we're sending (excluding binary data)
            log_data = cv_data.copy()
            if 'content' in log_data and isinstance(log_data['content'], (bytes, bytearray)):
                log_data['content'] = f"[binary data, size: {len(log_data['content'])} bytes]"
            print(f"[DEBUG] Sending CV generation request with data: {log_data}")
            
            # Prepare work experience data
            work_experience = []
            for exp in cv_data.get('work_experience', []):
                # Ensure description is a list of strings
                description = exp.get('description', '')
                if not isinstance(description, list):
                    description = [description] if description else []
                elif description and not isinstance(description[0], str):
                    description = [str(d) for d in description]
                
                # Format dates (convert MM/YYYY to YYYY-MM-DD)
                start_date = exp.get('start_date', '')
                if start_date and '/' in start_date:
                    month, year = start_date.split('/')
                    start_date = f"{year}-{month.zfill(2)}-01"
                
                end_date = exp.get('end_date', '')
                is_current = exp.get('is_current', False) or (isinstance(end_date, str) and end_date.lower() == 'present')
                
                if end_date and not is_current and '/' in end_date:
                    month, year = end_date.split('/')
                    end_date = f"{year}-{month.zfill(2)}-01"
                elif is_current:
                    end_date = None  # Will be set to None for current jobs
                
                work_exp = {
                    "title": exp.get('position', exp.get('title', '')),  # Try both position and title
                    "company": exp.get('company', ''),
                    "start_date": start_date,
                    "end_date": end_date,
                    "current": is_current,
                    "description": description,
                    "location": exp.get('location', '')
                }
                work_experience.append(work_exp)
            
            # Prepare education data
            education = []
            for edu in cv_data.get('education', []):
                # Format dates (convert YYYY to YYYY-01-01)
                start_year = edu.get('start_year', '')
                start_date = f"{start_year}-01-01" if start_year and len(start_year) == 4 else ''
                
                end_year = edu.get('end_year', '')
                is_ongoing = edu.get('is_ongoing', False)
                end_date = None
                
                if is_ongoing:
                    end_date = None  # Current education
                elif end_year and len(end_year) == 4:
                    end_date = f"{end_year}-12-31"
                
                edu_data = {
                    "degree": edu.get('degree', ''),
                    "institution": edu.get('institution', ''),
                    "field_of_study": edu.get('field_of_study', ''),
                    "start_date": start_date,
                    "end_date": end_date,
                    "gpa": float(edu.get('gpa', 0)) if edu.get('gpa') else None
                }
                education.append(edu_data)
            
            # Prepare personal info
            personal_info = cv_data.get('personal_info', {})
            
            # Prepare the final request data according to backend's CVGenerationRequest model
            request_data = {
                "personal_info": {
                    "name": personal_info.get('name', 
                        f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}".strip()
                    ),
                    "email": personal_info.get('email', ''),
                    "phone": personal_info.get('phone', ''),
                    "location": personal_info.get('location', ''),
                    "summary": personal_info.get('summary', '')
                },
                "work_experience": work_experience,
                "education": education,
                "skills": cv_data.get('skills', []),
                "template": cv_data.get('template', 'modern'),
                "format": cv_data.get('format', 'pdf').lower()  # Ensure lowercase format
            }
            
            # Debug: Print the final request data
            print("[DEBUG] Final request data:", json.dumps(request_data, indent=2))
            
            # Make the request using _make_request to handle errors and auth
            response = APIService._make_request(
                method="POST",
                endpoint="/api/cv/generate",
                json=request_data,
                token=token
            )
            
            # If we get here, the request was successful
            print("[DEBUG] CV generation response:", json.dumps(response, indent=2))
            
            # If the response contains base64 content, decode it
            if response.get('status') == 'success' and 'content' in response:
                try:
                    response['content'] = base64.b64decode(response['content'])
                except Exception as e:
                    print(f"[WARNING] Failed to decode base64 content: {str(e)}")
            
            return response
            
        except Exception as e:
            error_msg = f"Failed to generate CV: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}
    
    @staticmethod
    def download_cv(cv_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a generated CV by its ID.
        
        Args:
            cv_id: The ID of the CV to download
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the file data or error information
        """
        try:
            # Add debug logging
            print(f"[DEBUG] Attempting to download CV with ID: {cv_id}")
            
            # Make the request with a reasonable timeout
            response = requests.get(
                f"{BACKEND_URL}/api/cv/download/{cv_id}",
                headers=APIService._get_auth_headers(token),
                stream=True,
                timeout=30  # 30 seconds timeout
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Get content type and content
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            content = response.content
            
            # Determine file extension from content type
            file_ext = 'bin'
            if 'pdf' in content_type:
                file_ext = 'pdf'
            elif 'word' in content_type or 'officedocument.wordprocessingml' in content_type:
                file_ext = 'docx'
            elif 'markdown' in content_type or 'text/plain' in content_type:
                file_ext = 'md'
            
            print(f"[DEBUG] Successfully downloaded CV. Content-Type: {content_type}, Size: {len(content)} bytes")
            
            return {
                'status': 'success',
                'content': content,
                'content_type': content_type,
                'filename': f'cv_{cv_id}.{file_ext}'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while downloading CV: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error while downloading CV: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}
    
    @staticmethod
    def generate_portfolio(data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Generate a portfolio with the provided data."""
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/portfolio/generate",
                json=data,
                headers=APIService._get_auth_headers(token)
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def generate_cv(data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a CV with the provided data.
        
        Args:
            data: Dictionary containing CV data
            token: Optional JWT token for authentication
            
        Returns:
            Dict containing the CV content and metadata or error information
        """
        try:
            # Log the data being sent (excluding large binary data)
            log_data = data.copy()
            if 'content' in log_data and isinstance(log_data['content'], (bytes, bytearray)):
                log_data['content'] = f"[binary data, size: {len(log_data['content'])} bytes]"
            print(f"[DEBUG] Sending CV generation request with data: {log_data}")
            
            # Make the request
            response = requests.post(
                f"{BACKEND_URL}/api/cv/generate",
                json=data,
                headers=APIService._get_auth_headers(token),
                timeout=190  # 190 seconds timeout (backend is 180s)
            )
            
            # Log the response status and headers
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {response.headers}")
            
            # Handle non-200 responses
            response.raise_for_status()
            
            # Parse the JSON response
            try:
                result = response.json()
                print(f"[DEBUG] Successfully parsed JSON response. Keys: {list(result.keys())}")
            except ValueError as e:
                # If JSON parsing fails, try to get text content
                error_msg = f"Failed to parse JSON response: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return {"status": "error", "message": error_msg, "raw_response": response.text[:1000]}
            
            # Check if the response contains the CV content
            if result.get('status') != 'success' or 'content' not in result:
                error_msg = result.get('message', 'Failed to generate CV')
                print(f"[ERROR] CV generation failed: {error_msg}")
                return {"status": "error", "message": error_msg, "details": result}
            
            # Decode the base64 content
            try:
                content = base64.b64decode(result['content'])
                print(f"[DEBUG] Successfully decoded CV content, size: {len(content)} bytes")
                
                # Create a response dict with the binary content
                response_data = {
                    "status": "success",
                    "cv_id": result.get('cv_id'),
                    "content": content,  # This is the binary content
                    "content_type": result.get('content_type', 'application/octet-stream'),
                    "filename": result.get('filename', f'cv.{data.get("format", "pdf")}'),
                    "format": result.get('format', data.get('format', 'pdf'))
                }
                
                # Debug: Log the response data (excluding binary content)
                debug_data = response_data.copy()
                debug_data['content'] = f"[binary data, size: {len(content)} bytes]"
                print(f"[DEBUG] Returning response data: {debug_data}")
                
                return response_data
                
            except Exception as decode_error:
                error_msg = f"Failed to process CV content: {str(decode_error)}"
                print(f"[ERROR] {error_msg}")
                print(f"[DEBUG] Content type: {type(result.get('content'))}, length: {len(result.get('content', '')) if isinstance(result.get('content'), (str, bytes, bytearray)) else 'N/A'}")
                return {"status": "error", "message": error_msg, "error_type": type(decode_error).__name__}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg, "error_type": type(e).__name__}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": error_msg, "error_type": type(e).__name__}
    
    @staticmethod
    def optimize_resume(resume_text: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Optimize a resume based on ATS best practices.
        
        Args:
            resume_text: The text content of the resume to optimize
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing:
                - status: 'success' or 'error'
                - optimized_text: The optimized resume text (if successful)
                - score: ATS compatibility score (0-100)
                - suggestions: List of improvement suggestions
                - message: Error message if status is 'error'
        """
        try:
            url = f"{BACKEND_URL}/api/optimize/resume"
            headers = APIService._get_auth_headers(token)
            
            # Log request details (safely)
            logger.info(f"Sending resume optimization request to {url}")
            logger.debug(f"Resume text length: {len(resume_text)} characters")
            
            # Log first 200 chars of resume for debugging
            sample_text = resume_text[:200].replace('\n', ' ').replace('\r', '')
            logger.debug(f"Resume sample: {sample_text}...")
            
            # Prepare request data
            request_data = {"resume_text": resume_text}
            logger.debug(f"Request data prepared, size: {len(str(request_data))} bytes")
            
            # Make the request to the backend
            logger.info("Sending POST request to backend...")
            response = requests.post(
                url,
                json=request_data,
                headers=headers,
                timeout=120  # 120 seconds timeout for processing
            )
            
            # Log response status and headers
            logger.info(f"Received response with status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Try to parse JSON response
            try:
                # First, clean the response text of control characters
                cleaned_text = ''.join(char for char in response.text if ord(char) >= 32 or char in '\n\r\t')
                
                # Try to parse the cleaned JSON
                try:
                    response_data = json.loads(cleaned_text)
                    logger.debug(f"Parsed JSON response: {json.dumps(response_data, indent=2)[:500]}...")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse cleaned JSON. Error: {str(e)}")
                    # Try to find where the error occurred
                    error_pos = e.pos
                    context = 50
                    start = max(0, error_pos - context)
                    end = min(len(cleaned_text), error_pos + context)
                    error_context = cleaned_text[start:end]
                    logger.error(f"Error context: ...{error_context}...")
                    
                    # Try to fix common JSON issues
                    try:
                        # Try to extract valid JSON using regex as a last resort
                        import re
                        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
                        if json_match:
                            response_data = json.loads(json_match.group(0))
                            logger.info("Successfully extracted JSON using regex fallback")
                        else:
                            raise json.JSONDecodeError("No valid JSON found in response", cleaned_text, 0)
                    except Exception as inner_e:
                        logger.error(f"Failed to recover JSON: {str(inner_e)}")
                        return {
                            "status": "error",
                            "message": f"Invalid JSON in response: {str(e)}\nContext: ...{error_context}...",
                            "response_text": cleaned_text[:1000]
                        }
            except Exception as e:
                logger.error(f"Unexpected error parsing response: {str(e)}")
                return {
                    "status": "error", 
                    "message": f"Failed to process server response: {str(e)}",
                    "response_text": response.text[:1000] if hasattr(response, 'text') else 'No response text'
                }
            
            if response.status_code != 200:
                error_msg = response_data.get("detail", f"Error {response.status_code}: {response.text[:500]}")
                logger.error(f"API Error: {error_msg}")
                return {
                    "status": "error", 
                    "message": error_msg,
                    "status_code": response.status_code
                }
            
            # Prepare the result
            result = {
                "status": "success",
                "score": response_data.get('score', 0),
                "optimized_text": response_data.get('optimized_text', resume_text),
                "suggestions": response_data.get('suggestions', []),
                "missing_keywords": response_data.get('missing_keywords', [])
            }
            
            logger.info(f"Optimization successful. Score: {result.get('score', 'N/A')}")
            return result
                
        except requests.exceptions.Timeout:
            error_msg = "Request timed out after 120 seconds. The server is taking too long to respond."
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to the server: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error", 
                "message": error_msg,
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def get_portfolio_questions() -> Dict[str, Any]:
        """Get the list of guided questions for portfolio creation."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/portfolio/questions")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def download_file(file_id: str, file_type: str = "portfolio", token: Optional[str] = None) -> Optional[bytes]:
        """Download a file from the backend."""
        try:
            endpoint = f"{BACKEND_URL}/api/{file_type}/download/{file_id}"
            response = requests.get(
                endpoint,
                headers=APIService._get_auth_headers(token),
                stream=True
            )
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
            
    @staticmethod
    def _get_mime_type(file_path: str) -> str:
        """
        Get the MIME type based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MIME type string
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return 'application/pdf'
        elif ext == '.docx':
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif ext == '.txt':
            return 'text/plain'
        return 'application/octet-stream'
    
    @staticmethod
    def upload_cover_letter_resume(file_path: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a resume file for cover letter generation.
        
        Args:
            file_path: Path to the resume file
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the upload result with resume_id or error information
            Format: {
                'status': 'success'|'error',
                'resume_id': str,  # Only if status is 'success'
                'message': str      # Error message if status is 'error'
            }
        """
        try:
            mime_type = APIService._get_mime_type(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, mime_type)}
                headers = APIService._get_auth_headers(token)
                # Remove Content-Type from headers as it's set by requests when using files
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                    
                response = requests.post(
                    f"{BACKEND_URL}/api/cover-letter/upload-resume",
                    files=files,
                    headers=headers
                )
                
                # Handle the response and ensure consistent format
                response_data = APIService._handle_response(response)
                
                # If the response contains a resume_id, return success format
                if 'resume_id' in response_data:
                    return {
                        'status': 'success',
                        'resume_id': response_data['resume_id']
                    }
                # If the response indicates an error, return error format
                elif 'status' in response_data and response_data['status'] == 'error':
                    return {
                        'status': 'error',
                        'message': response_data.get('message', 'Failed to upload resume')
                    }
                # For any other format, return a generic success with the data
                return {'status': 'success', **response_data}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def upload_portfolio_resume(file_path: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a resume file for portfolio generation.
        
        Args:
            file_path: Path to the resume file
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the upload result with resume_id or error information
            Format: {
                'status': 'success'|'error',
                'resume_id': str,  # Only if status is 'success'
                'message': str      # Error message if status is 'error'
            }
        """
        try:
            mime_type = APIService._get_mime_type(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, mime_type)}
                headers = APIService._get_auth_headers(token)
                # Remove Content-Type from headers as it's set by requests when using files
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                    
                response = requests.post(
                    f"{BACKEND_URL}/api/portfolio/upload-resume",
                    files=files,
                    headers=headers
                )
                
                # Handle the response and ensure consistent format
                response_data = APIService._handle_response(response)
                
                # If the response contains a resume_id, return success format
                if 'resume_id' in response_data:
                    return {
                        'status': 'success',
                        'resume_id': response_data['resume_id']
                    }
                # If the response indicates an error, return error format
                elif 'status' in response_data and response_data['status'] == 'error':
                    return {
                        'status': 'error',
                        'message': response_data.get('message', 'Failed to upload resume')
                    }
                # For any other format, return a generic success with the data
                return {'status': 'success', **response_data}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def generate_portfolio(portfolio_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a portfolio with the provided data.
        
        Args:
            portfolio_data: Dictionary containing portfolio data
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the portfolio generation result or error information
        """
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/portfolio/generate",
                json=portfolio_data,
                headers=APIService._get_auth_headers(token)
            )
            return APIService._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    @staticmethod
    def get_portfolio_preview(portfolio_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a preview of the generated portfolio.
        
        Args:
            portfolio_id: ID of the generated portfolio
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the portfolio preview HTML or error information
        """
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/portfolio/preview/{portfolio_id}",
                headers=APIService._get_auth_headers(token)
            )
            return APIService._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    @staticmethod
    def download_portfolio(portfolio_id: str, format: str = 'html', token: Optional[str] = None) -> Dict[str, Any]:
        """
        Download the generated portfolio in the specified format.
        
        Args:
            portfolio_id: ID of the generated portfolio
            format: Format to download (html, pdf, zip)
            token: Optional JWT token for authenticated requests
            
        Returns:
            Dict containing the download URL or error information
        """
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/portfolio/download/{portfolio_id}?format={format}",
                headers=APIService._get_auth_headers(token)
            )
            return APIService._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": str(e)}
