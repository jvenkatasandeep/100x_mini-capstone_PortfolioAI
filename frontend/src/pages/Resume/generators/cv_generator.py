import streamlit as st
from typing import Dict, List, Optional, Tuple
import base64
import json
import logging
import requests
from pathlib import Path
from src.components.sections.header import show_header

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session state keys
RESUME_DATA = 'cv_resume_data'
CURRENT_STEP = 'cv_current_step'

# Constants
STEPS = [
    'Personal Information',
    'Work Experience',
    'Education & Skills',
    'Template & Generate'
]

def initialize_session_state():
    """Initialize session state for CV generator if not already done."""
    if RESUME_DATA not in st.session_state:
        st.session_state[RESUME_DATA] = {
            'personal_info': {},
            'work_experience': [],
            'education': [],
            'skills': [],
            'template': 'professional',
            'format': 'pdf',
            'include_photo': True
        }
    
    if CURRENT_STEP not in st.session_state:
        st.session_state[CURRENT_STEP] = 0

def show_cv_header():
    """Display the CV generator specific header."""
    st.markdown("""
    <style>
        /* Global text color */
        .stTextInput > label, .stTextArea > label, .stMarkdown p, 
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
        .stCheckbox > label, .stSelectbox > label, .stRadio > label,
        .stTextArea > div > div > textarea, .stTextInput > div > div > input,
        .stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder {
            color: #000000 !important;
        }
        
        /* Main button styling */
        .stButton>button {
            background-color: #4f8bf9;
            color: white !important;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #3a7de8;
            color: white !important;
        }
        
        /* Input field styling */
        .stTextInput>div>div>input, .stTextArea>div>textarea {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 0.5rem;
            color: #000000 !important;
        }
        
        /* Section headers */
        h3 {
            color: #000000 !important;
            margin-top: 1.5rem;
        }
        
        /* Progress indicator */
        .stProgress > div > div > div > div {
            background-color: #4f8bf9;
        }
        
        /* Checkbox and radio button labels */
        .stCheckbox > label, .stRadio > label {
            color: #000000 !important;
        }
        
        /* Expander headers */
        .stExpander > label > div > p {
            color: #000000 !important;
        }
        
        /* File uploader */
        .stFileUploader > label, .stFileUploader > div > div > div > span {
            color: #000000 !important;
        }
        
        /* Required field asterisks */
        .stMarkdown > p > small::before {
            color: #ff4b4b !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown("<h1 style='margin: 0; padding: 0;'>PortfolioAI</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("Logout", key="cv_logout_btn", type="primary"):
            st.session_state.clear()
            st.rerun()
    
    # Breadcrumb with updated styling
    st.markdown("<p style='color: #6b7280; margin: 0.5rem 0;'><a href='#' style='color: #4f8bf9; text-decoration: none;'>Home</a> / <strong>CV Generator</strong></p>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)

def show_step_indicator():
    """Display the current step indicator."""
    current = st.session_state[CURRENT_STEP] + 1
    total = len(STEPS)
    
    # Create a progress bar
    progress = current / total
    st.progress(progress)
    
    # Display step information with better styling
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin: 1rem 0;'>
        <div style='font-size: 1.1rem; color: #1e3a8a; font-weight: 600;'>
            Step {current} of {total}: {STEPS[st.session_state[CURRENT_STEP]]}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a subtle divider
    st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)

def show_personal_info_step() -> bool:
    """Display and handle the personal information step."""
    st.markdown("### Personal Information")
    
    # Get existing data or initialize
    personal_info = st.session_state[RESUME_DATA].get('personal_info', {})
    
    # Single name field instead of first/last
    name = st.text_input("Full Name*", 
                        value=personal_info.get('name', 
                            f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}".strip()
                        ))
    
    col1, col2 = st.columns(2)
    
    with col1:
        email = st.text_input("Email*", 
                            value=personal_info.get('email', ''))
        phone = st.text_input("Phone*", 
                             value=personal_info.get('phone', ''))
    
    with col2:
        location = st.text_input("Location", 
                               value=personal_info.get('location', ''))
        profile_pic = st.file_uploader("Profile Picture (optional)", 
                                      type=['jpg', 'jpeg', 'png'],
                                      key='profile_uploader')
    
    # Professional summary/objective
    summary = st.text_area("Professional Summary",
                          value=personal_info.get('summary', ''),
                          help="A brief overview of your professional background and goals")
    
    # Save uploaded file
    if profile_pic is not None:
        file_ext = profile_pic.name.split('.')[-1].lower()
        file_name = f"profile_pic.{file_ext}"
        file_path = Path("uploads") / file_name
        
        # Create uploads directory if it doesn't exist
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(profile_pic.getbuffer())
        st.session_state[RESUME_DATA]['personal_info']['profile_pic'] = str(file_path)
    
    # Validate required fields
    required_fields = [name, email, phone]
    if not all(required_fields):
        st.error("Please fill in all required fields (marked with *)")
        return False
    
    # Save data
    st.session_state[RESUME_DATA]['personal_info'].update({
        'name': name,
        'email': email,
        'phone': phone,
        'location': location,
        'summary': summary
    })
    
    return True

def show_work_experience_step() -> bool:
    """Display and handle the work experience step."""
    st.markdown("### Work Experience")
    
    # Initialize work experience in session state if not exists
    if 'work_experience' not in st.session_state[RESUME_DATA] or not st.session_state[RESUME_DATA]['work_experience']:
        st.session_state[RESUME_DATA]['work_experience'] = [{
            'company': '',
            'position': '',
            'start_date': '',
            'end_date': '',
            'is_current': False,
            'description': [],
            'location': ''
        }]
    
    # Get a reference to the work experience list
    work_exp = st.session_state[RESUME_DATA]['work_experience']
    
    # Display existing experiences
    for i, exp in enumerate(work_exp):
        with st.expander(f"Work Experience {i+1}", expanded=True):
            company = st.text_input(f"Company*", 
                                 value=exp.get('company', ''),
                                 key=f"company_{i}")
            
            col1, col2 = st.columns(2)
            with col1:
                position = st.text_input(f"Job Title*", 
                                      value=exp.get('position', exp.get('title', '')),
                                      key=f"position_{i}")
            with col2:
                location = st.text_input(f"Location",
                                     value=exp.get('location', ''),
                                     key=f"location_{i}")
            
            # Date inputs
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.text_input(f"Start Date (MM/YYYY)*", 
                                        value=exp.get('start_date', ''),
                                        key=f"start_date_{i}")
            with col2:
                is_current = st.checkbox("I currently work here", 
                                       value=exp.get('is_current', False),
                                       key=f"is_current_{i}")
                end_date = None
                if not is_current:
                    end_date = st.text_input(f"End Date (MM/YYYY)*", 
                                          value=exp.get('end_date', ''),
                                          key=f"end_date_{i}")
                else:
                    end_date = "Present"
            
            # Description as bullet points
            st.markdown("**Responsibilities & Achievements** (one per line, will be formatted as bullet points)")
            description = st.text_area("Work Description",
                                    value='\n'.join(exp.get('description', [])) if isinstance(exp.get('description'), list) else exp.get('description', ''),
                                    key=f"description_{i}",
                                    height=100,
                                    label_visibility="collapsed")
            
            # Convert description to list of strings (one per line)
            description_list = [line.strip() for line in description.split('\n') if line.strip()]
            
                    # Update experience
            work_exp[i] = {
                'company': company.strip(),
                'position': position.strip(),
                'title': position.strip(),  # Add title as an alias for position
                'start_date': start_date.strip(),
                'end_date': end_date.strip() if isinstance(end_date, str) else end_date,
                'is_current': is_current,
                'description': description_list if description_list else [''],
                'location': location.strip()
            }
    
    # Update the session state with the modified work experience
    st.session_state[RESUME_DATA]['work_experience'] = work_exp
    
    # Add new experience button
    if st.button("➕ Add Another Position"):
        work_exp.append({
            'company': '',
            'position': '',
            'start_date': '',
            'end_date': '',
            'is_current': False,
            'description': [''],
            'location': ''
        })
        st.rerun()
    
    # Check if any experience has all required fields
    has_valid = False
    for exp in work_exp:
        # Check required fields
        if not all([exp.get('company', '').strip(), 
                   exp.get('position', '').strip(), 
                   exp.get('start_date', '').strip()]):
            continue
            
        # Check dates
        if not exp.get('is_current') and not exp.get('end_date', '').strip():
            continue
            
        has_valid = True
        break
    
    if not has_valid and any(exp.get('company') or exp.get('position') for exp in work_exp):
        st.error("Please fill in all required fields for at least one work experience (Company, Position, Start Date, and either End Date or 'I currently work here')")
        return False
    
    return has_valid or not any(exp.get('company') or exp.get('position') for exp in work_exp)

def show_education_skills_step() -> bool:
    """Display and handle the education and skills step."""
    st.markdown("### Education & Skills")
    
    # Education Section
    st.markdown("#### Education")
    education = st.session_state[RESUME_DATA].get('education', [])
    
    # Initialize with one empty education if none exists
    if not education:
        education = [{
            'institution': '',
            'degree': '',
            'field_of_study': '',
            'start_year': '',
            'end_year': '',
            'is_ongoing': False,
            'gpa': ''
        }]
    
    # Display education entries
    for i, edu in enumerate(education):
        with st.expander(f"Education {i+1}", expanded=True):
            institution = st.text_input(f"Institution*",
                                     value=edu.get('institution', ''),
                                     key=f"institution_{i}")
            
            col1, col2 = st.columns(2)
            with col1:
                degree = st.text_input(f"Degree*",
                                    value=edu.get('degree', ''),
                                    key=f"degree_{i}",
                                    placeholder="e.g., Bachelor of Science")
            with col2:
                field_of_study = st.text_input(f"Field of Study",
                                            value=edu.get('field_of_study', ''),
                                            key=f"field_{i}",
                                            placeholder="e.g., Computer Science")
            
            col1, col2 = st.columns(2)
            with col1:
                # Start date as YYYY or MM/YYYY
                start_year = st.text_input(f"Start Year (YYYY or MM/YYYY)*",
                                        value=edu.get('start_year', edu.get('start_date', '')),
                                        key=f"start_year_{i}",
                                        placeholder="e.g., 2018 or 09/2018")
            with col2:
                is_ongoing = st.checkbox(f"Currently Enrolled",
                                       value=edu.get('is_ongoing', False),
                                       key=f"ongoing_{i}")
                if not is_ongoing:
                    end_year = st.text_input(f"End Year (YYYY or MM/YYYY)",
                                          value=edu.get('end_year', edu.get('end_date', '')),
                                          key=f"end_year_{i}",
                                          placeholder="e.g., 2022 or 05/2022")
                else:
                    end_year = "Present"
            
            # GPA input
            gpa = st.text_input(f"GPA (Optional)",
                             value=edu.get('gpa', '') if edu.get('gpa') is not None else '',
                             key=f"gpa_{i}",
                             placeholder="e.g., 3.7")
            
            # Format dates for display
            start_date = f"{start_year}-01-01" if start_year and len(start_year) == 4 else start_year
            end_date = None
            if not is_ongoing and end_year and end_year.lower() != 'present':
                end_date = f"{end_year}-12-31" if len(end_year) == 4 else end_year
            
            # Handle GPA validation safely
            processed_gpa = None
            if gpa:  # Only process if gpa is not None and not empty string
                try:
                    # Try to convert to float and validate it's a positive number
                    gpa_float = float(gpa)
                    if 0.0 <= gpa_float <= 4.0:  # Assuming 4.0 scale, adjust if needed
                        processed_gpa = gpa_float
                except (ValueError, TypeError):
                    # If conversion fails, keep it as None
                    processed_gpa = None
            
            # Update education
            education[i] = {
                'institution': institution,
                'degree': degree,
                'field_of_study': field_of_study,
                'start_year': start_year,
                'end_year': end_year,
                'start_date': start_date,
                'end_date': end_date,
                'is_ongoing': is_ongoing,
                'gpa': processed_gpa
            }
    
    # Add new education button
    if st.button("➕ Add Another Education"):
        education.append({
            'institution': '',
            'degree': '',
            'field_of_study': '',
            'start_year': '',
            'end_year': '',
            'is_ongoing': False,
            'gpa': ''
        })
        st.experimental_rerun()
    
    # Save education to session state
    st.session_state[RESUME_DATA]['education'] = education
    
    # Validate at least one education entry is complete
    for i, edu in enumerate(education):
        if not all([edu['institution'], edu['degree'], edu['start_year']]):
            st.error(f"Please fill in all required fields for Education {i+1} (Institution, Degree, Start Year)")
            return False
        if not edu['is_ongoing'] and not edu['end_year']:
            st.error(f"Please provide an end year or check 'Currently Enrolled' for Education {i+1}")
            return False
    
    # Skills Section
    st.markdown("#### Skills")
    
    # Get current skills or initialize empty list
    current_skills = st.session_state[RESUME_DATA].get('skills', [])
    
    # Ensure current_skills is a list
    if isinstance(current_skills, str):
        current_skills = [s.strip() for s in current_skills.split(',') if s.strip()]
    elif not isinstance(current_skills, list):
        current_skills = []
    
    # Skills input with chips/tags style
    st.markdown("**Add your skills (comma separated)**")
    skills_input = st.text_input("", 
                               value=", ".join(current_skills) if current_skills else "",
                               key="skills_input",
                               placeholder="e.g., Python, Project Management, Data Analysis")
    
    # Update skills when input changes
    if skills_input:
        # Split by comma and clean up
        new_skills = [skill.strip() for skill in skills_input.split(",") if skill.strip()]
        st.session_state[RESUME_DATA]['skills'] = new_skills
        current_skills = new_skills  # Update current_skills to reflect changes
    
    # Display current skills as tags
    if current_skills:
        st.write("Your skills:")
        cols = st.columns(4)
        for i, skill in enumerate(current_skills):
            if not skill:
                continue
            with cols[i % 4]:
                if st.button(f"× {skill}", key=f"skill_{i}"):
                    if skill in current_skills:
                        current_skills.remove(skill)
                        st.session_state[RESUME_DATA]['skills'] = current_skills
                        st.experimental_rerun()
    
    # Save to session state
    st.session_state[RESUME_DATA]['education'] = education
    
    # Validate at least one education entry is complete
    for edu in education:
        if not all([edu['institution'], edu['degree'], edu['start_year']]):
            st.error("Please fill in all required fields for each education entry (Institution, Degree, Start Year)")
            return False
        if not edu['is_ongoing'] and not edu['end_year']:
            st.error("Please provide an end year or check 'Ongoing'")
            return False
    
    return True

def show_template_step() -> bool:
    """Display and handle the template and generate step."""
    # Add CSS to ensure all text is black
    st.markdown("""
    <style>
        h1, h2, h3, h4, h5, h6, p, label, div[data-testid="stMarkdownContainer"],
        .stRadio > div, .stCheckbox > div, .stRadio label, .stCheckbox label,
        .stRadio p, .stCheckbox p, .stRadio span, .stCheckbox span {
            color: black !important;
        }
        /* Style radio buttons and checkboxes to be more visible */
        .stRadio > div > label, .stCheckbox > label {
            color: black !important;
            font-weight: normal;
        }
        /* Ensure the radio button circles are visible */
        .stRadio > div > div[role="radiogroup"] > div[role="radio"] > div:first-child {
            background-color: white;
            border: 1px solid black;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### Choose Template & Generate")
    
    # Template Selection
    st.markdown("#### Select a Template")
    
    # Define available templates and their display names
    template_options = ["modern", "professional", "creative", "simple"]
    template_display_names = [t.capitalize() for t in template_options]
    
    # Get current template, defaulting to 'modern' if not set
    current_template = st.session_state[RESUME_DATA].get('template', 'modern')
    
    # Ensure the current template is in the options
    if current_template not in template_options:
        current_template = 'modern'
    
    # Display template selection
    selected_template_display = st.radio(
        "Choose a template style:",
        options=template_display_names,
        index=template_options.index(current_template),
        key="template_radio"
    )
    
    # Map display name back to template name
    selected_template = template_options[template_display_names.index(selected_template_display)]
    
    # Format Selection
    st.markdown("#### Select Output Format")
    format_options = ["pdf", "docx"]
    format_display_names = [f.upper() for f in format_options]
    
    # Get current format, defaulting to 'pdf' if not set
    current_format = st.session_state[RESUME_DATA].get('format', 'pdf')
    
    # Ensure the current format is in the options
    if current_format not in format_options:
        current_format = 'pdf'
    
    # Display format selection
    selected_format_display = st.radio(
        "Choose output format:",
        options=format_display_names,
        index=format_options.index(current_format),
        key="format_radio"
    )
    
    # Map display name back to format name
    selected_format = format_options[format_display_names.index(selected_format_display)]
    
    # Include Photo Option
    include_photo = st.checkbox(
        "Include Profile Picture",
        value=st.session_state[RESUME_DATA].get('include_photo', True),
        key="include_photo_checkbox"
    )
    
    # Save selections
    st.session_state[RESUME_DATA].update({
        'template': selected_template,
        'format': selected_format,
        'include_photo': include_photo
    })
    
    # Preview Section
    st.markdown("### Preview")
    st.markdown("Here's a summary of your CV:")
    
    # Personal Info Preview
    personal = st.session_state[RESUME_DATA]['personal_info']
    st.markdown(f"**Name:** {personal.get('first_name', '')} {personal.get('last_name', '')}")
    st.markdown(f"**Email:** {personal.get('email', '')}")
    st.markdown(f"**Phone:** {personal.get('phone', '')}")
    if personal.get('location'):
        st.markdown(f"**Location:** {personal.get('location')}")
    
    # Work Experience Preview
    st.markdown("**Work Experience:**")
    for exp in st.session_state[RESUME_DATA].get('work_experience', []):
        st.markdown(f"- **{exp.get('position', '')}** at {exp.get('company', '')} "
                   f"({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})")
    
    # Education Preview
    st.markdown("**Education:**")
    for edu in st.session_state[RESUME_DATA].get('education', []):
        end_year = edu.get('end_year', 'Present') if edu.get('is_ongoing') else edu.get('end_year', '')
        st.markdown(f"- **{edu.get('degree', '')}** in {edu.get('field_of_study', '')} "
                   f"from {edu.get('institution', '')} "
                   f"({edu.get('start_year', '')} - {end_year})")
    
    # Skills Preview
    if st.session_state[RESUME_DATA].get('skills'):
        st.markdown("**Skills:**")
        st.markdown(", ".join(st.session_state[RESUME_DATA]['skills']))
    
    return True

def generate_cv():
    """Generate the CV using the backend API with improved error handling and feedback."""
    import time
    from datetime import datetime
    
    # Initialize status elements
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    def update_status(step, total_steps=5, message=""):
        """Update the progress and status message."""
        progress = int((step / total_steps) * 100)
        progress_bar.progress(progress)
        if message:
            status_container.info(f"Status: {message}")
    
    try:
        # Step 1: Prepare data
        update_status(1, message="Preparing your CV data...")
        
        # Import the API service
        from src.services.api import APIService
        
        # Get the JWT token from session state if available
        token = st.session_state.get('jwt_token')
        
        # Get skills and ensure they're properly formatted
        skills = st.session_state[RESUME_DATA].get('skills', [])
        # Ensure skills is a list of strings
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',') if s.strip()]
        elif not isinstance(skills, list):
            skills = []
            
        # Prepare the CV data from session state
        cv_data = {
            'personal_info': st.session_state[RESUME_DATA].get('personal_info', {}),
            'work_experience': st.session_state[RESUME_DATA].get('work_experience', []),
            'education': st.session_state[RESUME_DATA].get('education', []),
            'skills': skills,  # Use the processed skills list
            'template': st.session_state[RESUME_DATA].get('template', 'modern'),
            'format': st.session_state[RESUME_DATA].get('format', 'pdf')
        }
        
        # Step 2: Generate CV
        update_status(2, message="Generating your CV (this may take a minute)...")
        
        # Call the API to generate the CV
        result = APIService.generate_cv(cv_data, token=token)
        
        # Check if we got a valid response
        if not result:
            raise ValueError("No response received from the server")
        
        # Step 3: Handle API response
        update_status(3, message="Processing response...")
        
        # Debug: Show API response in expander and log it
        # Create a safe copy of the result for logging (without binary data)
        log_result = result.copy()
        if 'content' in log_result and isinstance(log_result['content'], (bytes, bytearray)):
            log_result['content'] = f"[binary data, size: {len(log_result['content'])} bytes]"
        
        logger.info(f"Received API response: {json.dumps(log_result, indent=2, default=str)}")
        
        # Show the response in an expander
        with st.expander("Show API Response (Frontend Debug)"):
            st.json(log_result)
        
        if result.get('status') != 'success':
            error_msg = result.get('message', 'Failed to generate CV')
            logger.error(f"API returned error status. Message: {error_msg}, Full response: {result}")
            # Check for nested details from backend error handling
            if 'details' in result and isinstance(result['details'], dict):
                detailed_error = result['details'].get('detail', '')
                if detailed_error:
                    error_msg += f" (Details: {detailed_error})"
            elif 'details' in result: # if details is not a dict but present
                 error_msg += f" (Details: {result['details']})"

            raise Exception(f"API Error: {error_msg}")
        
        # Get CV ID and content from response
        cv_id = result.get('cv_id')
        logger.info(f"Extracted cv_id: {cv_id}")
        if not cv_id:
            logger.error("cv_id not found in API response.")
            raise ValueError("No CV ID returned from the server")
            
        # Get the content directly from the response
        content = result.get('content')
        if isinstance(content, str):
            # If content is a string, it's base64 encoded
            logger.info("Content is base64 encoded, decoding...")
            try:
                content = base64.b64decode(content)
                logger.info(f"Successfully decoded base64 content. Decoded content length: {len(content)} bytes")
            except Exception as e:
                logger.error(f"Failed to decode base64 content: {str(e)}")
                raise ValueError(f"Failed to decode CV content: {str(e)}")
        elif content is None:
            logger.error("No content found in API response")
            raise ValueError("No CV content returned from the server")
        
        # Get content type and file extension
        content_type = result.get('content_type', 'application/pdf').lower()
        filename = result.get('filename', f'cv_{cv_id}.pdf')
        file_extension = filename.split('.')[-1].lower()
        
        # Ensure the content is bytes
        if not isinstance(content, (bytes, bytearray)):
            logger.error(f"Content is not in binary format. Type: {type(content)}")
            raise ValueError("Invalid CV content format received from server")
            
        logger.info(f"Content type: {content_type}, Filename: {filename}, Extension: {file_extension}")
        
        # Step 4: Display the result
        update_status(4, message="CV ready!")
        
        # Show success message
        st.success("🎉 CV generated successfully!")
        st.balloons()
        
        # Create a download button for the CV
        st.download_button(
            label=f"⬇️ Download CV ({file_extension.upper()})",
            data=content,
            file_name=filename,
            mime=content_type,
            key=f"download_cv_{cv_id}_{int(time.time())}"  # Add timestamp to force refresh
        )
        
        # Show a preview for PDFs
        if 'pdf' in content_type:
            with st.expander("📄 Preview CV"):
                try:
                    base64_pdf = base64.b64encode(content).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Failed to display PDF preview: {str(e)}")
                    st.warning("Could not display PDF preview. Please download the file to view it.")
        
        return True
        
    except requests.exceptions.RequestException as e:
        st.error("❌ Network error: Failed to connect to the server. Please check your internet connection and try again.")
        st.error(f"Details: {str(e)}")
        logger.error(f"Network error during CV generation: {str(e)} - URL: {e.request.url if hasattr(e, 'request') else 'N/A'}")
    except json.JSONDecodeError as e:
        st.error("❌ Error: Invalid response from the server. The server might be experiencing issues.")
        st.error(f"Details: {str(e)}")
        logger.error(f"JSON decode error in CV generation: {str(e)}")
    except ValueError as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"Value error in CV generation: {str(e)}")
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        st.error(f"❌ An unexpected error occurred: {error_msg}")
        logger.error(f"Unexpected error in CV generation ({error_type}): {error_msg}")
        
        # Show more detailed error information in an expander for debugging
        with st.expander("Show error details"):
            st.text(f"Error type: {error_type}")
            st.text(f"Error message: {error_msg}")
            import traceback
            st.code(traceback.format_exc())
            
            # Show the last few API responses if available
            if 'last_api_response' in locals():
                st.subheader("Last API Response")
                st.json(result)
    
    finally:
        # Ensure we always clear the progress bar
        progress_bar.empty()
        status_container.empty()
        
        # Add a small delay to ensure the UI updates
        time.sleep(0.5)
        
    return False

def validate_current_step() -> bool:
    """Validate the current step's inputs."""
    current_step = st.session_state[CURRENT_STEP]
    
    # Personal Info Step
    if current_step == 0:
        personal_info = st.session_state[RESUME_DATA].get('personal_info', {})
        required_fields = [
            (personal_info.get('name', '').strip(), 'Full name is required'),
            (personal_info.get('email', '').strip(), 'Email is required'),
            (personal_info.get('phone', '').strip(), 'Phone number is required')
        ]
        
        for field, error_msg in required_fields:
            if not field:
                st.error(error_msg)
                return False
                
        # Validate email format
        import re
        email = personal_info.get('email', '')
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            st.error('Please enter a valid email address')
            return False
            
    # Work Experience Step
    elif current_step == 1:
        work_experience = st.session_state[RESUME_DATA].get('work_experience', [])
        if not work_experience:
            st.error('Please add at least one work experience')
            return False
            
    # Education and Skills Step
    elif current_step == 2:
        education = st.session_state[RESUME_DATA].get('education', [])
        skills = st.session_state[RESUME_DATA].get('skills', [])
        
        if not education:
            st.error('Please add at least one education entry')
            return False
            
        if not skills:
            st.error('Please add at least one skill')
            return False
            
    # Template Step
    elif current_step == 3:
        if not st.session_state[RESUME_DATA].get('template'):
            st.error('Please select a template')
            return False
    
    return True

def show_cv_generator():
    """Main function to display the CV generator."""
    # Add CSS to ensure all text is black and buttons are readable
    st.markdown("""
    <style>
    /* Force all text to be black */
    * {
        color: #000000 !important;
    }
    /* Style text inputs and textareas */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label, 
    .stDateInput > label, .stCheckbox > label, .stRadio > label,
    .stMultiSelect > label, .stNumberInput > label, .stFileUploader > label,
    .stTimeInput > label, .stColorPicker > label, .stSlider > label {
        color: #000000 !important;
    }
    /* Style all buttons */
    .stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    .stButton > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #999999 !important;
    }
    /* Primary buttons */
    .stButton > button.primary {
        background-color: #1f77b4 !important;
        color: #ffffff !important;
        border: 1px solid #1a6da3 !important;
    }
    .stButton > button.primary:hover {
        background-color: #1a6da3 !important;
    }
    /* Style placeholder text */
    ::placeholder {
        color: #666666 !important;
        opacity: 1 !important; /* Firefox */
    }
    /* Style checkboxes and radio buttons */
    .stCheckbox > div > label, .stRadio > div > label {
        color: #000000 !important;
    }
    /* Style expander headers */
    .streamlit-expanderHeader {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Show the current step
    show_step_indicator()
    
    # Navigation buttons
    col1, col2, col3 = st.columns([2, 1, 2])
    
    # Show the appropriate step content and get validation result
    validation_passed = False
    if st.session_state[CURRENT_STEP] == 0:
        validation_passed = show_personal_info_step()
    elif st.session_state[CURRENT_STEP] == 1:
        validation_passed = show_work_experience_step()
    elif st.session_state[CURRENT_STEP] == 2:
        validation_passed = show_education_skills_step()
    elif st.session_state[CURRENT_STEP] == 3:
        validation_passed = show_template_step()
    
    with col1:
        if st.session_state[CURRENT_STEP] > 0:
            if st.button("← Back"):
                st.session_state[CURRENT_STEP] -= 1
                st.rerun()
    
    with col3:
        # Only proceed with navigation if the current step's validation passed
        if st.session_state[CURRENT_STEP] < len(STEPS) - 1:
            if st.button("Next →"):
                # Set form as submitted before validation
                st.session_state['form_submitted'] = True
                if validate_current_step():
                    st.session_state[CURRENT_STEP] += 1
                    st.rerun()
        else:
            if st.button("Generate CV", type="primary"):
                # Set form as submitted before validation
                st.session_state['form_submitted'] = True
                if validate_current_step():
                    generate_cv()
    
    # Debug: Show current state (can be removed in production)
    if st.checkbox("Show debug info"):
        st.json(st.session_state[RESUME_DATA])

# This allows the file to be run directly for testing
if __name__ == "__main__":
    show_cv_generator()
