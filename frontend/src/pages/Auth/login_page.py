import streamlit as st
from src.pages.Auth.auth import login, signup, reset_password, is_authenticated
import time

def show_login_page():
    """Display the login/signup form with tabbed interface."""
    st.markdown(
        """
        <style>
            /* Base styles */
            * {
                color: #000000 !important;
            }
            
            .login-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 5%;
                background: #ffffff !important;
                border-bottom: 1px solid #e0e0e0;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                margin: -1.5rem -1.5rem 2rem -1.5rem;
            }
            
            /* Style the form container */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                padding: 0 24px;
                margin-right: 0;
                border-radius: 8px 8px 0 0;
                background-color: #f5f5f5;
                color: #666;
            }
            
            .stTabs [aria-selected="true"] {
                background-color: white;
                color: #000;
                font-weight: 600;
            }
            
            [data-testid="stAppViewBlockContainer"] {
                max-width: 600px;
                margin: 0 auto;
                padding: 2rem;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
                margin-top: 2rem;
            }
            
            /* Input fields */
            .stTextInput > div > div > input,
            .stTextInput > div > div > input:focus,
            .stTextInput > div > div > input:active,
            .stTextInput > div > div > input:hover,
            .stTextInput > div > div > input:not(:placeholder-shown) {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 1px solid #000000 !important;
                border-radius: 8px !important;
                padding: 0.5rem 1rem !important;
            }
            
            /* Labels */
            .stTextInput > label,
            .stTextInput > div > label,
            .stTextInput > div > div > label,
            .stTextInput > div > div > div > label {
                color: #000000 !important;
                font-weight: 500 !important;
            }
            
            /* -------------------------
               Button overrides - Using !important and high specificity
               to override any other styles including those in app.py
            */
            html body div[data-testid="stAppViewContainer"] div[data-testid="stForm"] .stButton > button,
            html body div[data-testid="stAppViewContainer"] div[data-testid="stForm"] .stButton > button:link,
            html body div[data-testid="stAppViewContainer"] div[data-testid="stForm"] .stButton > button:visited,
            html body div[data-testid="stAppViewContainer"] div[data-testid="stForm"] .stButton > button:hover,
            html body div[data-testid="stAppViewContainer"] div[data-testid="stForm"] .stButton > button:active,
            html body div[data-testid="stAppViewContainer"] div[data-testid="stForm"] .stButton > button:focus {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
                font-weight: 700 !important;
                border-radius: 8px !important;
                padding: 0.75rem 1.5rem !important;
                transition: all 0.2s ease !important;
                cursor: pointer !important;
                width: 100% !important;
                margin-top: 1.5rem !important;
                font-size: 1rem !important;
                text-transform: none !important;
                --text-color: #000000 !important;
                --text: #000000 !important;
            }
            
            /* Hover state */
            body div[data-testid="stAppViewContainer"] .stButton > button:hover {
                background-color: #f0f0f0 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            }
            
            /* Active/Focus state */
            body div[data-testid="stAppViewContainer"] .stButton > button:active,
            body div[data-testid="stAppViewContainer"] .stButton > button:focus {
                transform: translateY(0) !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
                background-color: #e0e0e0 !important;
                outline: none !important;
            }
            
            /* -------------------------------------------------------------------
               Button overrides (Login / Sign Up / Reset Password)
               -------------------------------------------------------------------
               We target the DIV that Streamlit wraps around any st.form_submit_button,
               namely: div[data-testid="stFormSubmitButton"] (not ".stButton").
            */
            /* Normal, link, visited, hover, active, focus states */
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button,
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:link,
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:visited,
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:hover,
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:active,
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:focus {
                background-color: #ffffff !important;   /* white background */
                color: #000000 !important;               /* black text */
                border: 2px solid #000000 !important;    /* black border */
                font-weight: 700 !important;
                border-radius: 8px !important;
                padding: 0.75rem 1.5rem !important;
                transition: all 0.2s ease !important;
                cursor: pointer !important;
                width: 100% !important;
                margin-top: 1.5rem !important;
                font-size: 1rem !important;
                text-transform: none !important;
            }

            /* Hover state: slightly grey on hover */
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:hover {
                background-color: #f0f0f0 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            }

            /* Active/Focus state: slightly darker grey when pressed or focused */
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:active,
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button:focus {
                transform: translateY(0) !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
                background-color: #e0e0e0 !important;
                outline: none !important;
            }

            /* Force all child text (spans, paragraphs, etc.) inside those buttons to be black */
            div[data-testid="stAppViewContainer"]
              div[data-testid="stFormSubmitButton"] button * {
                color: #000000 !important;
            }
            
            .logo {
                font-size: 1.75rem;
                font-weight: 700;
                color: #000000 !important;
                text-decoration: none;
                letter-spacing: -0.5px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            .logo span {
                color: #000000 !important;
                font-weight: 800;
            }
        </style>
        <div class="login-header">
            <a href="/" class="logo">Portfolio<span>AI</span></a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # (…rest of your Python code remains exactly as before…)
    # You still have three tabs: Login, Sign Up, Reset Password, each with its own form.

    tab_titles = ["Login", "Sign Up", "Reset Password"]
    if 'page' in st.session_state and st.session_state.page == 'signup':
        default_index = 1
        st.session_state.page = 'login'
    else:
        default_index = 0

    login_tab, signup_tab, reset_tab = st.tabs(tab_titles)

    with login_tab:
        st.markdown("### Welcome back!")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit_button = st.form_submit_button(
                "Login", 
                type="secondary",  # Uses our custom styling above
                help="Sign in to your account"
            )

            if submit_button:
                with st.spinner("Signing in..."):
                    if login(email, password):
                        st.session_state.is_authenticated = True
                        st.session_state.page = 'home'
                        st.rerun()
                    else:
                        st.error("Invalid email or password")

    with signup_tab:
        st.markdown("<h3 style='margin-top: 0; padding-top: 0;'>Create Your Account</h3>", unsafe_allow_html=True)
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="signup_first_name")
            with col2:
                last_name = st.text_input("Last Name", key="signup_last_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            submit_button = st.form_submit_button(
                "Sign Up",
                type="secondary",  # Uses our custom styling above
                help="Create a new account"
            )

            if submit_button:
                if not first_name or not last_name:
                    st.error("Please enter both first and last name")
                elif password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    full_name = f"{first_name} {last_name}"
                    if signup(email, password, full_name):
                        st.success("Account created! Please check your email to verify your account.")

    with reset_tab:
        st.markdown("### Reset Password")
        with st.form("reset_form"):
            email = st.text_input("Email", key="reset_email")
            submit_button = st.form_submit_button(
                "Send Reset Link",
                type="secondary",  # Uses our custom styling above
                help="Send password reset instructions"
            )

            if submit_button:
                if reset_password(email):
                    st.success("If an account exists with this email, you'll receive a password reset link.")