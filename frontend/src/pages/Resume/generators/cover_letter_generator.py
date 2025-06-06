import streamlit as st
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import json
import requests
import io

# For file processing
from PyPDF2 import PdfReader
import docx

# Import API service
from src.services.api import APIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session state keys
COVER_LETTER_DATA = 'cl_letter_data'

# API endpoints
UPLOAD_RESUME_ENDPOINT = "/api/cover-letter/upload-resume"
GENERATE_COVER_LETTER_ENDPOINT = "/api/cover-letter/generate"
SAVE_COVER_LETTER_ENDPOINT = "/api/cover-letter/save"

def initialize_session_state():
    """Initialize session state for cover letter generator if not already done."""
    if COVER_LETTER_DATA not in st.session_state:
        st.session_state[COVER_LETTER_DATA] = {
            'resume_id': None,
            'job_title': '',
            'company_name': '',
            'job_description': '',
            'tone': 'Professional',
            'length': 'Medium',
            'cover_letter_text': '',
            'uploaded_resume': None
        }

def show_header():
    """Display the header with logo and logout button."""
    # Add custom CSS for consistent styling
    st.markdown("""
    <style>
        /* Global text color */
        body, .stTextInput > label, .stTextArea > label, .stMarkdown p, 
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
        
        /* Checkbox and radio button labels */
        .stCheckbox > label, .stRadio > label, 
        .stRadio > div > label, .stRadio > div > div > label,
        .stRadio > div > div > div > label,
        .stRadio > div > div > div > div > label {
            color: #000000 !important;
            font-weight: normal !important;
        }

        /* Force radio button label text to black */
        .stRadio label, 
        .stRadio div > div > label,
        .stRadio div > div > div > label {
            color: #000000 !important;
        }

        /* Force generate button text to white */
        button[data-testid="stFormSubmitButton"] > div > p {
            color: #ffffff !important;
        }
        
        /* Dialog styling */
        dialog {
            background-color: white;
            color: #000000;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        dialog::backdrop {
            background-color: rgba(0, 0, 0, 0.5);
        }
        
        dialog h3 {
            margin-top: 0;
            color: #000000 !important;
        }
        
        dialog textarea {
            width: 100%;
            min-height: 300px;
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: monospace;
            color: #000000;
        }
        
        dialog .dialog-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 15px;
        }
        
        dialog button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        
        dialog button.cancel {
            background-color: #f0f0f0;
            color: #333;
        }
        
        dialog button.save {
            background-color: #4f8bf9;
            color: white;
        }
        
        dialog button:hover {
            opacity: 0.9;
        }
        
        /* Radio button circle and text */
        .stRadio > div > div > div > div > div > div {
            border-color: #000000 !important;
        }
        /* Radio button label text color */
        .stRadio > label > div:first-child > div {
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
        
        /* Cover letter preview */
        .cover-letter-preview {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 1rem;
            min-height: 300px;
            white-space: pre-line;
            background-color: #f9f9f9;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Add JavaScript for the edit dialog
    st.markdown(
        """
        <script>
        // Check if the function is already defined
        if (typeof window.saveEditedLetter === 'undefined') {
            // Initialize the textarea with current content when dialog opens
            document.addEventListener('DOMContentLoaded', function() {
                const editDialog = document.getElementById('edit-letter');
                if (editDialog) {
                    editDialog.addEventListener('show', function() {
                        const content = document.getElementById('cover-letter-content')?.innerText || '';
                        const editor = document.getElementById('edited-letter');
                        if (editor) editor.value = content;
                    });
                }
            });
            
            // Function to save edited content
            window.saveEditedLetter = function() {
                const editor = document.getElementById('edited-letter');
                const content = editor ? editor.value : '';
                const preview = document.getElementById('cover-letter-content');
                
                if (preview) {
                    // Update the displayed content with proper line breaks
                    preview.innerHTML = content.replace(/\n/g, '<br>');
                }
                
                // Close the dialog
                const dialog = document.getElementById('edit-letter');
                if (dialog) dialog.close();
                
                // Update the session state via Streamlit
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/_stcore/upload_file', true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.send(JSON.stringify({
                    'cover_letter_text': content,
                    'session_id': document.querySelector('script[data-testid="stMarkdownContainer"]')?.getAttribute('data-session-id') || ''
                }));
            };
        }
        </script>
        """,
        unsafe_allow_html=True
    )
    


def upload_resume(file) -> Optional[str]:
    """
    Process an uploaded resume file and extract its text content.
    
    Args:
        file: The uploaded file object from Streamlit
        
    Returns:
        str: The extracted text content if successful, None otherwise
    """
    if file is None:
        return None
    
    # Get file extension and validate it
    file_ext = Path(file.name).suffix.lower()
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
    
    if file_ext not in allowed_extensions:
        error_msg = f"File type {file_ext} not supported. Please upload a PDF, DOCX, or TXT file."
        logger.error(error_msg)
        st.error(error_msg)
        return None
    
    try:
        with st.spinner("Processing your resume..."):
            logger.info(f"Processing uploaded file: {file.name} (type: {file.type if hasattr(file, 'type') else 'unknown'})")
            
            # Read the file content
            try:
                file_content = file.getvalue()
                
                # Extract text from the file based on its type
                resume_text = ""
                if file_ext == '.pdf':
                    logger.info("Extracting text from PDF file")
                    pdf_reader = PdfReader(io.BytesIO(file_content))
                    resume_text = "\n\n".join([page.extract_text() for page in pdf_reader.pages])
                    logger.info(f"Extracted {len(resume_text)} characters from PDF")
                elif file_ext in ['.docx', '.doc']:
                    logger.info("Extracting text from Word document")
                    doc = docx.Document(io.BytesIO(file_content))
                    resume_text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                    logger.info(f"Extracted {len(resume_text)} characters from Word document")
                else:  # txt file
                    logger.info("Reading text file content")
                    resume_text = file_content.decode("utf-8")
                    logger.info(f"Read {len(resume_text)} characters from text file")
                
                # Clean up the extracted text
                resume_text = resume_text.strip()
                
                # Validate resume text
                if not resume_text:
                    error_msg = "The uploaded file appears to be empty or couldn't be read."
                    logger.warning(error_msg)
                    st.error(error_msg)
                    return None
                    
                if len(resume_text) < 50:
                    error_msg = f"The uploaded file doesn't contain enough text. Only found {len(resume_text)} characters."
                    logger.warning(error_msg)
                    st.error(error_msg)
                    return None
                    
                # Store the resume text in session state
                if COVER_LETTER_DATA not in st.session_state:
                    st.session_state[COVER_LETTER_DATA] = {}
                    
                st.session_state[COVER_LETTER_DATA]['resume_text'] = resume_text
                st.session_state[COVER_LETTER_DATA]['resume_uploaded'] = True
                
                logger.info("Successfully processed resume")
                return resume_text
                
            except Exception as e:
                error_msg = f"Error reading file: {str(e)}"
                logger.error(error_msg, exc_info=True)
                st.error("Failed to process the uploaded file. Please try again with a different file.")
                return None
                
    except Exception as e:
        error_msg = f"Unexpected error during file upload: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error("An unexpected error occurred. Please try again later.")
        return None
                
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None

def generate_cover_letter(data: Dict) -> Optional[str]:
    """Generate a cover letter using the backend API.
    
    Args:
        data: Dictionary containing:
            - resume_text: The text content of the resume
            - job_description: The job description to target
            - tone: The desired tone (professional, friendly, formal, enthusiastic)
    """
    try:
        with st.spinner("Generating cover letter..."):
            # Prepare the request data in the format expected by the backend
            request_data = {
                'resume_text': data.get('resume_text', ''),
                'job_description': data.get('job_description', ''),
                'tone': data.get('tone', 'professional').lower()
            }
            
            # Log the request data for debugging
            logger.info(f"Sending cover letter generation request: {request_data}")
            
            # Use APIService to generate the cover letter
            response = APIService.generate_cover_letter(request_data)
            
            # Log the full response for debugging
            logger.info(f"Cover letter generation response: {response}")
            
            # The response is the cover letter text directly, not wrapped in a 'status' field
            if response and isinstance(response, dict) and 'cover_letter' in response:
                cover_letter = response['cover_letter']
                # Update session state with the generated cover letter
                if COVER_LETTER_DATA not in st.session_state:
                    st.session_state[COVER_LETTER_DATA] = {}
                st.session_state[COVER_LETTER_DATA]['cover_letter_text'] = cover_letter
                return cover_letter
            else:
                error_msg = "Generated cover letter is empty or in an unexpected format"
                if isinstance(response, dict) and 'message' in response:
                    error_msg = response['message']
                logger.error(f"Cover letter generation error: {error_msg}. Response: {response}")
                st.error(f"Failed to generate cover letter: {error_msg}")
                return None
    except Exception as e:
        error_msg = f"Failed to generate cover letter: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg, exc_info=True)
        return None

def save_cover_letter(data: Dict) -> bool:
    """Save the generated cover letter."""
    try:
        with st.spinner("Saving cover letter..."):
            # Prepare the data for saving
            save_data = {
                'cover_letter_text': data.get('cover_letter_text', ''),
                'job_title': data.get('job_title', ''),
                'company_name': data.get('company_name', ''),
                'job_description': data.get('job_description', '')
            }
            
            # Use APIService to save the cover letter
            response = APIService._make_request(
                "POST",
                SAVE_COVER_LETTER_ENDPOINT,
                json=save_data
            )
            
            if isinstance(response, dict) and response.get("status") == "success":
                return True
            else:
                error_msg = response.get("message", "Failed to save cover letter")
                st.error(f"Failed to save cover letter: {error_msg}")
                logger.error(f"Failed to save cover letter: {error_msg}")
                return False
    except Exception as e:
        error_msg = f"Failed to save cover letter: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg, exc_info=True)
        return False

def show_cover_letter_form():
    """Display the cover letter generation form and preview in a single view."""
    # Add custom CSS for form elements
    st.markdown("""
    <style>
        /* Target all radio button text */
        .stRadio > div, .stRadio label {
            color: #000000 !important;
        }
        /* Target selected radio button text */
        .stRadio > div[data-baseweb="radio"] > div > div {
            color: #000000 !important;
        }
        /* File uploader styling */
        .stFileUploader > div > div > div > button {
            background-color: #4f8bf9;
            color: white !important;
        }
        /* Preview section styling */
        .cover-letter-preview {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 1.5rem;
            margin-top: 1rem;
            background-color: #f9f9f9;
            white-space: pre-line;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### Cover Letter Generator")
    
    # Initialize session state for form data if not exists
    if COVER_LETTER_DATA not in st.session_state:
        st.session_state[COVER_LETTER_DATA] = {}
    
    # Create two columns for the layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # File uploader section
        st.markdown("#### 1. Upload Resume")
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "doc", "txt"],
            key="resume_uploader",
            help="Upload your resume in PDF, DOCX, or TXT format (max 5MB)",
            accept_multiple_files=False
        )
        
        # Process file upload when a file is selected
        if uploaded_file is not None:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if uploaded_file.size > max_size:
                st.error("File size too large. Please upload a file smaller than 5MB.")
            else:
                with st.spinner("Processing resume..."):
                    try:
                        resume_text = upload_resume(uploaded_file)
                        if resume_text:
                            st.session_state[COVER_LETTER_DATA].update({
                                'uploaded_resume': uploaded_file.name,
                                'resume_processed': True,
                                'resume_text': resume_text
                            })
                            st.success("✅ Resume processed successfully!")
                        else:
                            st.error("Failed to process resume. The file might be empty or corrupted.")
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
                        logger.error(f"Error in resume processing: {str(e)}")
        
        # Only show the form if resume is processed
        if st.session_state.get(COVER_LETTER_DATA, {}).get('resume_processed'):
            # Create the form
            with st.form("cover_letter_form"):
                st.markdown("#### 2. Job Details")
                
                # Job details form fields
                job_title = st.text_input(
                    "Job Title*",
                    value=st.session_state.get(COVER_LETTER_DATA, {}).get('job_title', ''),
                    key="job_title"
                )
                
                company_name = st.text_input(
                    "Company Name*",
                    value=st.session_state.get(COVER_LETTER_DATA, {}).get('company_name', ''),
                    key="company_name"
                )
                
                job_description = st.text_area(
                    "Job Description*",
                    value=st.session_state.get(COVER_LETTER_DATA, {}).get('job_description', ''),
                    help="Paste the job description to help generate a tailored cover letter",
                    key="job_description"
                )
                
                # Customization options
                st.markdown("#### 3. Customization (Optional)")
                
                # Create two columns for layout
                col1_inner, col2_inner = st.columns(2)
                
                with col1_inner:
                    tone = st.selectbox(
                        "Tone*",
                        ["Professional", "Friendly", "Concise"],
                        index=["Professional", "Friendly", "Concise"].index(
                            st.session_state.get(COVER_LETTER_DATA, {}).get('tone', 'Professional')
                        ),
                        key="tone"
                    )
                    
                    hiring_manager = st.text_input(
                        "Hiring Manager's Name (Optional)",
                        value=st.session_state.get(COVER_LETTER_DATA, {}).get('hiring_manager', ''),
                        key="hiring_manager"
                    )
                
                with col2_inner:
                    length = st.selectbox(
                        "Length*",
                        ["Short (200-300 words)", "Medium (300-400 words)", "Long (400-500 words)"],
                        index=1,  # Default to Medium
                        key="length"
                    )
                    
                    job_reference = st.text_input(
                        "Job Reference/ID (Optional)",
                        value=st.session_state.get(COVER_LETTER_DATA, {}).get('job_reference', ''),
                        key="job_reference"
                    )
                
                # Add some space before the button
                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                
                # Submit button at the bottom of the form
                submitted = st.form_submit_button("Generate Cover Letter")
                
                # Only process the form when it's submitted
                if submitted:
                    # Validate required fields
                    if not job_title or not company_name or not job_description.strip():
                        st.error("Please fill in all required fields (marked with *)")
                    else:
                        with st.spinner("Generating your cover letter..."):
                            try:
                                # Prepare data for API
                                # Include company name and job title in the job description
                                enhanced_job_description = f"""
                                Job Title: {job_title}
                                Company: {company_name}
                                
                                Job Description:
                                {job_description}
                                
                                Additional Information:
                                """
                                
                                if hiring_manager:
                                    enhanced_job_description += f"Hiring Manager: {hiring_manager}\n"
                                if job_reference:
                                    enhanced_job_description += f"Job Reference: {job_reference}\n"
                                
                                # Prepare the data in the format expected by the backend
                                data = {
                                    "resume_text": st.session_state[COVER_LETTER_DATA].get('resume_text', ''),
                                    "job_description": enhanced_job_description.strip(),
                                    "tone": tone.lower().split()[0]  # Get the first word (e.g., "Professional" -> "professional")
                                }
                                
                                # Generate cover letter
                                cover_letter_text = generate_cover_letter(data)
                                
                                if cover_letter_text:
                                    # Update session state with new data
                                    st.session_state[COVER_LETTER_DATA].update({
                                        'cover_letter_text': cover_letter_text,
                                        'job_title': job_title,
                                        'company_name': company_name,
                                        'job_description': job_description,
                                        'tone': tone,
                                        'length': length,
                                        'hiring_manager': hiring_manager,
                                        'job_reference': job_reference,
                                        'show_preview': True
                                    })
                                else:
                                    st.error("Failed to generate cover letter. Please try again.")
                                    
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                                logger.error(f"Error generating cover letter: {str(e)}")
    
    with col2:
        # Show preview section
        if st.session_state.get(COVER_LETTER_DATA, {}).get('show_preview'):
            st.markdown("#### Cover Letter Preview")
            
            # Display the generated cover letter
            cover_letter_text = st.session_state[COVER_LETTER_DATA].get('cover_letter_text', '')
            if cover_letter_text:
                # Add edit and copy buttons
                st.markdown("""
                <div style="margin-bottom: 1rem; display: flex; gap: 0.5rem;">
                    <button onclick="document.getElementById('edit-letter').showModal()" class="css-1x8cf1d edgvbvh10" style="margin-right: 0.5rem;">
                        Edit
                    </button>
                    <button onclick="navigator.clipboard.writeText(document.getElementById('cover-letter-content').innerText)" class="css-1x8cf1d edgvbvh10">
                        Copy to Clipboard
                    </button>
                </div>
                """, unsafe_allow_html=True)
                
                # Display the cover letter in a scrollable container
                st.markdown(
                    f"""
                    <div id="cover-letter-content" class="cover-letter-preview" style="max-height: 600px; overflow-y: auto; white-space: pre-line;">
                        {cover_letter_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Add edit dialog
                st.markdown("""
                <dialog id="edit-letter">
                    <h3>Edit Cover Letter</h3>
                    <textarea id="edited-letter"></textarea>
                    <div class="dialog-buttons">
                        <button onclick="document.getElementById('edit-letter').close()" class="cancel">Cancel</button>
                        <button onclick="saveEditedLetter()" class="save">Save Changes</button>
                    </div>
                </dialog>
                """, unsafe_allow_html=True)
                
                # Add download button
                st.download_button(
                    label="Download as DOCX",
                    data=cover_letter_text.encode('utf-8'),
                    file_name=f"cover_letter_{st.session_state[COVER_LETTER_DATA].get('company_name', 'company').lower().replace(' ', '_')}.txt",
                    mime="text/plain"
                )

def show_cover_letter_generator():
    """Main function to display the cover letter generator."""
    initialize_session_state()
    show_header()
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        st.warning("Please log in to access the cover letter generator.")
        return
    
    # Show the cover letter form which includes the preview
    show_cover_letter_form()

# This allows the file to be run directly for testing
if __name__ == "__main__":
    show_cover_letter_generator()
