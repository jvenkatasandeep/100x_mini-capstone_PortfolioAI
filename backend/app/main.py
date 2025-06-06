"""
PortfolioAI Backend - Simplified MVP
"""
import base64
import os
from typing import Generator
from sqlalchemy.orm import Session

# Database
from .database.local_config import get_db, init_db, Base
from .database.models import User, Portfolio, CV, CoverLetter, APICall
import uuid

# Initialize database
init_db()
import tempfile
import shutil
import logging
import json
import uuid
import asyncio
import base64
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
from .services.portfolio_builder import PortfolioBuilder

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request, Form, APIRouter, status
from pydantic import ValidationError, BaseModel, Field
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import re
from typing import Optional
from pydantic import BaseModel, Field, model_validator, field_validator, validator
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from sqlalchemy.orm import Session

# Import database models and session
from .database.models import CV, User, Portfolio, APICall, CoverLetter, ResumeOptimization

# All routes are defined directly in this file

# Import and initialize services with proper dependency injection
def init_services():
    # Import services
    from .services.groq_client import GroqClient
    from .services.portfolio_builder import PortfolioBuilder
    from .services.optimizer import ResumeOptimizer
    from .services.cv_generator import CVGenerator
    from .services.cover_letter_generator import CoverLetterGenerator
    
    # Initialize Groq client first
    groq_client = GroqClient()
    
    # Initialize services with dependencies
    portfolio_builder = PortfolioBuilder(groq_client)
    cv_generator = CVGenerator()
    cover_letter_generator = CoverLetterGenerator()
    resume_optimizer = ResumeOptimizer(groq_client)
    
    # Return all initialized services
    return {
        'groq_client': groq_client,
        'portfolio_builder': portfolio_builder,
        'cv_generator': cv_generator,
        'cover_letter_generator': cover_letter_generator,
        'resume_optimizer': resume_optimizer
    }

# Initialize all services
services = init_services()

# Make services available at module level
groq_client = services['groq_client']
portfolio_builder = services['portfolio_builder']
cv_generator = services['cv_generator']
cover_letter_generator = services['cover_letter_generator']
resume_optimizer = services['resume_optimizer']

# Import utilities after services are initialized
from .utils.file_utils import get_temp_file, is_file_supported, cleanup_file as utils_cleanup_file

# Import modules after services are initialized
def update_module_variables():
    modules = {
        'portfolio_module': None,
        'optimizer_module': None,
        'cv_module': None,
        'cl_module': None
    }
    
    try:
        from .services import portfolio_builder as portfolio_module
        from .services import optimizer as optimizer_module
        from .services import cv_generator as cv_module
        from .services import cover_letter_generator as cl_module
        from .services.groq_client import GroqClient
        
        # Store the modules
        modules.update({
            'portfolio_module': portfolio_module,
            'optimizer_module': optimizer_module,
            'cv_module': cv_module,
            'cl_module': cl_module
        })
        
        # Initialize Groq client
        groq_client = GroqClient()
        
        # Initialize portfolio_builder if not already initialized
        if hasattr(portfolio_module, 'PortfolioBuilder'):
            if not hasattr(portfolio_module, 'portfolio_builder') or portfolio_module.portfolio_builder is None:
                portfolio_module.portfolio_builder = portfolio_module.PortfolioBuilder(groq_client)
        
        # Set other service instances
        if hasattr(optimizer_module, 'resume_optimizer'):
            optimizer_module.resume_optimizer = resume_optimizer
            
        if hasattr(cv_module, 'cv_generator'):
            cv_module.cv_generator = cv_generator
            
        if hasattr(cl_module, 'cover_letter_generator'):
            cl_module.cover_letter_generator = cover_letter_generator
            
    except ImportError as e:
        print(f"Warning: Failed to import required modules: {e}")
    except Exception as e:
        print(f"Error initializing modules: {e}")
    
    # Return modules in case they're needed
    return modules

# Update module variables
modules = update_module_variables()

# Set up templates
templates_dir = Path(__file__).parent / "templates"
if not templates_dir.exists():
    templates_dir.mkdir()
templates = Jinja2Templates(directory=str(templates_dir))

# Load environment variables
from dotenv import load_dotenv
import os

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Validate required environment variables
required_vars = ["JWT_SECRET_KEY"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(
    title="PortfolioAI API",
    description="API for generating professional portfolios, CVs, and cover letters using AI.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# All routes are defined directly in this file

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic Models for Request Validation
class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None

class WorkExperience(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: Optional[str] = None
    current: bool = False
    description: List[str]
    location: Optional[str] = None

class Education(BaseModel):
    degree: str
    institution: str
    field_of_study: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    gpa: Optional[float] = None

class CVGenerationRequest(BaseModel):
    personal_info: PersonalInfo
    work_experience: List[WorkExperience]
    education: List[Education]
    skills: List[str]
    template: str = "modern"
    format: Literal["docx", "pdf", "md"] = "docx"
    
    @field_validator('template')
    @classmethod
    def validate_template(cls, v: str) -> str:
        valid_templates = ["modern", "professional", "creative", "simple"]
        v_lower = v.lower()
        if v_lower not in valid_templates:
            raise ValueError(f"Template must be one of: {', '.join(valid_templates)}")
        return v_lower

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in ['docx', 'pdf', 'markdown']:
            raise ValueError("Format must be one of: docx, pdf, markdown")
        return v_lower

class CoverLetterRequest(BaseModel):
    job_description: str
    resume_text: str
    tone: str = "professional"  # professional, friendly, formal, enthusiastic
    
    @validator('tone')
    def validate_tone(cls, v: str) -> str:
        valid_tones = ["professional", "friendly", "formal", "enthusiastic"]
        v_lower = v.lower()
        if v_lower not in valid_tones:
            raise ValueError(f"Tone must be one of: {', '.join(valid_tones)}")
        return v_lower

class NewCoverLetterRequest(BaseModel):
    """Request model for the new cover letter generator."""
    resume_id: str
    job_title: str
    company_name: str
    tone: str = "professional"
    length: str = "medium"
    
    @validator('tone')
    def validate_tone(cls, v: str) -> str:
        valid_tones = ["professional", "friendly", "concise"]
        v_lower = v.lower()
        if v_lower not in valid_tones:
            raise ValueError(f"Tone must be one of: {', '.join(valid_tones)}")
        return v_lower
    
    @validator('length')
    def validate_length(cls, v: str) -> str:
        valid_lengths = ["short", "medium", "long"]
        v_lower = v.lower()
        if v_lower not in valid_lengths:
            raise ValueError(f"Length must be one of: {', '.join(valid_lengths)}")
        return v_lower

class OptimizationRequest(BaseModel):
    resume_text: str
    job_description: str = ""  # Made optional with default empty string
    
    @model_validator(mode='after')
    def validate_text_lengths(self) -> 'OptimizationRequest':
        if len(self.resume_text.strip()) < 50:
            raise ValueError("resume_text must be at least 50 characters long")
        return self

# Authentication
def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    """Dependency to get the current authenticated user."""
    # In development, we'll skip API key validation
    # In production, you should validate the API key
    if os.getenv("ENV") == "production":
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key is required")
    
    # Get the test user from the database or create one if it doesn't exist
    test_user = db.query(User).filter(User.email == "test.user@example.com").first()
    if not test_user:
        from uuid import uuid4
        test_user = User(
            id=str(uuid4()),
            email="test.user@example.com",
            hashed_password="hashed_password_placeholder",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    # Ensure the user has a valid UUID
    if not test_user.id or not isinstance(test_user.id, str) or len(test_user.id) != 36:
        # If the ID is invalid, generate a new one
        from uuid import uuid4
        test_user.id = str(uuid4())
        db.commit()
    
    return {
        "id": test_user.id,  # This is now guaranteed to be a valid UUID string
        "email": test_user.email
    }

# Helper functions
def get_temp_file(ext: str = "") -> str:
    """Create a temporary file and return its path."""
    temp_dir = Path(tempfile.gettempdir()) / "portfolioai"
    temp_dir.mkdir(exist_ok=True)
    return str(temp_dir / f"{uuid.uuid4()}{ext}")

async def cleanup_file(file_path: str, delay: int = 0) -> None:
    """
    Asynchronously remove a file if it exists after an optional delay.
    This function is intended to be run as a FastAPI background task.

    Args:
        file_path: Path to the file to clean up.
        delay: Delay in seconds before cleaning up the file.
    """
    if not file_path:
        logger.warning("cleanup_file called with no file_path.")
        return

    logger.debug(f"Cleanup task started for {file_path} with delay {delay}s.")
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        path_exists = await asyncio.to_thread(os.path.exists, file_path)
        if path_exists:
            await asyncio.to_thread(os.remove, file_path)
            logger.info(f"Successfully cleaned up file: {file_path}")
        else:
            logger.info(f"File not found for cleanup (already removed or never existed): {file_path}")
    except Exception as e:
        logger.error(f"Error during file cleanup for {file_path}: {e}", exc_info=True)

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that provides API documentation."""
    return """
    <html>
        <head>
            <title>PortfolioAI Backend</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { color: #333; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-left: 4px solid #4CAF50; }
                .method { font-weight: bold; color: #4CAF50; }
                .path { font-family: monospace; }
                .description { margin: 5px 0 0 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>PortfolioAI Backend API</h1>
                <p>Welcome to the PortfolioAI Backend API. Below are the available endpoints:</p>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="path">/</span></div>
                    <div class="description">API documentation (this page)</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="path">/health</span></div>
                    <div class="description">Health check endpoint</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="path">/api/portfolio/generate</span></div>
                    <div class="description">Generate a portfolio from structured data</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="path">/api/portfolio/upload</span></div>
                    <div class="description">Generate a portfolio by uploading a resume</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="path">/api/portfolio/{portfolio_id}/download</span></div>
                    <div class="description">Download a generated portfolio</div>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="path">/api/portfolio/{portfolio_id}/preview</span></div>
                    <div class="description">Preview a generated portfolio in the browser</div>
                </div>
                
                <p>For detailed API documentation, visit <a href="/docs">/docs</a> or <a href="/redoc">/redoc</a></p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "PortfolioAI Backend is running"}

@app.get("/p/{subdomain}", response_class=HTMLResponse)
async def view_portfolio_by_subdomain(
    subdomain: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """View a portfolio by its subdomain."""
    # Find the portfolio with the given subdomain
    portfolio = db.query(Portfolio).filter(
        Portfolio.subdomain == subdomain,
        Portfolio.is_public == True
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not publicly accessible"
        )
    
    # If we have HTML content, render it
    if portfolio.content and 'html' in portfolio.content:
        return HTMLResponse(content=portfolio.content['html'])
    
    # Otherwise, redirect to the download or preview endpoint
    return RedirectResponse(url=f"/api/portfolios/{portfolio.id}/preview")

class SubdomainRequest(BaseModel):
    """Request model for setting a portfolio subdomain."""
    subdomain: str = Field(..., min_length=3, max_length=63, pattern=r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$')

@app.post("/api/portfolios/{portfolio_id}/subdomain", status_code=status.HTTP_200_OK)
async def set_portfolio_subdomain(
    portfolio_id: str,
    subdomain_request: SubdomainRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a custom subdomain for a portfolio."""
    # Get the portfolio
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user['id']
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Check if the subdomain is already taken
    existing = db.query(Portfolio).filter(
        Portfolio.subdomain == subdomain_request.subdomain,
        Portfolio.id != portfolio_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already in use"
        )
    
    # Update the portfolio with the new subdomain
    portfolio.subdomain = subdomain_request.subdomain
    db.commit()
    
    return {"status": "success", "subdomain": portfolio.subdomain}

class PortfolioTemplate(str, Enum):
    DEFAULT = "default"
    MODERN = "modern"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"

class PortfolioGenerationRequest(BaseModel):
    """Request model for generating a portfolio."""
    personal_info: PersonalInfo
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: List[str] = []
    projects: List[Dict[str, Any]] = []
    template: str = "default"
    subdomain: Optional[str] = Field(None, min_length=3, max_length=63, pattern=r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$')
    
    class Config:
        json_schema_extra = {
            "example": {
                "personal_info": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "linkedin": "linkedin.com/in/johndoe",
                    "github": "github.com/johndoe",
                    "summary": "Full Stack Developer with 5+ years of experience...",
                    "location": "San Francisco, CA"
                },
                "work_experience": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "start_date": "2020-01-01",
                        "end_date": "2023-12-31",
                        "current": False,
                        "description": ["Developed web applications", "Led a team of developers"],
                        "location": "San Francisco, CA"
                    }
                ],
                "education": [
                    {
                        "degree": "B.S. Computer Science",
                        "institution": "Stanford University",
                        "field_of_study": "Computer Science",
                        "start_date": "2016-01-01",
                        "end_date": "2020-01-01",
                        "gpa": 3.8
                    }
                ],
                "skills": ["Python", "JavaScript", "React", "Node.js"],
                "projects": [
                    {
                        "name": "Portfolio Website",
                        "description": "A personal portfolio website built with React and Node.js",
                        "technologies": ["React", "Node.js", "MongoDB"],
                        "url": "https://example.com/portfolio"
                    }
                ],
                "template": "modern"
            }
        }
@app.get("/api/portfolio/questions")
async def get_portfolio_questions():
    """
    Get the list of guided questions for portfolio creation.
    """
    try:
        questions = await portfolio_builder.get_guided_questions()
        return {"status": "success", "questions": questions}
    except Exception as e:
        logger.error(f"Error getting portfolio questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/generate/guided")
async def generate_portfolio_guided(
    answers: List[str],
    template: str = "default",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a portfolio website from guided Q&A answers and save to database.
    
    - **answers**: List of answers to the guided questions
    - **template**: Template to use (default, modern, professional, creative)
    """
    try:
        # Process answers and generate portfolio data
        # This is a simplified example - in a real app, you'd process these answers
        # to create structured data for the portfolio
        portfolio_data = {
            "personal_info": {
                "name": answers[0] if len(answers) > 0 else "Your Name",
                "title": answers[1] if len(answers) > 1 else "Professional Title",
                "email": answers[2] if len(answers) > 2 else "your.email@example.com",
                "bio": answers[3] if len(answers) > 3 else "A short bio about yourself."
            },
            "sections": [
                {"title": "About", "content": answers[4] if len(answers) > 4 else "About section content"},
                {"title": "Experience", "content": answers[5] if len(answers) > 5 else "Experience details"},
                {"title": "Skills", "content": answers[6] if len(answers) > 6 else "Your skills"},
                {"title": "Contact", "content": "Get in touch with me!"}
            ]
        }
        
        # Generate a unique ID for the portfolio
        portfolio_id = str(uuid.uuid4())
        
        # Create output directory
        output_dir = Path(tempfile.gettempdir()) / "portfolioai" / portfolio_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate the portfolio
        generator = PortfolioGenerator()
        output_file = generator.generate_portfolio(
            portfolio_data,
            template=template,
            output_dir=str(output_dir)
        )
        
        # Create a database record for the portfolio
        portfolio = Portfolio(
            id=portfolio_id,
            user_id=current_user["id"],
            title=f"Portfolio - {portfolio_data['personal_info'].get('name', 'Untitled')}",
            file_path=output_file,
            file_type="zip",
            content=portfolio_data,
            is_public=False,
            template=template
        )
        
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        
        # Log the API call
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint="/api/portfolio/generate/guided",
                method="POST",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        # Schedule cleanup of the generated files after 1 hour
        background_tasks.add_task(cleanup_file, str(output_dir), delay=3600)
        
        # Generate a simple subdomain for preview
        subdomain = f"{portfolio_id[:8]}"
        
        # Get the filename from the output path
        filename = os.path.basename(output_file)
        
        return {
            "status": "success",
            "message": "Portfolio generated and saved successfully",
            "portfolio_id": portfolio_id,
            "download_url": f"/api/portfolio/download/{portfolio_id}/{filename}",
            "preview_url": f"/api/portfolio/preview/{portfolio_id}/{filename}",
            "subdomain": subdomain
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating portfolio from Q&A: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/upload-resume", response_model=Dict[str, str])
async def upload_portfolio_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume file for portfolio generation.
    
    - **file**: The resume file to upload (PDF, DOCX, TXT)
    """
    try:
        logger.info(f"[PORTFOLIO_UPLOAD_RESUME] Received request. User ID: {current_user.get('id', 'unknown')}")
        
        # Get user_id from the current_user dictionary
        user_id = current_user.get('id', 'unknown')
        
        # Validate file type
        allowed_types = ["application/pdf", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                        "text/plain"]
        
        if file.content_type not in allowed_types:
            error_msg = f"File type {file.content_type} not supported. Please upload a PDF, DOCX, or TXT file."
            logger.error(f"[PORTFOLIO_UPLOAD_RESUME_VALIDATION_ERROR] {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Read file content
        file_content = await file.read()
        
        # Generate a unique ID for the resume
        resume_id = str(uuid.uuid4())
        
        # In a real implementation, you would process the resume here
        # For now, we'll just return the resume_id
        
        logger.info(f"[PORTFOLIO_UPLOAD_RESUME_SUCCESS] Successfully processed resume. Resume ID: {resume_id}")
        
        return {"resume_id": resume_id}
        
    except HTTPException as he:
        logger.error(f"[PORTFOLIO_UPLOAD_RESUME_HTTP_ERROR] Detail: {he.detail}, Status Code: {he.status_code}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"[PORTFOLIO_UPLOAD_RESUME_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

class ResumePortfolioRequest(BaseModel):
    resume_text: str
    sections: List[str]
    subdomain: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=63, 
        pattern=r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$',
        description="Custom subdomain for the portfolio (e.g., 'john-doe' for 'john-doe.portfolioai.com')"
    )

@app.get("/api/portfolio/check-subdomain")
async def check_subdomain_availability(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """
    Check if a subdomain is available for use.
    
    - **subdomain**: The subdomain to check (e.g., 'john-doe' for 'john-doe.portfolioai.com')
    """
    # Validate subdomain format
    import re
    if not re.match(r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$', subdomain):
        return {
            "available": False,
            "message": "Invalid subdomain format. Use 3-63 characters: lowercase letters, numbers, and hyphens only. Must start and end with a letter or number."
        }
    
    # Check if subdomain exists
    existing = db.query(Portfolio).filter(
        Portfolio.subdomain == subdomain
    ).first()
    
    if existing:
        return {
            "available": False,
            "message": f"Subdomain '{subdomain}' is already taken. Please choose a different one."
        }
    
    return {
        "available": True,
        "message": f"Subdomain '{subdomain}' is available!"
    }


@app.post("/api/portfolio/generate/from-resume")
async def generate_portfolio_from_resume(
    request: ResumePortfolioRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a portfolio website from resume text using PortfolioBuilder.
    """
    try:
        # Save resume text to a temporary file for processing
        import tempfile
        import os
        
        # Create a temporary file with the resume content
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            temp_file.write(request.resume_text)
            temp_path = temp_file.name
        
        try:
            # Initialize PortfolioBuilder with Groq client
            from .services.groq_client import groq_client
            from .services.portfolio_builder import PortfolioBuilder
            
            portfolio_builder = PortfolioBuilder(groq_client)
            
            # Generate portfolio using the builder
            output_file = await portfolio_builder.build_from_resume(
                resume_path=temp_path,
                template='default',
                use_ai_enhancement=True
            )
            
            # Read the generated content
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            # Create a database record for the portfolio
            portfolio_id = str(uuid.uuid4())
            
            # Create portfolio record
            portfolio = Portfolio(
                id=portfolio_id,
                user_id=current_user["id"],
                title=f"Portfolio - {portfolio_id[:8]}",  # Default title with first 8 chars of ID
                content={
                    'html': content,
                    'sections': request.sections,
                    'file_path': output_file,
                    'file_type': 'html'
                },
                is_public=True,  # Make portfolio publicly accessible
                subdomain=request.subdomain  # Set the subdomain if provided
            )
            
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            
            # Generate the public URL if subdomain is provided
            public_url = None
            if request.subdomain:
                public_url = f"http://{request.subdomain}.portfolioai.com"
            
            # Return the generated content with portfolio info
            return JSONResponse(content={
                'status': 'success',
                'content': content,
                'sections': request.sections,
                'portfolio_id': portfolio_id,
                'subdomain': request.subdomain,
                'public_url': public_url
            })
            
        except Exception as e:
            # Clean up the temporary file in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
        
    except Exception as e:
        logger.error(f"Error generating portfolio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/generate", response_model=dict)
async def generate_portfolio(
    request: PortfolioGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a portfolio website based on the provided information and save to database.
    """
    # Generate a unique ID for this portfolio
    portfolio_id = str(uuid.uuid4())
    
    # Check if subdomain is provided and available
    if request.subdomain:
        existing = db.query(Portfolio).filter(
            Portfolio.subdomain == request.subdomain
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already in use"
            )
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(tempfile.gettempdir()) / "portfolioai" / portfolio_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate the portfolio using the PortfolioBuilder
        builder = PortfolioBuilder()
        
        # Convert Pydantic model to dictionary and handle nested models
        portfolio_data = request.dict()
        
        # Convert nested Pydantic models to dictionaries
        if 'personal_info' in portfolio_data and hasattr(portfolio_data['personal_info'], 'dict'):
            portfolio_data['personal_info'] = portfolio_data['personal_info'].dict()
            
        if 'work_experience' in portfolio_data and portfolio_data['work_experience']:
            portfolio_data['work_experience'] = [exp.dict() if hasattr(exp, 'dict') else exp 
                                              for exp in portfolio_data['work_experience']]
                                              
        if 'education' in portfolio_data and portfolio_data['education']:
            portfolio_data['education'] = [edu.dict() if hasattr(edu, 'dict') else edu 
                                         for edu in portfolio_data['education']]
        
        # Generate the portfolio
        output_file = await builder._generate_portfolio(
            portfolio_data,
            template_name=request.template
        )
        
        # Get the filename from the output path
        filename = os.path.basename(output_file)
        
        # Create a database record for the portfolio
        portfolio = Portfolio(
            id=portfolio_id,
            user_id=current_user["id"],
            title=f"Portfolio - {request.personal_info.get('name', 'Untitled')}",
            file_path=output_file,
            file_type="zip",
            content=request.dict(),
            is_public=True,  # Make portfolio publicly accessible for subdomain
            subdomain=request.subdomain  # Set the subdomain if provided
        )
        
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        
        # Log the API call
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint="/api/portfolio/generate",
                method="POST",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        # Schedule cleanup of the generated files after 1 hour
        background_tasks.add_task(cleanup_file, str(output_dir), delay=3600)
        
        # Generate a preview URL
        preview_url = f"/api/portfolio/preview/{portfolio_id}/{filename}"
        
        return {
            "status": "success",
            "message": "Portfolio generated and saved successfully",
            "portfolio_id": portfolio_id,
            "download_url": f"/api/portfolio/download/{portfolio_id}/{filename}",
            "preview_url": preview_url
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/generate")
async def generate_portfolio(
    file: UploadFile = File(...),
    template: str = "default",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate a portfolio website from an uploaded resume.
    
    - **file**: Resume file (PDF, DOCX, TXT)
    - **template**: Template to use (default, modern, professional, creative)
    """
    temp_file = None
    try:
        # Validate template
        try:
            template_enum = PortfolioTemplate(template.lower())
            template = template_enum.value
        except ValueError:
            valid_templates = [t.value for t in PortfolioTemplate]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template. Must be one of: {', '.join(valid_templates)}"
            )
            
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.docx', '.doc', '.txt']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file."
            )
            
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename)[1].lower()
        temp_file = get_temp_file(file_ext)
        
        with open(temp_file, "wb") as f:
            f.write(await file.read())
        
        # Generate portfolio
        html_path = await portfolio_builder.build_from_resume(temp_file, template=template)
        
        # Generate a subdomain based on the filename
        subdomain = portfolio_builder.generate_subdomain(os.path.splitext(file.filename)[0])
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, temp_file)
        background_tasks.add_task(cleanup_file, html_path, delay=3600)  # Clean up after 1 hour
        
        # Return the result with a download URL
        filename = os.path.basename(html_path)
        return {
            "status": "success",
            "message": "Portfolio generated successfully",
            "download_url": f"/api/portfolio/download/{filename}",
            "subdomain": subdomain,
            "preview_url": f"/api/portfolio/preview/{filename}"
        }
        
    except Exception as e:
        logger.error(f"Error generating portfolio: {str(e)}")
        if temp_file and os.path.exists(temp_file):
            # Use background_tasks for cleanup if available, otherwise call directly
            if 'background_tasks' in locals():
                background_tasks.add_task(
                    cleanup_file,
                    file_path=temp_file,
                    delay=0,
                    background_tasks=background_tasks
                )
            else:
                # Fallback to direct cleanup if background_tasks is not available
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    logger.error(
                        f"Failed to clean up temp file {temp_file}: "
                        f"{str(cleanup_error)}"
                    )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cv/generate", response_model=Dict[str, Any])
async def generate_cv(
    request: CVGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a CV based on the provided data with timeout and proper cleanup.
    
    This endpoint accepts CV data and generates a CV in the specified format.
    The generated CV is returned as a base64-encoded string in the response.
    """
    output_file = None
    logger.info("Starting CV generation request")
    
    try:
        # Convert the request to a dictionary and add user_id
        cv_data = request.model_dump()
        cv_data['user_id'] = current_user['id']
        
        # Log the request details (without sensitive data)
        logger.info(f"Generating CV in {request.format} format for user {current_user['id']}")
        
        # Set a timeout for the entire CV generation process
        try:
            # Generate the CV file with a timeout
            logger.info("Starting CV generation with timeout")
            
            # Use asyncio.shield to prevent cancellation during cleanup
            output_file = await asyncio.wait_for(
                asyncio.shield(cv_generator.generate_cv(
                    cv_data=cv_data,
                    output_format=request.format
                )),
                timeout=180  # 3 minutes total timeout
            )
            logger.info(f"CV generation completed successfully. Output file: {output_file}")
            
            # Read the generated file
            try:
                with open(output_file, 'rb') as f:
                    file_content = f.read()
                
                # Determine content type based on format
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if request.format == 'pdf':
                    content_type = "application/pdf"
                elif request.format == 'md':
                    content_type = "text/markdown"
                
                # Generate a unique CV ID
                cv_id = str(uuid.uuid4())
                
                # Schedule cleanup of the temporary file
                background_tasks.add_task(cleanup_file, output_file, delay=3600)  # Clean up after 1 hour
                
                # Return the response with the CV ID and file info
                return {
                    "status": "success",
                    "cv_id": cv_id,
                    "content": base64.b64encode(file_content).decode('utf-8'),
                    "content_type": content_type,
                    "filename": f"cv_{cv_id}.{request.format}",
                    "format": request.format
                }
                
            except Exception as e:
                logger.error(f"Error reading generated CV file: {str(e)}", exc_info=True)
                # Ensure we clean up the file if it exists
                if output_file and os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up file {output_file}: {str(cleanup_error)}")
                raise RuntimeError("Failed to read generated CV file")
                
        except asyncio.TimeoutError:
            logger.error("CV generation timed out after 3 minutes")
            raise HTTPException(
                status_code=504,
                detail="CV generation timed out. Please try again with a smaller CV or different format."
            )
        except asyncio.CancelledError:
            logger.warning("CV generation was cancelled")
            raise HTTPException(
                status_code=500,
                detail="CV generation was cancelled"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error generating CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CV: {str(e)}"
        )
        
    finally:
        # Ensure cleanup of the temporary file in case of any errors
        if output_file and os.path.exists(output_file) and not os.path.getsize(output_file):
            try:
                os.remove(output_file)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up file {output_file}: {str(cleanup_error)}")
        # Schedule the final cleanup via background task if the file still exists and has content
        # (or if output_file was defined but generation failed before content was written)
        if output_file: # Ensure output_file is defined
            cleanup_delay = 600 # 10 minutes, same as original logic
            background_tasks.add_task(cleanup_file, output_file, delay=cleanup_delay)
            logger.info(f"Scheduled final cleanup for {output_file} in {cleanup_delay} seconds.")

@app.post("/api/cover-letter/upload-resume", response_model=Dict[str, str])
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume file for cover letter generation.
    
    - **file**: The resume file to upload (PDF, DOCX, TXT)
    """
    try:
        logger.info(f"[UPLOAD_RESUME_START] Received request. Current user type: {type(current_user)}, value: {current_user}")
        
        # Get user_id from the current_user dictionary
        user_id = current_user.get('id', 'unknown')
        logger.info(f"[UPLOAD_RESUME_USER_ID] Using user_id: {user_id} from current_user dict")
        
        if user_id == 'unknown':
            logger.warning("[UPLOAD_RESUME_WARNING] No user_id found in current_user")
            
        logger.info(f"[UPLOAD_RESUME_PROCESSING] Processing resume upload for user_id: {user_id}")
        
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
        if file.content_type not in allowed_types:
            error_msg = f"File type {file.content_type} not supported. Please upload a PDF, DOCX, or TXT file."
            logger.error(f"[UPLOAD_RESUME_VALIDATION_ERROR] {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        logger.info(f"[UPLOAD_RESUME_CALL_SERVICE] Calling cover_letter_generator.upload_resume for file: {file.filename}")
        
        # Ensure file pointer is at the start
        await file.seek(0)
        
        # Create a new UploadFile object to ensure it's in a clean state
        from fastapi import UploadFile
        from tempfile import SpooledTemporaryFile
        
        # Read the file content
        file_content = await file.read()
        
        # Create a new SpooledTemporaryFile
        temp_file = SpooledTemporaryFile()
        temp_file.write(file_content)
        temp_file.seek(0)
        
        # Create a new UploadFile with the same content
        new_file = UploadFile(
            filename=file.filename,
            file=temp_file,
            content_type=file.content_type
        )
        
        try:
            # Call the service with the new file object
            result = await cover_letter_generator.upload_resume(new_file)
            logger.info(f"[UPLOAD_RESUME_SERVICE_RESULT] Result from service: {result}")

            if not result or 'resume_id' not in result:
                error_msg = "Failed to process resume: No resume_id in response from service"
                logger.error(f"[UPLOAD_RESUME_SERVICE_ERROR] {error_msg}. Result: {result}")
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )
        finally:
            # Ensure the temporary file is closed
            await new_file.close()
            temp_file.close()
        
        resume_id_from_result = result['resume_id']
        logger.info(f"[UPLOAD_RESUME_SUCCESS] Successfully processed resume. Resume ID: {resume_id_from_result}, User ID: {user_id}")
        
        return {"resume_id": resume_id_from_result}
        
    except HTTPException as he:
        logger.error(f"[UPLOAD_RESUME_HTTP_ERROR] Detail: {he.detail}, Status Code: {he.status_code}", exc_info=True)
        raise
    except AttributeError as ae:
        logger.error(f"[UPLOAD_RESUME_ATTRIBUTE_ERROR] Error: {str(ae)}. Current user state: {current_user}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: Attribute error - {str(ae)}"
        )
    except Exception as e:
        logger.error(f"[UPLOAD_RESUME_GENERAL_ERROR] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# New simplified endpoint that doesn't store resumes
@app.post("/api/cover-letter/generate-direct")
async def generate_cover_letter_direct(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company_name: str = Form(...),
    tone: str = Form("professional"),
    length: str = Form("medium"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a cover letter directly from an uploaded resume without storing it.
    
    - **file**: The resume file (PDF, DOCX, TXT) - currently not used, hardcoded resume is used
    - **job_title**: The job title being applied for
    - **company_name**: The name of the company
    - **tone**: The desired tone (professional, friendly, concise)
    - **length**: The desired length (short, medium, long)
    """
    logger.info(f"[GENERATE_COVER_LETTER_DIRECT] Starting direct cover letter generation for {current_user.get('email')}")
    
    try:
        # Hardcoded resume text for testing
        resume_text = """
        JOHN DOE
        Senior Software Engineer
        
        SUMMARY
        Experienced software engineer with 5+ years of experience in full-stack development. 
        Proficient in Python, JavaScript, and cloud technologies.
        
        EXPERIENCE
        - Senior Software Engineer at Tech Corp (2020-Present)
          - Led a team of 5 developers
          - Developed microservices using Python and FastAPI
        - Software Developer at Web Solutions (2018-2020)
          - Built responsive web applications using React and Node.js
        
        EDUCATION
        B.S. in Computer Science, University of Technology (2018)
        """
        
        logger.info("[GENERATE_COVER_LETTER_DIRECT] Using hardcoded resume text")
        
        # Generate the cover letter using the legacy endpoint
        job_description = f"Job Title: {job_title}\nCompany: {company_name}"
        logger.info(f"[GENERATE_COVER_LETTER_DIRECT] Job description: {job_description}")
        
        request = CoverLetterRequest(
            job_description=job_description,
            resume_text=resume_text,
            tone=tone
        )
        
        logger.info("[GENERATE_COVER_LETTER_DIRECT] Calling legacy_generate_cover_letter")
        result = await legacy_generate_cover_letter(request, current_user, next(get_db()))
        
        if not result or "cover_letter" not in result:
            logger.error("[GENERATE_COVER_LETTER_DIRECT] No cover letter was generated")
            raise HTTPException(status_code=500, detail="Failed to generate cover letter")
        
        logger.info("[GENERATE_COVER_LETTER_DIRECT] Successfully generated cover letter")
        return {"cover_letter": result.get("cover_letter")}
                
    except HTTPException as he:
        logger.error(f"[GENERATE_COVER_LETTER_DIRECT] HTTPException: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"[GENERATE_COVER_LETTER_DIRECT] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")

@app.post("/api/cover-letter/generate", response_model=Dict[str, str])
async def generate_cover_letter(
    request: NewCoverLetterRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a cover letter based on the provided information.
    
    - **resume_id**: ID of the resume to use
    - **job_title**: The job title being applied for
    - **company_name**: The name of the company
    - **tone**: The desired tone (professional, friendly, concise)
    - **length**: The desired length (short, medium, long)
    """
    try:
        # Get user_id from the current_user dictionary
        user_id = current_user.get('id')
        if not user_id:
            logger.error("No user_id found in current_user")
            raise HTTPException(status_code=400, detail="User ID not found in authentication token")
            
        # Log the API call
        api_call = APICall(
            user_id=user_id,
            endpoint="/api/cover-letter/generate",
            method="POST",
            status="pending"
        )
        db.add(api_call)
        db.commit()
        
        # Convert the request to a dictionary for the service
        request_dict = request.dict()
        
        # Generate the cover letter using the service
        result = await cover_letter_generator.generate_cover_letter(request_dict)
        
        # Save the generated cover letter to the database
        cover_letter = CoverLetter(
            user_id=current_user.id,
            job_title=request.job_title,
            company_name=request.company_name,
            content=result["cover_letter_text"],
            status="completed"
        )
        db.add(cover_letter)
        db.commit()
        
        # Update API call status
        api_call.status = "completed"
        db.commit()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        error_msg = f"Error generating cover letter: {str(e)}"
        logger.error(error_msg)
        
        # Update API call status
        if 'api_call' in locals():
            api_call.status = f"error: {str(e)[:200]}"  # Truncate error message
            db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.post("/api/cover-letter/save", response_model=Dict[str, str])
async def save_cover_letter(
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a generated cover letter.
    
    - **resume_id**: ID of the resume used
    - **job_title**: The job title
    - **company_name**: The company name
    - **content**: The cover letter content
    """
    try:
        # Get user_id from the current_user dictionary
        user_id = current_user.get('id')
        if not user_id:
            logger.error("No user_id found in current_user")
            raise HTTPException(status_code=400, detail="User ID not found in authentication token")
            
        # Log the API call
        api_call = APICall(
            user_id=user_id,
            endpoint="/api/cover-letter/save",
            method="POST",
            status="pending"
        )
        db.add(api_call)
        db.commit()
        
        # Save the cover letter using the service
        result = await cover_letter_generator.save_cover_letter(data)
        
        # Log the successful save
        logger.info(f"Successfully saved cover letter for user {user_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving cover letter: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save cover letter: {str(e)}"
        )

# Legacy endpoint - kept for backward compatibility
@app.post("/api/cover-letter/legacy-generate", response_model=Dict[str, str])
async def legacy_generate_cover_letter(
    request: CoverLetterRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Legacy endpoint for generating a cover letter based on job description and resume text.
    
    - **job_description**: The job description to target
    - **resume_text**: The applicant's resume content
    - **tone**: The desired tone (professional, enthusiastic, formal, etc.)
    """
    try:
        # Get user_id from the current_user dictionary
        user_id = current_user.get('id')
        if not user_id:
            logger.error("No user_id found in current_user")
            raise HTTPException(status_code=400, detail="User ID not found in authentication token")
            
        # Log the API call
        api_call = APICall(
            user_id=user_id,
            endpoint="/api/cover-letter/legacy-generate",
            method="POST",
            status_code=200  # Default to 200, will be updated if there's an error
        )
        db.add(api_call)
        db.commit()
        
        # Generate the cover letter using GroqClient
        try:
            # Use the generate_cover_letter method from GroqClient
            cover_letter_text = await groq_client.generate_cover_letter(
                resume_text=request.resume_text,
                job_description=request.job_description,
                tone=request.tone
            )
            
            # Save the generated cover letter to the database
            cover_letter = CoverLetter(
                user_id=user_id,
                title=f"Cover Letter for {request.job_description[:50]}..." if request.job_description else "Generated Cover Letter",
                content={
                    "text": cover_letter_text,
                    "job_description": request.job_description,
                    "tone": request.tone,
                    "status": "completed"
                }
            )
            db.add(cover_letter)
            db.commit()
            
            # Update API call status_code to 200 for success
            api_call.status_code = 200
            db.commit()
            
            return {"cover_letter": cover_letter_text}
            
        except Exception as e:
            # Log the error
            error_msg = str(e)[:200]  # Truncate error message
            logger.error(f"Error generating cover letter: {error_msg}")
            api_call.status_code = 500  # Set status code to 500 for server error
            db.commit()
            
            # Return a fallback response
            return {
                "cover_letter": f"Failed to generate cover letter: {str(e)}. " \
                              "Please try again later or contact support if the issue persists."
            }
            
    except Exception as e:
        # Log any other unexpected errors
        logger.error(f"Unexpected error in legacy_generate_cover_letter: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cv/download/{cv_id}")
async def download_cv(
    cv_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a generated CV file.
    
    - **cv_id**: The ID of the CV to download
    """
    try:
        # Get CV from database
        cv = db.query(CV).filter(
            CV.id == cv_id,
            (CV.user_id == current_user["id"]) | (CV.is_public == True)
        ).first()
        
        if not cv:
            raise HTTPException(status_code=404, detail="CV not found or access denied")
        
        if not cv.file_path or not os.path.exists(cv.file_path):
            raise HTTPException(status_code=404, detail="CV file not found on server")
        
        # Determine content type based on file extension
        if cv.file_type == 'docx':
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif cv.file_type == 'pdf':
            media_type = "application/pdf"
        else:  # Default to markdown
            media_type = "text/markdown"
        
        # Log the download
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint=f"/api/cv/download/{cv_id}",
                method="GET",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        # Schedule cleanup of the file after 60 seconds
        background_tasks.add_task(
            cleanup_file,
            file_path=cv.file_path,
            delay=60,
            background_tasks=background_tasks
        )
        
        # Return the file as a response
        return FileResponse(
            path=cv.file_path,
            filename=f"cv_{cv.id}.{cv.file_type}",
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading CV")

@app.get("/api/portfolio/download/{portfolio_id}/{filename}")
async def download_portfolio(
    portfolio_id: str,
    filename: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a generated portfolio.
    
    - **portfolio_id**: ID of the portfolio to download
    - **filename**: Name of the file to download (for backward compatibility)
    """
    try:
        # Get the portfolio from the database
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            (Portfolio.user_id == current_user["id"]) | (Portfolio.is_public == True)
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found or access denied")
        
        if not portfolio.file_path or not os.path.exists(portfolio.file_path):
            raise HTTPException(status_code=404, detail="Portfolio file not found on server")
        
        # Log the download
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint=f"/api/portfolio/download/{portfolio_id}",
                method="GET",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        # Schedule cleanup of the file after 60 seconds
        background_tasks.add_task(
            cleanup_file,
            file_path=portfolio.file_path,
            delay=60,
            background_tasks=background_tasks
        )
        
        return FileResponse(
            path=portfolio.file_path,
            filename=f"portfolio_{portfolio.id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/preview/{portfolio_id}/{filename}", response_class=HTMLResponse)
async def preview_portfolio(
    request: Request,
    portfolio_id: str,
    filename: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview a generated portfolio in the browser.
    
    - **portfolio_id**: ID of the portfolio to preview
    - **filename**: Name of the file to preview (for backward compatibility)
    """
    try:
        # Get the portfolio from the database
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            (Portfolio.user_id == current_user["id"]) | (Portfolio.is_public == True)
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found or access denied")
        
        if not portfolio.file_path or not os.path.exists(portfolio.file_path):
            raise HTTPException(status_code=404, detail="Portfolio file not found on server")
        
        # For now, we'll just return the file if it's HTML
        # In a real implementation, you might want to extract the HTML from the zip
        if not portfolio.file_path.endswith('.html'):
            return {"detail": "Preview is only available for HTML portfolios"}
        
        # Schedule cleanup of the file after 60 seconds
        background_tasks.add_task(
            cleanup_file,
            file_path=portfolio.file_path,
            delay=60,
            background_tasks=background_tasks
        )
        
        # Read the HTML content
        with open(portfolio.file_path, 'r') as f:
            html_content = f.read()
        
        # Log the preview
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint=f"/api/portfolio/preview/{portfolio_id}",
                method="GET",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        return HTMLResponse(content=html_content, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/export/{portfolio_id}")
async def export_portfolio(
    portfolio_id: str,
    format: str = "html",  # Supported formats: html, pdf, zip
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export a portfolio in the specified format.
    
    - **portfolio_id**: ID of the portfolio to export
    - **format**: Export format (html, pdf, zip)
    """
    try:
        # Validate format
        format = format.lower()
        if format not in ["html", "pdf", "zip"]:
            raise HTTPException(status_code=400, detail="Invalid format. Supported formats: html, pdf, zip")
            
        # Get the portfolio from the database
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            (Portfolio.user_id == current_user["id"]) | (Portfolio.is_public == True)
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found or access denied")
        
        if not portfolio.file_path or not os.path.exists(portfolio.file_path):
            raise HTTPException(status_code=404, detail="Portfolio file not found on server")
        
        # Log the export
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint=f"/api/portfolio/export/{portfolio_id}?format={format}",
                method="GET",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path / f"portfolio_{portfolio_id}.{format}"
            
            try:
                if format == "pdf":
                    # Convert to PDF using WeasyPrint
                    if portfolio.file_path.endswith(('.html', '.htm')):
                        # Direct HTML to PDF conversion
                        pdf_bytes = self._convert_html_to_pdf(portfolio.file_path)
                        with open(output_path, 'wb') as f:
                            f.write(pdf_bytes)
                    else:
                        # For other formats, convert to HTML first
                        html_path = self._convert_to_html(portfolio.file_path, temp_dir_path, portfolio_id)
                        pdf_bytes = self._convert_html_to_pdf(html_path)
                        with open(output_path, 'wb') as f:
                            f.write(pdf_bytes)
                    
                    # Schedule cleanup of the temporary file
                    background_tasks.add_task(
                        cleanup_file,
                        file_path=str(output_path),
                        delay=60,
                        background_tasks=background_tasks
                    )
                    
                    return FileResponse(
                        path=output_path,
                        filename=f"portfolio_{portfolio_id}.pdf",
                        media_type="application/pdf"
                    )
                    
                elif format == "zip":
                    if portfolio.file_path.endswith('.zip'):
                        # If it's already a zip, return it directly
                        return FileResponse(
                            path=portfolio.file_path,
                            filename=f"portfolio_{portfolio_id}.zip",
                            media_type="application/zip"
                        )
                    else:
                        # Create a zip of the directory
                        import shutil
                        zip_path = temp_dir_path / f"portfolio_{portfolio_id}.zip"
                        
                        if os.path.isdir(portfolio.file_path):
                            # If it's a directory, zip the entire directory
                            shutil.make_archive(
                                str(zip_path.with_suffix('')),
                                'zip',
                                portfolio.file_path
                            )
                        else:
                            # If it's a single file, create a zip with that file
                            with zipfile.ZipFile(zip_path, 'w') as zipf:
                                zipf.write(
                                    portfolio.file_path,
                                    arcname=os.path.basename(portfolio.file_path)
                                )
                        
                        # Schedule cleanup of the temporary file
                        background_tasks.add_task(
                            cleanup_file,
                            file_path=str(zip_path),
                            delay=60,
                            background_tasks=background_tasks
                        )
                        
                        return FileResponse(
                            path=zip_path,
                            filename=f"portfolio_{portfolio_id}.zip",
                            media_type="application/zip"
                        )
                
                else:  # Default to HTML
                    if portfolio.file_path.endswith(('.html', '.htm')):
                        # If it's already HTML, return it directly
                        return FileResponse(
                            path=portfolio.file_path,
                            filename=f"portfolio_{portfolio_id}.html",
                            media_type="text/html"
                        )
                    else:
                        # Convert to HTML
                        html_path = self._convert_to_html(portfolio.file_path, temp_dir_path, portfolio_id)
                        
                        # Schedule cleanup of the temporary file
                        background_tasks.add_task(
                            cleanup_file,
                            file_path=str(html_path),
                            delay=60,
                            background_tasks=background_tasks
                        )
                        
                        return FileResponse(
                            path=html_path,
                            filename=f"portfolio_{portfolio_id}.html",
                            media_type="text/html"
                        )
                        
            except Exception as e:
                logger.error(f"Error during {format} conversion: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to convert portfolio to {format.upper()}: {str(e)}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting portfolio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export portfolio: {str(e)}")

def _convert_html_to_pdf(self, html_path: str) -> bytes:
    """
    Convert an HTML file to PDF using WeasyPrint.
    
    Args:
        html_path: Path to the HTML file
        
    Returns:
        PDF content as bytes
    """
    try:
        from weasyprint import HTML
        
        # Convert HTML to PDF
        pdf_bytes = HTML(html_path).write_pdf()
        return pdf_bytes
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF generation requires WeasyPrint. Install with: pip install weasyprint"
        )
    except Exception as e:
        logger.error(f"Error converting HTML to PDF: {str(e)}")
        raise

def _convert_to_html(self, file_path: str, output_dir: Path, portfolio_id: str) -> Path:
    """
    Convert various file formats to HTML.
    
    Args:
        file_path: Path to the source file
        output_dir: Directory to save the HTML output
        portfolio_id: ID of the portfolio for naming
        
    Returns:
        Path to the generated HTML file
    """
    try:
        output_path = output_dir / f"portfolio_{portfolio_id}.html"
        
        if file_path.endswith(('.docx', '.doc')):
            # Convert DOCX to HTML using python-docx
            import docx2txt
            text = docx2txt.process(file_path)
            
            # Create a simple HTML wrapper
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Portfolio Export</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    .section {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="content">
                    {content}
                </div>
            </body>
            </html>
            """.replace("{content}", text.replace("\n", "<br>"))
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        else:
            # For other formats, create a simple HTML file with the content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Portfolio Export</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        max-width: 800px; 
                        margin: 0 auto; 
                        padding: 20px;
                        white-space: pre-wrap;
                    }}
                </style>
            </head>
            <body>
                <pre>{content}</pre>
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting to HTML: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert file to HTML: {str(e)}"
        )

@app.get("/api/cover-letter/download/{cover_letter_id}")
async def download_cover_letter(
    cover_letter_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a generated cover letter.
    
    - **cover_letter_id**: ID of the cover letter to download
    """
    try:
        # Get the cover letter from the database
        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.id == cover_letter_id,
            (CoverLetter.user_id == current_user["id"]) | (CoverLetter.is_public == True)
        ).first()
        
        if not cover_letter:
            raise HTTPException(status_code=404, detail="Cover letter not found or access denied")
        
        if not cover_letter.file_path or not os.path.exists(cover_letter.file_path):
            # If file doesn't exist, create it from the content
            try:
                with open(cover_letter.file_path, 'w') as f:
                    f.write(cover_letter.content.get('content', ''))
            except Exception as e:
                logger.error(f"Failed to recreate cover letter file: {str(e)}")
                raise HTTPException(status_code=404, detail="Cover letter file not found and could not be recreated")
        
        # Log the download
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint=f"/api/cover-letter/download/{cover_letter_id}",
                method="GET",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        return FileResponse(
            path=cover_letter.file_path,
            filename=f"cover_letter_{cover_letter_id}.{cover_letter.file_type}",
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading cover letter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize/resume")
async def optimize_resume(
    request: OptimizationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize a resume based on a job description using AI.
    
    - **resume_text**: The current resume text to optimize
    - **job_description**: The job description to optimize for
    """
    logger = logging.getLogger(__name__)
    logger.info("=== RESUME OPTIMIZATION REQUEST RECEIVED ===")
    logger.info(f"User ID: {current_user.get('id', 'anonymous')}")
    logger.debug(f"Request headers: {dict(request.headers) if hasattr(request, 'headers') else 'N/A'}")
    
    try:
        # Log request details (safely)
        logger.info(f"Resume text length: {len(request.resume_text)} characters")
        logger.info(f"Job description provided: {'Yes' if request.job_description else 'No'}")
        
        # Log sample of resume text
        sample_text = request.resume_text[:200].replace('\n', ' ').replace('\r', '')
        logger.debug(f"Resume sample: {sample_text}...")
        
        # Validate input lengths
        logger.info("Validating input lengths...")
        request.validate_text_lengths()
        
        # Call the resume optimizer service
        logger.info("Calling resume optimizer service...")
        optimization_result = await resume_optimizer.optimize_resume(
            resume_text=request.resume_text,
            job_description=request.job_description
        )
        
        logger.info(f"Optimization completed. Score: {optimization_result.get('score', 'N/A')}")
        logger.debug(f"Optimization result keys: {list(optimization_result.keys())}")
        
        # Create a database record for the optimization
        optimization_id = str(uuid.uuid4())
        optimization = ResumeOptimization(
            id=optimization_id,
            user_id=current_user["id"],
            original_text=request.resume_text,
            optimized_text=optimization_result.get("optimized_text", request.resume_text),
            job_description=request.job_description,
            score=optimization_result.get("score", 0.0),
            suggestions=optimization_result.get("suggestions", []),
            keywords_matched=optimization_result.get("keywords_matched", []),
            missing_keywords=optimization_result.get("missing_keywords", [])
        )
        
        db.add(optimization)
        db.commit()
        db.refresh(optimization)
        
        # Log the API call
        try:
            api_call = APICall(
                user_id=current_user["id"],
                endpoint="/api/optimize/resume",
                method="POST",
                status_code=200
            )
            db.add(api_call)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {str(e)}")
            db.rollback()
        
        # Return the optimization results
        return {
            "status": "success",
            "message": "Resume optimized successfully",
            "optimization_id": optimization_id,
            "optimized_text": optimization_result.get("optimized_text", request.resume_text),
            "score": optimization_result.get("score", 0.0),
            "suggestions": optimization_result.get("suggestions", []),
            "keywords_matched": optimization_result.get("keywords_matched", []),
            "missing_keywords": optimization_result.get("missing_keywords", [])
        }
        
    except ValidationError as ve:
        error_msg = f"Validation error in resume optimization: {str(ve)}"
        logger.warning(error_msg, exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "message": "Validation error",
            "detail": str(ve),
            "error_type": "ValidationError"
        }
    except Exception as e:
        error_msg = f"Error optimizing resume: {str(e)}"
        logger.error(error_msg, exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "message": "An unexpected error occurred during resume optimization",
            "detail": str(e),
            "error_type": type(e).__name__
        }

if __name__ == "__main__":
    import uvicorn
    
    # Disable reload in production or when not needed
    # Set RELOAD environment variable to 'true' to enable hot reload
    reload_enabled = os.getenv('RELOAD', 'false').lower() == 'true'
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,  # Only enable reload if explicitly requested
        reload_dirs=["backend"] if reload_enabled else None,  # Only watch backend directory
        reload_excludes=['*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.obj', '*.o', '*.a', '*.lib', '*.dylib', '*.so.*', '*.dll.*', '*.obj.*', '*.o.*', '*.a.*', '*.lib.*', '*.dylib.*'],
        reload_includes=['*.py'],
        reload_delay=2.0  # Add a small delay to prevent rapid reloading
    )
