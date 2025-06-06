import streamlit as st
from pathlib import Path
import base64
from typing import Optional
import sys

# This flag is used to check if this module is being imported or run directly
IS_RUNNING_DIRECTLY = not hasattr(st, '_is_running_with_streamlit') or st._is_running_with_streamlit

def inject_landing_css():
    """Inject custom CSS for the landing page"""
    st.markdown("""
    <style>
        /* Import font first */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
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
        
        /* Landing page specific styles */
        .landing-page {
            --primary-color: #000000;
            --secondary-color: #0066cc;
            --text-color: #333;
            --light-gray: #f9fafb;
            --border-radius: 12px;
            --box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        /* Ensure content starts below the fixed header */
        .landing-page .main .block-container {
            padding-top: 80px !important;
        }
        
        /* Hide Streamlit elements */
        .stApp > header,
        .stApp > footer,
        .stApp > .stAppToolbar,
        .stApp > .stDecoration {
            display: none !important;
        }
        
        /* Landing page specific styles */
        .landing-page {
            --primary-color: #4f46e5;
            --secondary-color: #7c3aed;
            --text-color: #333;
            --light-gray: #f9fafb;
            --border-radius: 12px;
            --box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        /* Hide Streamlit elements */
        .landing-page .main .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        .landing-page .stApp {
            background: #ffffff;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
        }
        
        /* Override Streamlit's default styles */
        .landing-page .stApp > header {
            display: none !important;
        }
        
        .landing-page .stApp > footer {
            display: none !important;
        }
        
        .landing-page .stApp > .reportview-container {
            padding: 0 !important;
        }
        padding-top: 80px; /* Add padding to account for fixed header */
    }
    
    /* Header styles */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 5%;
        background: rgba(255, 255, 255, 0.95);
        border-bottom: 1px solid #eee;
        position: fixed;
        width: 100%;
        left: 0;
        top: 0;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        max-width: 2000px;
        margin: 0 auto;
        box-sizing: border-box;
    }
    
    .logo {
        font-size: 1.75rem;
        font-weight: 700;
        text-decoration: none;
        letter-spacing: -0.5px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        display: flex;
        align-items: center;
    }
    .logo span {
        color: #0066cc; /* Blue color for 'AI' */
    }
    
    /* Header buttons */
    .header-buttons {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .header-button {
        padding: 0.5rem 1.25rem;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.9375rem;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        border: 1.5px solid transparent;
    }
    
    .header-button.login {
        color: #1a1a1a;
        background: transparent;
        border-color: #e2e8f0;
    }
    
    .header-button.signup {
        background: #2563eb;
        color: white;
    }
    
    .header-button.login:hover {
        background: #f8fafc;
    }
    
    .header-button.signup:hover {
        background: #1d4ed8;
    }
    
    .nav-buttons {
        display: flex;
        gap: 1rem;
    }
    
    .btn {
        padding: 0.625rem 1.25rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        font-size: 0.9375rem;
        transition: all 0.2s ease;
    }
    
    .btn-outline, .btn-primary {
        border: 2px solid #000;
        color: #000;
        background: #fff;
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
    }
    
    .btn-outline:hover, .btn-primary:hover {
        background: #f5f5f5;
        color: #000;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Hero section */
    .hero {
        text-align: center;
        padding: 6rem 2rem;
        background: #fafafa;
        position: relative;
        overflow: hidden;
        margin-top: -80px; /* Compensate for fixed header */
        padding-top: 10rem; /* Add more top padding */
    }
    
    .hero::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #ddd, transparent);
    }
    
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1.2;
        margin: 0 auto 2rem;
        max-width: 900px;
        color: #000;
        letter-spacing: -1px;
    }
    
    /* Main container width */
    .st-emotion-cache-1w723zb {
        max-width: 2000px !important;
        margin: 0 auto;
    }
    
    .hero p {
        font-size: 1.25rem;
        color: #666;
        max-width: 700px;
        margin: 0 auto 3rem;
        font-weight: 400;
        line-height: 1.8;
    }
    
    .hero-cta {
        font-size: 1.125rem;
        padding: 0.875rem 2rem;
        border-radius: 8px;
    }
    
    /* Features section */
    .features {
        padding: 6rem 5%;
        background: #fff;
        position: relative;
    }
    
    .section-title {
        text-align: center;
        font-size: 2.25rem;
        font-weight: 700;
        margin-bottom: 3rem;
        color: #111827;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .feature-card {
        background: #fff;
        border-radius: 0;
        padding: 2.5rem 2rem;
        border: 1px solid #eee;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #000;
        transform: scaleY(0);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover::before {
        transform: scaleY(1);
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    .feature-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 2rem;
        background: #f5f5f5;
        color: #000;
        font-size: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover .feature-icon {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }
    
    .feature-title {
        font-size: 1.375rem;
        font-weight: 600;
        margin-bottom: 1.25rem;
        color: #000;
        position: relative;
        display: inline-block;
    }
  
    .feature-description {
        color: #666;
        line-height: 1.8;
        font-size: 1.05rem;
    }
    
    /* Why Section Styles */
    .why-section {
        padding: 5rem 5%;
        background-color: #f8f9fa;
    }
    
    .why-container {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .section-title {
        text-align: center;
        font-size: 2.5rem;
        color: #2c3e50;
        margin-bottom: 3rem;
        font-weight: 700;
    }
    
    .problem-benefit-pair {
        background: white;
        border-radius: 10px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .problem-benefit-pair:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    
    .problem {
        font-size: 1.25rem;
        font-weight: 600;
        color: #e74c3c;
        margin-bottom: 1rem;
        position: relative;
        padding-left: 1.5rem;
    }
    
    .problem:before {
        content: '!';
        position: absolute;
        left: 0;
        top: 0;
        color: #e74c3c;
        font-weight: bold;
    }
    
    .benefit {
        font-size: 1.1rem;
        color: #2c3e50;
        line-height: 1.7;
        margin: 0;
    }
    
    /* Why PortfolioAI Section */
    .why-section {
        padding: 6rem 5%;
        background: #fafafa;
        position: relative;
    }
    
    .why-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #ddd, transparent);
    }
    
    .why-container {
        max-width: 800px;
        margin: 0 auto;
        text-align: center;
    }
    
    .section-title {
        font-size: 2.25rem;
        font-weight: 700;
        margin-bottom: 3rem;
        color: #000;
        position: relative;
        display: inline-block;
        text-align: center;
        width: 100%;
    }
    
    .problem-benefit-pair {
        margin-bottom: 2rem;
        padding: 2rem;
        border: 1px solid #eee;
        border-radius: 8px;
        background: #fff;
        transition: all 0.3s ease;
        text-align: left;
        box-shadow: 0 2px 15px rgba(0,0,0,0.03);
    }
    
    .problem-benefit-pair:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    
    .problem {
        color: #000;
        font-weight: 700;
        font-size: 1.375rem;
        margin-bottom: 1.5rem;
        line-height: 1.4;
    }
    
    .benefit {
        color: #444;
        line-height: 1.8;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Footer */
    .footer {
        background: #000;
        padding: 6rem 5% 3rem;
        color: #fff;
        position: relative;
    }
    
    .footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #444, transparent);
    }
    
    .footer-content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .footer-section h4 {
        color: #fff;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .footer-section p, .footer-section a {
        color: #aaa;
        margin-bottom: 1rem;
        display: block;
        text-decoration: none;
        transition: all 0.3s ease;
        font-size: 0.95rem;
    }
    
    .footer-section a:hover {
        color: #fff;
        padding-left: 5px;
    }
    
    .social-links {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .copyright {
        text-align: center;
        margin-top: 5rem;
        padding-top: 2rem;
        border-top: 1px solid #333;
        color: #777;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero h1 {
            font-size: 2.25rem;
        }
        
        .hero p {
            font-size: 1.125rem;
        }
        
        .features-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Custom styles for signup form */
    .stForm {
        background: #fff;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def show_header():
    """Render the header with logo and navigation buttons."""
    # Add header styles
    st.markdown(
        """
        <style>
            .header-container {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                background: white;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                padding: 10px 5%;
                margin: 0;
                width: 100%;
                box-sizing: border-box;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .logo {
                font-size: 1.5rem;
                font-weight: 700;
                color: #000;
                text-decoration: none;
                letter-spacing: -0.5px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            .logo span {
                color: #0066cc;
            }
            .header-buttons {
                display: flex;
                gap: 16px;
                align-items: center;
            }
            .stButton > button {
                padding: 8px 24px !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
                min-width: 100px !important;
                transition: all 0.2s ease !important;
                cursor: pointer !important;
            }
            .stButton > button:first-child {
                background: transparent !important;
                color: #000 !important;
                border: 1px solid #000 !important;
            }
            .stButton > button:first-child:hover {
                background: #f5f5f5 !important;
                border-color: #000 !important;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            .stButton > button:last-child {
                background: #0066cc !important;
                color: white !important;
                border: 1px solid #0066cc !important;
            }
            .stButton > button:last-child:hover {
                background: #0052a3 !important;
                border-color: #0052a3 !important;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0, 102, 204, 0.3);
            }
            .main .block-container {
                padding-top: 80px !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Create a container for the header
    header = st.container()
    with header:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(
                """
                <a href="/" class="logo">Portfolio<span>AI</span></a>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            # Create the buttons using Streamlit
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Log In", key="header_login_btn", type="secondary"):
                    st.session_state.page = 'login'
                    st.rerun()
            with btn_col2:
                if st.button("Sign Up", key="header_signup_btn", type="primary"):
                    st.session_state.page = 'signup'
                    st.rerun()
    
    # Add some spacing below the header
    st.markdown("<div style='margin-top: 80px;'></div>", unsafe_allow_html=True)
    
    # Add some CSS to ensure the header is properly positioned
    st.markdown(
        """
        <style>
        /* Main content container */
        .main .block-container {
            padding-top: 80px !important;
        }
        
        /* Header container */
        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: white;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 10px 5%;
            margin: 0;
            width: 100%;
            box-sizing: border-box;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        /* Logo styling */
        .logo {
            font-size: 1.75rem;
            font-weight: 700;
            color: #000;
            text-decoration: none;
            letter-spacing: -0.5px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .logo span {
            color: #0066cc;
        }
        
        /* Header buttons container */
        .header-buttons {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        /* Button base styles */
        .login-btn,
        .signup-btn {
            padding: 8px 20px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Login button */
        .login-btn {
            background: transparent;
            color: #333;
            border: 1px solid #ddd;
        }
        
        .login-btn:hover {
            background: #f8f8f8;
            border-color: #ccc;
        }
        
        /* Signup button */
        .signup-btn {
            background: #0066cc;
            color: white;
            border: 1px solid #0066cc;
        }
        
        .signup-btn:hover {
            background: #e65c50;
            border-color: #e65c50;
        }
        
        .header a.logo {
            font-size: 1.5rem;
            font-weight: 700;
            text-decoration: none;
            color: #333;
            display: flex;
            align-items: center;
            height: 100%;
        }
        .header a.logo span {
            color: #0066cc;
        }
        .header-buttons {
            display: flex;
            gap: 1rem;
            align-items: center;
            height: 100%;
        }
        .header-button {
            padding: 0.5rem 1.25rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 38px;
            box-sizing: border-box;
        }
        .header-button.login {
            color: #000;
            border: 1px solid #000;
            background: transparent;
        }
        .header-button.signup {
            background: #0066cc;
            color: white;
            border: 1px solid #0066cc;
        }
        .header-button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header-button:active {
            transform: translateY(0);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def show_hero():
    """Render the hero section."""
    # Create a container for the hero section
    hero_container = st.container()
    
    with hero_container:
        st.markdown("""
        <div class="hero">
            <h1>Transform Your Resume into a Professional Portfolio—In Seconds</h1>
            <p>Upload your resume and let our AI instantly craft a sleek, ATS-ready portfolio that makes recruiters take notice.</p>
        """, unsafe_allow_html=True)
        
        # Add the sign-in button with the original styling
        if st.button("Sign In →", key="hero_signin_btn", type="primary"):
            st.session_state.page = 'login'
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)

def show_features():
    """Render the features section with three cards."""
    st.markdown("""
    <section class="features">
        <h2 class="section-title">Portfolio AI combines three powerful modules to help you land your next job faster.</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <h3 class="feature-title">Portfolio Builder</h3>
                <p class="feature-description">Automatically convert your resume into a beautiful, responsive portfolio website that showcases your skills and experience in the best light.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <h3 class="feature-title">CV Generator</h3>
                <p class="feature-description">Create multiple versions of your resume tailored to different job descriptions with our AI-powered CV generator.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">✨</div>
                <h3 class="feature-title">Resume Optimizer</h3>
                <p class="feature-description">Get instant feedback and optimization suggestions to make your resume ATS-friendly and more likely to get noticed by recruiters.</p>
            </div>
        </div>
    </section>
    """, unsafe_allow_html=True)

def show_why_section():
    """Render the 'Why PortfolioAI?' section."""
    # Add custom CSS for the section
    st.markdown("""
    <style>
        .why-section {
            padding: 5rem 5%;
            background-color: #f8f9fa;
        }
        .why-container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .why-title {
            text-align: center;
            font-size: 2.5rem;
            color: #2c3e50;
            margin-bottom: 3rem;
            font-weight: 700;
        }
        .problem-card {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        .problem-text {
            font-size: 1.25rem;
            font-weight: 600;
            color: #000000;
            margin-bottom: 1rem;
            padding-left: 0;
        }
        .benefit-text {
            font-size: 1.1rem;
            color: #2c3e50;
            line-height: 1.7;
            margin: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Section container
    st.markdown("<div class='why-section'><div class='why-container'>", unsafe_allow_html=True)
    
    # Title
    st.markdown("<h2 class='why-title'>Why PortfolioAI?</h2>", unsafe_allow_html=True)
    
    # Problem-Benefit Pairs
    problem_benefits = [
        {
            'problem': "Crafting a Portfolio Takes Hours (or Days)",
            'benefit': "Save Time – Our AI builds a complete, polished portfolio in seconds, so you spend less time formatting and more time applying."
        },
        {
            'problem': "Recruiters' ATS Systems Reject Your Resume",
            'benefit': "Improve ATS Success – Get an instant ATS score and keyword suggestions so your resume sails past automated filters."
        },
        {
            'problem': "It's Hard to Know Which Template or Layout Works",
            'benefit': "Professional Design, Zero Guesswork – Choose from multiple responsive templates that highlight your strengths; no design skills needed."
        }
    ]
    
    for item in problem_benefits:
        with st.container():
            st.markdown(f"<div class='problem-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='problem-text'>Problem: {item['problem']}</div>", unsafe_allow_html=True)
            st.markdown(f"<p class='benefit-text'>{item['benefit']}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Close the container divs
    st.markdown("</div></div>", unsafe_allow_html=True)



def show_footer():
    """Render the footer."""
    st.markdown("""
    <footer style="background-color: #f8f9fa; padding: 4rem 2rem 2rem; margin-top: 4rem; border-top: 1px solid #e9ecef;">
        <div style="max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 2rem;">
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="font-size: 1.1rem; margin-bottom: 1rem; color: #333;">Contact us</h4>
                    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                        <a href="mailto:support@portfolio.ai" style="color: #4b5563; text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-envelope" style="width: 20px;"></i>
                            support@portfolio.ai
                        </a>
                        <p style="color: #4b5563; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-map-marker-alt" style="width: 20px;"></i>
                            100x Startup Lane, Tech City, 45678
                        </p>
                    </div>
                </div>
                <div style=" min-width: 200px;">
                    <h4 style="font-size: 1.1rem; margin-bottom: 1rem; color: #333;">Follow us</h4>
                    <div style="display: flex; gap: 1rem;">
                        <a href="https://twitter.com/portfolioai" target="_blank" style="color: #1da1f2; font-size: 1.5rem;">
                            <i class="fab fa-twitter"></i>
                        </a>
                        <a href="https://linkedin.com/company/portfolioai" target="_blank" style="color: #0a66c2; font-size: 1.5rem;">
                            <i class="fab fa-linkedin"></i>
                        </a>
                    </div>
                </div>
            </div>
            <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e9ecef; text-align: center; color: #6b7280; font-size: 0.9rem;">
                &copy; 2025 Portfolio AI. All rights reserved.
            </div>
        </div>
        <!-- Font Awesome for icons -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    </footer>
    """, unsafe_allow_html=True)

def show_signup_card():
    """Render the signup card section with a functional signup form."""
    from src.pages.Auth.auth import signup  # Import signup function from auth module
    
    # Add custom CSS for the form
    st.markdown("""
    <style>
        .signup-container {
            max-width: 480px;
            margin: 2rem auto;
            padding: 2.5rem;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
        }
        .signup-title {
            text-align: center;
            font-size: 1.75rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 2rem;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .stTextInput > div > div > input {
            border-radius: 8px;
            padding: 0.75rem 1rem;
            border: 1px solid #e2e8f0;
            font-size: 0.9375rem;
        }
        .stTextInput > label {
            font-weight: 500;
            color: #4a5568;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            background: #2563eb;
            border: none;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background: #1d4ed8;
            transform: translateY(-1px);
        }
        .signin-link {
            text-align: center;
            margin-top: 1.5rem;
            color: #4a5568;
            font-size: 0.9375rem;
        }
        .signin-link a {
            color: #2563eb;
            text-decoration: none;
            font-weight: 500;
            margin-left: 0.25rem;
        }
        .signin-link a:hover {
            text-decoration: underline;
        }
        .privacy-note {
            text-align: center;
            margin-top: 1.5rem;
            color: #718096;
            font-size: 0.8125rem;
            line-height: 1.5;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        
        st.markdown("<h1 class='signup-title'>Create Your Account</h1>", unsafe_allow_html=True)
        
        with st.form("signup_form"):
            # Name field
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="signup_first_name")
            with col2:
                last_name = st.text_input("Last Name", key="signup_last_name")
            
            # Email and password fields
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            # Submit button
            submit_button = st.form_submit_button("Create Account", type="primary")
            
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
                        st.session_state.page = "login"
                        st.rerun()
        
        # Create a container for the sign-in link and privacy note
        signin_container = st.container()
        with signin_container:
            # Split into columns to align the sign-in link with the text
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("""
                <p class="privacy-note">
                    We'll never share your information. Passwords are stored securely.
                </p>
                """, unsafe_allow_html=True)
            
            with col2:
                # Use a button that looks like a link for the sign-in action
                if st.button("Sign in", key="signin_link_btn", 
                           help="Click to sign in to your account"):
                    st.session_state.page = 'login'
                    st.rerun()
        
        # Add some CSS to make the button look like a link
        st.markdown("""
        <style>
            div[data-testid="stHorizontalBlock"] > div button[kind="secondary"] {
                background: transparent !important;
                color: #2563eb !important;
                border: none !important;
                padding: 0 !important;
                margin: 0 !important;
                font-size: 1rem !important;
                text-decoration: underline !important;
                box-shadow: none !important;
                min-width: auto !important;
                height: auto !important;
                line-height: 1.5 !important;
            }
            div[data-testid="stHorizontalBlock"] > div button[kind="secondary"]:hover {
                background: transparent !important;
                color: #1d4ed8 !important;
                text-decoration: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
        

def main():
    """Main function to render the landing page."""
    # Inject landing page CSS
    inject_landing_css()
    
    # Add landing page class to the app container
    st.markdown(
        """
        <script>
        document.querySelector('[data-testid="stAppViewContainer"]').classList.add('landing-page');
        </script>
        """,
        unsafe_allow_html=True
    )
    
    # Show the landing page components
    with st.container():
        show_header()
        show_hero()
        show_features()
        show_why_section()
        show_signup_card()
        show_footer()
        
    # Add any necessary JavaScript
    st.markdown(
        """
        <script>
        // Add any necessary JavaScript here
        </script>
        """,
        unsafe_allow_html=True
    )
    
    # Add JavaScript to handle smooth scrolling
    st.markdown(
        """
        <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
        </script>
        """,
        unsafe_allow_html=True
    )

# This module is meant to be imported by app.py
# All page configuration is handled in app.py
