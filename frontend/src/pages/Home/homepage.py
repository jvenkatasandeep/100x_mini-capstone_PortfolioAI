import streamlit as st
from typing import Optional, Dict, Any
import logging
from src.components.sections.header import show_header

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature card data
FEATURE_CARDS = [
    {
        "title": "CV Generator",
        "subtitle": "Create a professional CV from scratch",
        "icon": "📝",
        "page": "cv-generator",
        "enabled": True
    },
    {
        "title": "Resume Optimizer",
        "subtitle": "Improve your resume with AI-powered suggestions",
        "icon": "✨",
        "page": "resume-optimizer",
        "enabled": True
    },
    {
        "title": "Cover Letter Generator",
        "subtitle": "Create tailored cover letters",
        "icon": "✉️",
        "page": "cover-letter",
        "enabled": True
    },
    {
        "title": "Portfolio Generator",
        "subtitle": "Build your professional portfolio",
        "icon": "🎨",
        "page": "portfolio-generator",
        "enabled": True
    }
]

def show_home_page():
    """Display the home/dashboard page with feature cards."""
    # First, ensure we have the necessary session state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
        
    # Handle URL parameters if present
    query_params = st.query_params
    if 'page' in query_params:
        page = query_params['page']
        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()

    # ─ Main heading ─────────────────────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='text-align: center; margin-bottom: 2rem;'>Choose a Feature to Get Started</h2>",
        unsafe_allow_html=True
    )

    # ─ Feature cards in a 2-column grid ─────────────────────────────────────────────────
    cols = st.columns(2)  # two columns total

    for i, card in enumerate(FEATURE_CARDS):
        with cols[i % 2]:
            # Create a button with card styling
            button_clicked = st.button(
                f"{card['icon']}\n\n### {card['title']}\n{card['subtitle']}",
                key=f"card_{i}",
                use_container_width=True,
                type="secondary"
            )
            
            # Handle button click
            if button_clicked:
                if card["enabled"]:
                    st.session_state.page = card["page"]
                    st.rerun()
                else:
                    st.warning("This feature is coming soon!")
            
            # Card styling
            card_style = f"""
            <style>
                div[data-testid="stButton"] > button[kind="secondary"] {{
                    height: 200px;
                    text-align: center;
                    padding: 1.5rem;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    background: #FFFFFF;
                    color: #111111;
                    opacity: 0.7;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }}
                div[data-testid="stButton"] > button[kind="secondary"]:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    opacity: 1;
                }}
                div[data-testid="stButton"] > button[kind="secondary"] > div > p {{
                    margin: 0.5rem 0;
                    color: #666666;
                }}
                div[data-testid="stButton"] > button[kind="secondary"] > div > h3 {{
                    margin: 1rem 0 0.5rem 0;
                    color: #111111;
                }}
                {"" if card["enabled"] else """
                div[data-testid="stButton"] > button[kind="secondary"]:after {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.5);
                    z-index: 1;
                }
                """}
            </style>
            """
            st.markdown(card_style, unsafe_allow_html=True)
            
            # Add "Coming Soon" text for disabled features
            if not card["enabled"]:
                st.markdown(
                    "<p style='color: #ff6b6b; margin: -10px 0 15px 0; text-align: center; font-size: 0.9em;'>Coming Soon</p>",
                    unsafe_allow_html=True
                )

    # ─ Spacer at the bottom ──────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)

    # ─ Custom CSS for Upload/Logout buttons and card hover ─────────────
    st.markdown(
        """
    <style>
        /* Re-style Upload/Logout Streamlit buttons */
        .stButton > button {
            background-color: white !important;
            color: black !important;
            border: 2px solid black !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.5rem !important;
            transition: all 0.2s ease !important;
            margin: 0.25rem 0 !important;
        }
        .stButton > button:hover {
            background-color: #f0f0f0 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* Make the page more compact top/bottom */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Card hover: lift + shadow */
        a div:hover {
            transform: translateY(-4px) scale(1.02) !important;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
        }
    </style>
        """,
        unsafe_allow_html=True
    )