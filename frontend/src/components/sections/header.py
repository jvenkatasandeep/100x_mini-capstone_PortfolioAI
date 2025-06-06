import streamlit as st
from src.pages.Auth.auth import logout

def show_header():
    """
    Displays the header with PortfolioAI logo and logout button.
    Should be called at the top of every page.
    """
    # Add custom CSS
    st.markdown("""
    <style>
    .logo-button {
        margin: 0;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-weight: 600;
        color: white !important;
        background: linear-gradient(90deg, #0066cc, #00ccff) !important;
        border: none;
        border-radius: 0.5rem;
        cursor: pointer;
        max-width: 200px;
        transition: all 0.3s ease;
        text-align: center;
        text-decoration: none;
        display: inline-block;
    }
    .logo-button:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a container for the header
    header = st.container()
    
    # Create two columns for the header layout
    col1, col2 = st.columns([9, 1])
    
    with header:
        with col1:
            # PortfolioAI button with matching style to logout button
            if st.button(
                "PortfolioAI",
                key="header_logo_button",
                use_container_width=False,
                type="primary"
            ):
                st.session_state.page = 'home'
                st.rerun()
                
            # Apply custom styling to match the logout button
            st.markdown(
                """
                <script>
                // Apply custom styling to the logo button
                const logoButton = document.querySelector('button[data-testid="baseButton-header_logo_button"]');
                if (logoButton) {
                    logoButton.classList.add('logo-button');
                    // Remove the fixed 100% width so the CSS max-width takes effect
                    logoButton.style.maxWidth = '200px';
                    logoButton.style.justifyContent = 'center';
                }
                </script>
                """,
                unsafe_allow_html=True
            )
            
        with col2:
            # Add some vertical space to align with the logo
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
            
            # Logout button with unique key
            if st.button("Logout", use_container_width=True, type="primary", key="header_logout_button"):
                logout()  # Use the centralized logout function from auth.py
    
    # Add a divider below the header
    st.markdown("---")
    return header
