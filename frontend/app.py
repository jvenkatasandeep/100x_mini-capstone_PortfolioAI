import streamlit as st
import os
import time
import json
import base64
from src.components.sections.header import show_header
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from urllib.parse import parse_qs, urlparse

# Import local modules
from src.pages.Auth.auth import is_authenticated, logout
from src.pages.Auth.login_page import show_login_page
from src.pages.Auth.reset_password_page import show_reset_password_page
from src.services.api import APIService
from src.pages.Home.landing import main as show_landing_page
from src.pages.Home.homepage import show_home_page as show_new_home_page
from src.pages.Resume.generators.cv_generator import show_cv_generator
from src.pages.Resume.generators.cover_letter_generator import show_cover_letter_generator
from src.pages.Portfolio.generators.portfolio_generator import show_portfolio_generator

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config - must be the first Streamlit command
# We'll set this only if it's not already set to avoid the duplicate config error
if 'page_config_set' not in st.session_state:
    st.set_page_config(
        page_title="Portfolio AI",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # Force light theme
    st.markdown(
        """
        <style>
            /* Disable dark mode */
            [data-testid="stAppViewContainer"] {
                color: #000000 !important;
                background-color: #FFFFFF !important;
            }
            
            /* Set cursor color to black */
            * {
                caret-color: #000000 !important;
            }
            
            /* Force light theme */
            [data-theme="light"] {
                --primary-color: #0066cc;
                --background-color: #FFFFFF;
                --secondary-background-color: #F7F8FA;
                --text-color: #000000;
                --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            /* Hide theme options */
            .st-eb {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.page_config_set = True

# Clear any existing session state if this is a fresh page load
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.initialized = True
    st.session_state.page = 'landing'  # Set default page to landing

# Inject app-wide styles
st.markdown("""
<style>
    :root {
        --primary-color: #0066cc;
        --background-color: #FFFFFF;
        --secondary-background: #F7F8FA;
        --text-color: #111111;
        --text-secondary: #666666;
        --border-color: #E0E0E0;
    }
    
    /* Base styles */
    body {
        color: var(--text-color);
        background-color: var(--background-color) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        margin: 0;
        padding: 0;
    }
    
    /* Force light theme */
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header, [data-testid="stToolbar"] {
        visibility: hidden !important;
    }
    
    /* Ensure text is visible in light theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input {
        color: var(--text-color) !important;
        background-color: var(--background-color) !important;
    }
    
    /* Main container */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Header styles */
    .header {
        background: #FFFFFF;
        padding: 12px 24px;
        border-bottom: 1px solid #E0E0E0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        z-index: 1000;
    }
    
    .header h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        color: #111111;
    }
    
    /* Button styles */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
        padding: 8px 16px;
        min-width: 100px;
        transition: all 0.2s;
    }
    
    .stButton>button:first-of-type {
        margin-right: 8px;
    }
    
    /* Main content */
    .main-content {
        padding: 88px 24px 40px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Feature grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 24px;
        margin-top: 32px;
    }
    
    /* Responsive adjustments */
    @ (max-width: 768px) {
        .feature-grid {
            grid-template-columns: 1fr;
        }
        
        .header-buttons {
            display: flex;
            gap: 8px;
        }
    }
    
    /* Hide Streamlit sidebar */
    .stApp > div:first-child {
        display: none;
    }
    
    /* Ensure content is not hidden behind fixed header */
    .stApp {
        padding-top: 0 !important;
    }
    
    /* Hide Streamlit's default header */
    .stApp > header {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Read URL query parameters for page routing
if 'page' in st.query_params:
    page_from_url = st.query_params['page']
    if page_from_url in ['landing', 'login', 'signup', 'home', 'upload', 'portfolio', 'cv-generator']:
        st.session_state.page = page_from_url

# Initialize session state variables
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

# Helper functions
def save_uploaded_file(uploaded_file) -> Optional[str]:
    """
    Save the uploaded file to a temporary directory and return the file path.
    
    Args:
        uploaded_file: The uploaded file object from Streamlit
        
    Returns:
        str: Path to the saved file, or None if an error occurs
    """
    try:
        # Create a temporary directory for uploads if it doesn't exist
        upload_dir = Path(tempfile.mkdtemp(prefix="portfolio_uploads_"))
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a unique filename to prevent collisions
        file_ext = Path(uploaded_file.name).suffix
        unique_filename = f"{int(time.time())}_{uploaded_file.name}"
        file_path = upload_dir / unique_filename
        
        # Save the file in chunks to handle large files
        with open(file_path, "wb") as f:
            # Get the buffer and write it in chunks
            buffer = uploaded_file.getvalue()
            chunk_size = 8192  # 8KB chunks
            for i in range(0, len(buffer), chunk_size):
                f.write(buffer[i:i + chunk_size])
        
        logger.info(f"Successfully saved uploaded file to: {file_path}")
        return str(file_path)
        
    except Exception as e:
        error_msg = f"Error saving uploaded file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None

import requests
from typing import Dict, Any
import os

def process_resume(file_path: str) -> Dict[str, Any]:
    """
    Process a resume file by sending it to the backend API for parsing and portfolio generation.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        dict: Parsed resume data
    """
    # Get the authentication token from session state if available
    token = st.session_state.get("token")
    
    try:
        # Call the API service
        result = APIService.process_resume(file_path, token=token)
        
        # Check for errors in the response
        if "error" in result or "status" in result and result.get("status") == "error":
            error_msg = result.get("message", "Failed to process resume")
            st.error(f"Error processing resume: {error_msg}")
            return {"error": error_msg}
            
        return result
        
    except Exception as e:
        error_msg = f"Error processing resume: {str(e)}"
        st.error(error_msg)
        return {"error": error_msg}

def generate_portfolio(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a portfolio based on the provided data.
    
    Args:
        data: Dictionary containing portfolio data
        
    Returns:
        dict: Generated portfolio data or error message
    """
    # Get the authentication token from session state if available
    token = st.session_state.get("token")
    
    try:
        # Call the API service
        result = APIService.generate_portfolio(data, token=token)
        
        # Check for errors in the response
        if "error" in result or "status" in result and result.get("status") == "error":
            error_msg = result.get("message", "Failed to generate portfolio")
            st.error(f"Error generating portfolio: {error_msg}")
            return {"error": error_msg}
            
        return result
        
    except Exception as e:
        error_msg = f"Error generating portfolio: {str(e)}"
        st.error(error_msg)
        return {"error": error_msg}

def show_home_page():
    """Display the home/dashboard page."""
    # Use the new homepage component
    show_new_home_page()

def show_upload_page():
    """Display the resume upload page."""
    st.title("Upload Your Resume")
    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        with st.spinner("Processing your resume..."):
            file_path = save_uploaded_file(uploaded_file)
            if file_path:
                try:
                    resume_data = process_resume(file_path)
                    st.session_state.resume_data = resume_data
                    st.success("Resume processed successfully!")
                    st.session_state.page = "portfolio"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing resume: {str(e)}")

def main():
    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    
    # Always check authentication status
    st.session_state.authenticated = is_authenticated()
    
    # Debug info
    print(f"Current page: {st.session_state.page}")
    print(f"Authenticated: {st.session_state.authenticated}")
    
    # Check if this is a password reset request
    if 'token' in st.query_params and st.query_params['token']:
        show_reset_password_page()
        return
    
    # Handle unauthenticated users
    if not st.session_state.authenticated:
        # Add landing page class and styles
        st.markdown(
            """
            <style>
                /* Reset Streamlit styles */
                .stApp {
                    padding: 0 !important;
                    margin: 0 !important;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                }
                
                .main .block-container {
                    padding: 0 !important;
                    max-width: 100% !important;
                }
                
                /* Hide Streamlit elements */
                .stApp > header,
                .stApp > footer,
                .stApp > .stAppToolbar,
                .stApp > .stDecoration {
                    display: none !important;
                }
                
                /* Ensure content starts below the fixed header */
                .main .block-container {
                    padding-top: 80px !important;
                }
                
                /* Style for login/signup forms */
                [data-testid="stAppViewBlockContainer"] {
                    max-width: 600px !important;
                    margin: 2rem auto !important;
                    padding: 2rem !important;
                    background: white !important;
                    border-radius: 16px !important;
                    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1) !important;
                }
            </style>
            <script>
                // Add landing page class to the app container
                document.documentElement.classList.add('landing-page');
                
                // Ensure the class stays applied during navigation
                const observer = new MutationObserver(function(mutations) {
                    if (!document.documentElement.classList.contains('landing-page')) {
                        document.documentElement.classList.add('landing-page');
                    }
                });
                
                observer.observe(document.documentElement, {
                    attributes: true,
                    attributeFilter: ['class']
                });
            </script>
            """,
            unsafe_allow_html=True
        )
        
        # Force a small delay to ensure styles are applied
        time.sleep(0.1)
        
        # Show the appropriate page
        if st.session_state.page == 'landing':
            show_landing_page()
        elif st.session_state.page == 'login':
            show_login_page()
        elif st.session_state.page == 'signup':
            st.session_state.page = 'login'  # Show login page with signup tab active
            show_login_page()
        else:
            st.session_state.page = 'landing'
            show_landing_page()
        return
    
    # For authenticated users, show the main app
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    # Get the current page from URL if available
    if 'page' in st.query_params:
        page_from_url = st.query_params['page']
        if page_from_url != st.session_state.page:
            st.session_state.page = page_from_url
    
    # Show header on all authenticated pages
    show_header()
    
    # Route to the appropriate page
    if st.session_state.page == 'home':
        show_home_page()
    elif st.session_state.page == 'upload':
        show_upload_page()
    elif st.session_state.page == 'portfolio':
        show_portfolio_page()
    elif st.session_state.page == 'cv-generator':
        from src.pages.Resume.generators.cv_generator import show_cv_generator
        show_cv_generator()
    elif st.session_state.page == 'cover-letter':
        from src.pages.Resume.generators.cover_letter_generator import show_cover_letter_generator
        show_cover_letter_generator()
    elif st.session_state.page == 'resume-optimizer':
        from src.pages.Resume.resume_optimizer import show_resume_optimizer
        show_resume_optimizer()
    elif st.session_state.page == 'portfolio-generator':
        from src.pages.Portfolio.generators.portfolio_generator import show_portfolio_generator
        show_portfolio_generator()
    else:
        # Default to home if page is not recognized
        st.session_state.page = 'home'
        st.rerun()

def show_portfolio_page():
    st.title("🎨 Your Portfolio")
    
    # Navigation in the sidebar
    st.sidebar.title("Navigation")
    if st.sidebar.button("← Back to Home"):
        st.session_state.page = "landing"
        st.rerun()
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "home"
        st.rerun()
    if st.sidebar.button("Upload Resume"):
        st.session_state.page = "upload"
        st.rerun()
    
    # Get portfolio ID from session state
    portfolio_id = st.session_state.get("portfolio_id")
    
    # Action buttons at the top
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Regenerate", help="Generate a new portfolio from scratch"):
            st.session_state.page = "upload"
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit Details", help="Edit your portfolio information"):
            st.session_state.editing = not st.session_state.get('editing', False)
            st.rerun()
    
    st.markdown("---")
    
    # Edit Mode
    if st.session_state.get('editing', False):
        st.subheader("✏️ Edit Your Portfolio")
        
        # Create a form for editing
        with st.form("edit_portfolio"):
            # Basic Information
            st.markdown("### Basic Information")
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name", value=st.session_state.portfolio_data.get('name', ''))
                email = st.text_input("Email", value=st.session_state.portfolio_data.get('email', ''))
                phone = st.text_input("Phone", value=st.session_state.portfolio_data.get('phone', ''))
            with cols[1]:
                title = st.text_input("Professional Title", value=st.session_state.portfolio_data.get('title', ''))
                location = st.text_input("Location", value=st.session_state.portfolio_data.get('location', ''))
            
            # Social Links
            st.markdown("### Social Links")
            social_cols = st.columns(2)
            with social_cols[0]:
                linkedin = st.text_input("LinkedIn", value=st.session_state.portfolio_data.get('linkedin', ''))
                github = st.text_input("GitHub", value=st.session_state.portfolio_data.get('github', ''))
            with social_cols[1]:
                twitter = st.text_input("Twitter", value=st.session_state.portfolio_data.get('twitter', ''))
                website = st.text_input("Website", value=st.session_state.portfolio_data.get('website', ''))
            
            # Summary
            st.markdown("### Professional Summary")
            summary = st.text_area("Summary", value=st.session_state.portfolio_data.get('summary', ''), height=100)
            
            # Form actions
            form_col1, form_col2 = st.columns([1, 3])
            with form_col1:
                if st.form_submit_button("💾 Save Changes"):
                    # Update session state with edited values
                    st.session_state.portfolio_data.update({
                        'name': name,
                        'title': title,
                        'email': email,
                        'phone': phone,
                        'location': location,
                        'linkedin': linkedin,
                        'github': github,
                        'twitter': twitter,
                        'website': website,
                        'summary': summary
                    })
                    
                    # Regenerate portfolio with updated data
                    with st.spinner("Updating your portfolio..."):
                        portfolio_result = generate_portfolio(st.session_state.portfolio_data)
                        if "error" not in portfolio_result:
                            st.session_state.portfolio_content = portfolio_result
                            st.session_state.editing = False
                            st.rerun()
            
            with form_col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.editing = False
                    st.rerun()
    
    # Display Mode
    else:
        # Portfolio Preview Section
        st.markdown("## Preview")
        
        if not portfolio_id:
            st.warning("No portfolio ID found. Please generate a new portfolio.")
            st.session_state.page = "upload"
            st.rerun()
        
        # Show portfolio preview in an iframe
        with st.spinner("Loading your portfolio..."):
            try:
                # Get the portfolio preview URL
                preview_url = f"http://localhost:8000/api/portfolio/preview/{portfolio_id}"
                
                # Display the portfolio in an iframe for preview
                st.components.v1.iframe(
                    preview_url,
                    height=800,
                    scrolling=True
                )
                
            except Exception as e:
                st.error(f"Error loading portfolio preview: {str(e)}")
                st.warning("Please make sure the backend server is running and accessible.")
                return
        
        # Download and Export Options
        st.markdown("---")
        st.markdown("### Download & Export")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download HTML
            if st.button("💾 Download HTML"):
                with st.spinner("Preparing HTML download..."):
                    try:
                        html_content = APIService.download_file(portfolio_id, "portfolio", token)
                        if html_content:
                            st.download_button(
                                label="⬇️ Save HTML",
                                data=html_content,
                                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.html",
                                mime="text/html"
                            )
                    except Exception as e:
                        st.error(f"Error downloading HTML: {str(e)}")
        
        with col2:
            # Export as PDF
            if st.button("📄 Export as PDF"):
                with st.spinner("Generating PDF..."):
                    try:
                        pdf_content = APIService.download_file(
                            f"{portfolio_id}?format=pdf", 
                            "portfolio", 
                            token
                        )
                        if pdf_content:
                            st.download_button(
                                label="⬇️ Save PDF",
                                data=pdf_content,
                                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
        
        with col3:
            # Raw data
            if st.button("📊 View Raw Data"):
                st.json(st.session_state.portfolio_data)
        
        # Single Back to Home button at the bottom
        if st.button("🏠 Back to Home", type="secondary"):
            st.session_state.page = "home"
            st.rerun()

if __name__ == "__main__":
    main()
