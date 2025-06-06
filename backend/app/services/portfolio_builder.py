"""
Portfolio Builder Service for PortfolioAI
"""
import os
import re
import json
import logging
import uuid
import textwrap
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from ..utils.file_utils import get_temp_file, cleanup_file, is_file_supported
from .groq_client import GroqClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default template for portfolio
DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        h1 { color: #333; }
        h2 { color: #444; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        .experience { margin-bottom: 20px; }
        .skills { display: flex; flex-wrap: wrap; gap: 10px; }
        .skill-tag { background: #f0f0f0; padding: 5px 10px; border-radius: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{name}}</h1>
        <p>{{title}}</p>
        <p>{{email}} | {{phone}} | {{location}}</p>
    </div>

    <div class="section">
        <h2>About</h2>
        <p>{{summary}}</p>
    </div>

    <div class="section">
        <h2>Experience</h2>
        {% for exp in experience %}
        <div class="experience">
            <h3>{{exp.title}} at {{exp.company}}</h3>
            <p><em>{{exp.start_date}} - {{exp.end_date or 'Present'}}</em></p>
            <ul>
                {% for item in exp.description %}
                <li>{{item}}</li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Education</h2>
        {% for edu in education %}
        <div class="education">
            <h3>{{edu.degree}} in {{edu.field_of_study or 'N/A'}}</h3>
            <p>{{edu.institution}} | {{edu.start_date}} - {{edu.end_date or 'Present'}}</p>
            {% if edu.gpa %}<p>GPA: {{edu.gpa}}</p>{% endif %}
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Skills</h2>
        <div class="skills">
            {% for skill in skills %}
            <span class="skill-tag">{{skill}}</span>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

class PortfolioBuilder:
    """Service for building portfolio websites with AI-powered enhancements."""
    
    def __init__(self, groq_client: GroqClient):
        """Initialize the portfolio builder with a Groq client."""
        self.groq_client = groq_client
        
        # Set up Jinja2 environment with default template
        self.templates_dir = Path(__file__).parent.parent / "templates"
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True)
        
        # Create default template if it doesn't exist
        default_template_path = self.templates_dir / "default.html"
        if not default_template_path.exists():
            with open(default_template_path, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_TEMPLATE)
        
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        # AI configuration
        self.ai_system_prompt = """You are a professional portfolio assistant that helps create compelling 
        and professional portfolio content. Your responses should be clear, concise, and tailored to highlight 
        the individual's strengths and experiences effectively."""
        
        # Initialize guided questions
        self.guided_questions = [
            "What is your full name?",
            "What is your professional title/headline?",
            "Please provide a brief professional summary (2-3 sentences):",
            "What is your email address?",
            "What is your phone number?",
            "What is your location (City, Country)?",
            "List your top 5-10 skills (comma-separated):",
            "Tell me about your work experience (company, title, dates, responsibilities - one per line, empty line to finish):"
        ]
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from different file types."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = '\n'.join([page.extract_text() for page in reader.pages])
                    return text
            except ImportError:
                logger.warning("PyPDF2 not installed, using fallback text extraction")
        
        # Fallback to simple text extraction
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    async def enhance_content(self, section: str, resume_data: Dict[str, Any], existing_content: str = "") -> Dict[str, Any]:
        """
        Enhance portfolio section content using AI.
        
        Args:
            section: The section being enhanced (e.g., 'about', 'experience')
            resume_data: The parsed resume data
            existing_content: Any existing content to refine
            
        Returns:
            Dict containing enhanced content and status
        """
        try:
            # Create a prompt based on the section type
            prompt = self._create_enhancement_prompt(section, resume_data, existing_content)
            
            # Call the AI model
            messages = [
                {"role": "system", "content": self.ai_system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.groq_client._make_request(messages)
            
            if not response or 'content' not in response:
                return {"status": "error", "message": "Failed to generate enhanced content"}
                
            return {
                "status": "success",
                "content": response['content'],
                "section": section
            }
            
        except Exception as e:
            logger.error(f"Error enhancing {section} content: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    async def suggest_sections(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest relevant sections for a portfolio based on resume data.
        
        Args:
            resume_data: The parsed resume data
            
        Returns:
            Dict containing suggested sections and status
        """
        try:
            prompt = f"""Based on the following resume data, suggest 3-5 relevant portfolio sections 
            that would best showcase this person's experience and skills. Focus on sections that highlight 
            their unique strengths and career trajectory.
            
            Resume Data:
            {json.dumps(resume_data, indent=2, default=str)}
            
            Return the sections as a JSON array of strings, like: ["section1", "section2", ...]"""
            
            messages = [
                {"role": "system", "content": self.ai_system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.groq_client._make_request(messages)
            
            if not response or 'content' not in response:
                return {"status": "error", "message": "Failed to generate section suggestions"}
                
            # Try to parse the response as JSON
            try:
                sections = json.loads(response['content'].strip())
                if not isinstance(sections, list):
                    raise ValueError("Expected a list of sections")
                    
                return {
                    "status": "success",
                    "suggested_sections": sections
                }
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse section suggestions: {str(e)}")
                return {"status": "error", "message": "Failed to parse section suggestions"}
                
        except Exception as e:
            logger.error(f"Error generating section suggestions: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    def _create_enhancement_prompt(self, section: str, resume_data: Dict[str, Any], existing_content: str = "") -> str:
        """Create a prompt for enhancing a specific portfolio section."""
        section_prompts = {
            "about": """Write a compelling 'About Me' section that highlights the person's professional 
            background, key skills, and career objectives. Focus on what makes them unique and valuable. 
            Keep it concise (3-4 paragraphs).""",
            
            "experience": """Enhance the work experience section with detailed, accomplishment-oriented 
            bullet points. For each role, include 3-5 bullet points that start with strong action verbs 
            and quantify achievements where possible.""",
            
            "skills": """Organize skills into relevant categories (e.g., Technical Skills, Languages, 
            Tools, etc.). Include proficiency levels where appropriate and highlight any certifications.""",
            
            "projects": """Describe 3-5 key projects that showcase the person's skills and experience. 
            For each project, include the project name, technologies used, and key contributions. 
            Focus on the impact and results achieved.""",
            
            "education": """Present the education background in a clear, professional format. 
            Include any relevant coursework, honors, or extracurricular activities if they strengthen 
            the candidate's profile."""
        }
        
        base_prompt = section_prompts.get(section.lower(), 
            f"Write a compelling {section} section for this portfolio.")
        
        prompt = f"""{base_prompt}
        
        Resume Data:
        {json.dumps(resume_data, indent=2, default=str)}"""
        
        if existing_content.strip():
            prompt += f"\n\nExisting Content (refine and improve this):\n{existing_content}"
            
        prompt += "\n\nPlease provide the enhanced content in markdown format."
        
        return prompt
    
    async def build_from_resume(self, resume_path: str, template: str = 'default', 
                              use_ai_enhancement: bool = True) -> str:
        """
        Build a portfolio website from a resume file.
        
        Args:
            resume_path: Path to the resume file
            template: Template name to use (default: 'default')
            
        Returns:
            str: Path to the generated HTML file
        """
        try:
            # Extract text from resume
            resume_text = await self._extract_text_from_file(resume_path)
            
            # Use Groq to extract structured data from resume
            prompt = f"""Extract the following information from the resume in JSON format:
            {{
                "name": "Full name",
                "title": "Professional title/headline",
                "summary": "Professional summary",
                "email": "Email address",
                "phone": "Phone number",
                "location": "Location (City, Country)",
                "experience": [
                    {{
                        "title": "Job title",
                        "company": "Company name",
                        "start_date": "Start date (YYYY-MM)",
                        "end_date": "End date (YYYY-MM or empty if current)",
                        "description": ["Responsibility 1", "Responsibility 2", ...]
                    }}
                ],
                "education": [
                    {{
                        "degree": "Degree name",
                        "institution": "Institution name",
                        "field_of_study": "Field of study (optional)",
                        "start_date": "Start date (YYYY)",
                        "end_date": "End date (YYYY or empty if current)",
                        "gpa": "GPA (if available)"
                    }}
                ],
                "skills": ["Skill 1", "Skill 2", ...]
            }}
            
            Resume content:
            {resume_text}
            """
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from resumes."},
                {"role": "user", "content": prompt}
            ]
            
            # Get structured data from Groq
            response = await self.groq_client._make_request(messages)
            
            # Parse the response (assuming it's in JSON format)
            try:
                # Extract JSON from markdown code block if present
                json_str = response.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].split('```')[0].strip()
                
                data = json.loads(json_str)
                
                # Generate portfolio using template
                return await self._generate_portfolio(data, template)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Groq response: {e}")
                logger.debug(f"Response content: {response}")
                raise ValueError("Failed to process resume. Please try again or use the guided Q&A option.")
            
        except Exception as e:
            logger.error(f"Error building portfolio from resume: {str(e)}")
            raise
    
    async def get_guided_questions(self) -> List[str]:
        """
        Get the list of guided questions for portfolio creation.
        
        Returns:
            List[str]: List of questions
        """
        return self.guided_questions
    
    async def process_guided_answers(self, answers: List[str], template: str = 'default') -> str:
        """
        Process answers from the guided Q&A flow and generate a portfolio.
        
        Args:
            answers: List of answers corresponding to guided_questions
            template: Template name to use (default: 'default')
            
        Returns:
            str: Path to the generated HTML file
        """
        try:
            if len(answers) != len(self.guided_questions):
                raise ValueError("Number of answers doesn't match number of questions")
            
            # Parse answers
            data = {
                "name": answers[0].strip(),
                "title": answers[1].strip(),
                "summary": answers[2].strip(),
                "email": answers[3].strip(),
                "phone": answers[4].strip(),
                "location": answers[5].strip(),
                "skills": [s.strip() for s in answers[6].split(',') if s.strip()],
                "experience": [],
                "education": []
            }
            
            # Parse work experience (if provided)
            if len(answers) > 7 and answers[7].strip():
                experience_entries = answers[7].split('\n\n')
                for entry in experience_entries:
                    lines = [line.strip() for line in entry.split('\n') if line.strip()]
                    if len(lines) >= 3:
                        # Simple parsing of company, title, dates, and bullet points
                        title_company = lines[0].split(' at ')
                        if len(title_company) == 2:
                            title, company = title_company
                        else:
                            title, company = lines[0], ""
                        
                        # Extract dates (simple pattern matching)
                        date_range = lines[1]
                        dates = re.findall(r'(\d{4}-\d{2}|\w+ \d{4})', date_range)
                        start_date = dates[0] if dates else ""
                        end_date = dates[1] if len(dates) > 1 else "Present"
                        
                        data["experience"].append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "start_date": start_date,
                            "end_date": end_date,
                            "description": lines[2:]
                        })
            
            return await self._generate_portfolio(data, template)
            
        except Exception as e:
            logger.error(f"Error building portfolio from resume: {str(e)}")
            raise

    async def get_guided_questions(self) -> List[str]:
        """
        Get the list of guided questions for portfolio creation.
        
        Returns:
            List[str]: List of guided questions
        """
        return self.guided_questions
    
    def generate_subdomain(self, name: str) -> str:
        """
        Generate a URL-friendly subdomain from a name.
        
        Args:
            name: Full name to generate subdomain from
            
        Returns:
            str: Generated subdomain
        """
        # Convert to lowercase and replace spaces with hyphens
        subdomain = name.lower().replace(' ', '-')
        # Remove special characters
        subdomain = re.sub(r'[^a-z0-9-]', '', subdomain)
        # Add a random string to ensure uniqueness
        random_str = str(uuid.uuid4())[:8]
        return f"{subdomain}-{random_str}"
    
    async def export_portfolio(self, html_path: str, output_dir: str = None) -> str:
        """
        Export the portfolio to a specified directory.
        
        Args:
            html_path: Path to the HTML file
            output_dir: Directory to export to (default: same as input)
            
        Returns:
            str: Path to the exported file
        """
        try:
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, os.path.basename(html_path))
                # Copy the file
                import shutil
                shutil.copy2(html_path, output_path)
                return output_path
            return html_path
        except Exception as e:
            logger.error(f"Error exporting portfolio: {str(e)}")
            raise
    
    async def build_from_qa(self, qa_data: Dict[str, str], template: str = 'default') -> str:
        """
        Build a portfolio website from Q&A data (legacy method).
        
        Args:
            qa_data: Dictionary of question-answer pairs
            template: Template name to use (default: 'default')
            
        Returns:
            str: Path to the generated HTML file
        """
        try:
            # Format Q&A data for the prompt
            qa_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_data.items()])
            
            # Convert Q&A data to structured format
            portfolio_data = self._convert_qa_to_portfolio_data(qa_data)
            
            # Generate portfolio using the structured data
            return await self._generate_portfolio(portfolio_data, template)
            
        except Exception as e:
            logger.error(f"Error building portfolio from Q&A: {str(e)}")
            raise
    
    async def _generate_portfolio(self, data: Dict[str, Any], template_name: str) -> str:
        """
        Generate portfolio content using AI and the specified template.
        
        Args:
            data: Portfolio data
            template_name: Name of the template to use
            
        Returns:
            str: Path to the generated HTML file
        """
        try:
            # First, enhance the content with AI
            enhanced_data = await self._enhance_with_ai(data)
            
            # Load the template
            try:
                template = self.env.get_template(f"{template_name}.html")
            except Exception as e:
                logger.warning(f"Template {template_name} not found, using default: {str(e)}")
                template = self.env.get_template("default.html")
            
            # Render template with enhanced portfolio data
            html_content = template.render(**enhanced_data)
            
            # Save to file with a unique name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = get_temp_file(f"portfolio_{timestamp}.html")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error generating portfolio: {str(e)}")
            # Fall back to basic template rendering if AI enhancement fails
            try:
                template = self.env.get_template("default.html")
                html_content = template.render(**(data or {}))
                output_file = get_temp_file("portfolio_fallback.html")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return output_file
            except Exception as fallback_error:
                logger.error(f"Fallback portfolio generation failed: {str(fallback_error)}")
                raise
    
    async def _enhance_with_ai(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance portfolio content using AI.
        
        Args:
            portfolio_data: Raw portfolio data
            
        Returns:
            Enhanced portfolio data with AI-generated content
        """
        try:
            # Prepare prompt for AI enhancement
            prompt = f"""
            You are an expert portfolio content writer. Enhance the following portfolio information
            to make it more compelling and professional.
            
            PORTFOLIO DATA:
            {json.dumps(portfolio_data, indent=2, ensure_ascii=False)}
            
            TASKS:
            1. Write a compelling professional summary if not provided
            2. Enhance work experience descriptions with quantifiable achievements
            3. Ensure consistent formatting and professional tone
            4. Add relevant skills and technologies to the skills section
            5. Suggest improvements for education and project descriptions
            
            Return the enhanced portfolio data in the same JSON structure.
            """
            
            # Get AI-enhanced content
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert career advisor and portfolio writer. "
                               "Your goal is to help professionals create outstanding portfolios."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = await self.groq_client._make_request(messages)
            
            try:
                # Try to parse the response as JSON
                enhanced_data = json.loads(response)
                return enhanced_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI-enhanced portfolio as JSON, using original data")
                return portfolio_data
                
        except Exception as e:
            logger.error(f"Error enhancing portfolio with AI: {str(e)}")
            return portfolio_data
    
    def _convert_qa_to_portfolio_data(self, qa_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert Q&A data to structured portfolio data.
        
        Args:
            qa_data: Dictionary of question-answer pairs
            
        Returns:
            Dict[str, Any]: Structured portfolio data
        """
        # Map questions to portfolio data fields
        field_map = {
            "What is your full name?": "name",
            "What is your professional title/headline?": "title",
            "Please provide a brief professional summary (2-3 sentences):": "summary",
            "What is your email address?": "email",
            "What is your phone number?": "phone",
            "What is your location (City, Country)?": "location",
            "List your top 5-10 skills (comma-separated):": "skills"
        }
        
        # Initialize portfolio data
        portfolio_data = {
            "experience": [],
            "education": [],
            "skills": []
        }
        
        # Map Q&A to portfolio data
        for question, answer in qa_data.items():
            field = field_map.get(question)
            if field:
                if field == "skills":
                    # Split skills by comma and strip whitespace
                    portfolio_data[field] = [s.strip() for s in answer.split(",") if s.strip()]
                else:
                    portfolio_data[field] = answer
        
        # Parse work experience if present in Q&A
        work_exp_key = "Tell me about your work experience (company, title, dates, responsibilities - one per line, empty line to finish):"
        if work_exp_key in qa_data and qa_data[work_exp_key].strip():
            experience_entries = qa_data[work_exp_key].split('\n\n')
            for entry in experience_entries:
                lines = [line.strip() for line in entry.split('\n') if line.strip()]
                if len(lines) >= 3:
                    # Simple parsing of company, title, dates, and bullet points
                    title_company = lines[0].split(' at ')
                    if len(title_company) == 2:
                        title, company = title_company
                    else:
                        title, company = lines[0], ""
                    
                    # Extract dates (simple pattern matching)
                    date_range = lines[1]
                    dates = re.findall(r'(\d{4}-\d{2}|\w+ \d{4})', date_range)
                    start_date = dates[0] if dates else ""
                    end_date = dates[1] if len(dates) > 1 else "Present"
                    
                    portfolio_data["experience"].append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "start_date": start_date,
                        "end_date": end_date,
                        "description": lines[2:]
                    })
        
        return portfolio_data

# This will be initialized in main.py with the proper GroqClient instance
portfolio_builder = None