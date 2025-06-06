"""
Simple Portfolio Generator

A streamlined interface for generating portfolios from resumes using AI.
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MAX_FILE_SIZE_MB = 5  # Maximum file size in MB

# Page config
st.set_page_config(
    page_title="PortfolioAI - Simple Generator",
    page_icon="✨",
    layout="wide"
)

def display_header():
    """Display the page header."""
    st.title("✨ PortfolioAI")
    st.markdown("### Simple Portfolio Generator")
    st.markdown("Upload your resume and select sections to generate a professional portfolio.")
    st.markdown("---")

def get_available_sections() -> List[str]:
    """Return list of available portfolio sections."""
    return [
        "about",
        "experience",
        "education",
        "skills",
        "projects",
        "contact"
    ]

def validate_file(file) -> Optional[str]:
    """Validate the uploaded file."""
    if file is None:
        return "No file uploaded"
    
    # Check file size (5MB limit)
    file_size = len(file.getvalue()) / (1024 * 1024)  # Convert to MB
    if file_size > MAX_FILE_SIZE_MB:
        return f"File size ({file_size:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
    
    # Check file type
    valid_types = ["application/pdf", 
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                  "application/msword"]
    if file.type not in valid_types:
        return f"Unsupported file type: {file.type}. Please upload a PDF or DOCX file."
    
    return None

def generate_portfolio(resume_file, selected_sections: List[str]) -> Dict[str, Any]:
    """Send request to backend to generate portfolio."""
    try:
        # Reset any previous error
        if "error" in st.session_state:
            del st.session_state.error
            
        files = {"file": (resume_file.name, resume_file, resume_file.type)}
        params = {"sections": ",".join(selected_sections)}
        
        with st.spinner("Generating your portfolio..."):
            response = requests.post(
                f"{BACKEND_URL}/api/portfolio/generate",
                files=files,
                params=params,
                timeout=60  # 60 seconds timeout
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = response.json().get("detail", "Unknown error occurred")
            st.session_state.error = f"Error generating portfolio: {error_msg}"
            return None
            
    except requests.exceptions.RequestException as e:
        st.session_state.error = f"Connection error: {str(e)}"
        return None
    except Exception as e:
        st.session_state.error = f"An unexpected error occurred: {str(e)}"
        return None

def display_portfolio(portfolio_data: Dict[str, Any]):
    """
    Display the generated portfolio with proper formatting and error handling.
    
    Args:
        portfolio_data: Dictionary containing the portfolio data from the API
    """
    st.subheader("✨ Generated Portfolio")
    st.markdown("---")
    
    if not portfolio_data:
        st.error("No portfolio data available.")
        return
    
    # Check for error in response
    if "error" in portfolio_data:
        st.error(f"Error: {portfolio_data['error']}")
        return
    
    # Get the portfolio content
    portfolio = portfolio_data.get("portfolio", {})
    
    # Handle different response formats
    if not portfolio:
        st.warning("No portfolio content was generated.")
        return
        
    # If portfolio is a string (raw content)
    if isinstance(portfolio, str):
        st.markdown(portfolio)
        return
    
    # If portfolio has sections
    if "sections" in portfolio and isinstance(portfolio["sections"], list):
        for section in portfolio["sections"]:
            if not isinstance(section, dict):
                continue
                
            section_name = section.get("name", "").strip()
            section_content = section.get("content", "").strip()
            
            if not section_content:
                continue
                
            # Display section with proper formatting
            if section_name:
                st.markdown(f"### {section_name.title()}")
            
            # Handle markdown content
            st.markdown(section_content, unsafe_allow_html=True)
            
            # Add a divider between sections
            if section_name:  # Only add divider if there's a section name
                st.markdown("---")
    
    # If portfolio has direct content
    elif "content" in portfolio and portfolio["content"]:
        st.markdown(portfolio["content"], unsafe_allow_html=True)
    
    # If no valid content found
    else:
        st.warning("The portfolio format is not recognized. Showing raw data:")
        st.json(portfolio)

def display_error():
    """Display error message if any."""
    if "error" in st.session_state:
        st.error(st.session_state.error)
        if st.button("Dismiss Error", key="dismiss_error_btn"):
            del st.session_state.error
            st.rerun()

def main():
    """Main application function."""
    # Initialize session state
    if "portfolio_data" not in st.session_state:
        st.session_state.portfolio_data = None
    
    display_header()
    
    # File upload
    st.sidebar.header("1. Upload Your Resume")
    resume_file = st.sidebar.file_uploader(
        label="Resume Upload",
        help=f"Upload your resume (PDF or DOCX, max {MAX_FILE_SIZE_MB}MB)",
        type=["pdf", "docx", "doc"],
        accept_multiple_files=False,
        key="resume_uploader"
    )
    
    # Section selection
    st.sidebar.header("2. Select Sections")
    available_sections = get_available_sections()
    selected_sections = []
    
    # Use columns to display checkboxes in 2 columns for better UI
    col1, col2 = st.sidebar.columns(2)
    for i, section in enumerate(available_sections):
        col = col1 if i % 2 == 0 else col2
        if col.checkbox(section.title(), value=True, key=f"section_{section}"):
            selected_sections.append(section)
    
    # Generate button
    if st.sidebar.button("✨ Generate Portfolio", use_container_width=True):
        if not resume_file:
            st.sidebar.error("Please upload a resume file")
            return
            
        if not selected_sections:
            st.sidebar.error("Please select at least one section")
            return
            
        # Validate file
        error = validate_file(resume_file)
        if error:
            st.sidebar.error(error)
            return
            
        # Generate portfolio
        portfolio_data = generate_portfolio(resume_file, selected_sections)
        if portfolio_data:
            st.session_state.portfolio_data = portfolio_data
            st.rerun()
    
    # Display error if any
    display_error()
    
    # Display portfolio if available
    if st.session_state.portfolio_data:
        display_portfolio(st.session_state.portfolio_data)

if __name__ == "__main__":
    main()
