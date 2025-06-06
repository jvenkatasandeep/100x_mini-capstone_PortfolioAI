import streamlit as st
from src.pages.Auth.auth import update_password_with_token, verify_reset_token

def show_reset_password_page():
    """Display the password reset form with token verification."""
    st.title("Reset Your Password")
    
    # Get token from URL parameters
    token = st.query_params.get("token", "")
    
    if not token:
        st.warning("No reset token found. Please use the reset link sent to your email.")
        return
    
    # Verify the token
    if not verify_reset_token(token):
        st.error("Invalid or expired reset link. Please request a new password reset.")
        return
    
    # Show the password reset form
    with st.form("reset_password_form"):
        st.write("### Create a new password")
        new_password = st.text_input("New Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password")
        submit_button = st.form_submit_button("Update Password")
        
        if submit_button:
            if not new_password or not confirm_password:
                st.error("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                if update_password_with_token(token, new_password):
                    st.success("Your password has been updated successfully!")
                    st.experimental_set_query_params()  # Clear the token from URL
                    # Redirect to login after a short delay
                    st.experimental_rerun()
