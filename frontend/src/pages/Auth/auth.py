import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Debug: Print all environment variables
print("Current working directory:", os.getcwd())
print("Environment variables:", os.environ)
print("SUPABASE_URL exists:", "SUPABASE_URL" in os.environ)
print("SUPABASE_KEY exists:", "SUPABASE_KEY" in os.environ)

# Initialize Supabase client with auto-refresh token
def init_supabase() -> Client:
    try:
        print("\n=== Initializing Supabase Client ===")
        
        # Load environment variables
        load_dotenv(override=True)
        
        # Get environment variables with debugging
        supabase_url = os.getenv("SUPABASE_URL", "").strip('"\'').strip()
        supabase_key = os.getenv("SUPABASE_KEY", "").strip('"\'').strip()
        
        print(f"Supabase URL from .env: {'*' * 8}{supabase_url[-10:] if supabase_url else 'None'}")
        print(f"Supabase Key starts with: {supabase_key[:8] if supabase_key else 'None'}...")
        
        if not supabase_url:
            raise ValueError("❌ SUPABASE_URL is empty in .env file")
        if not supabase_key:
            raise ValueError("❌ SUPABASE_KEY is empty in .env file")
        
        # Clean and validate URL
        if not supabase_url.startswith(('http://', 'https://')):
            supabase_url = f'https://{supabase_url}'
        supabase_url = supabase_url.rstrip('/')
        
        print(f"✅ Using Supabase URL: {supabase_url}")
        
        try:
            # Initialize client with minimal options
            print("Attempting to create Supabase client...")
            client = create_client(supabase_url, supabase_key)
            print("✅ Supabase client created successfully")
            
            # Store the client in session state for reuse
            if hasattr(st, 'session_state'):
                st.session_state.supabase_client = client
            
            return client
            
        except Exception as client_error:
            print(f"❌ Error creating Supabase client: {str(client_error)}")
            if "Invalid API key" in str(client_error):
                print("\n⚠️  The API key appears to be invalid. Please verify:")
                print("1. You're using the 'anon' public key (not service role key)")
                print("2. The key hasn't been rotated or regenerated")
                print("3. The key is correctly copied without extra spaces")
            raise
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Fatal error initializing Supabase: {error_msg}")
        print("\nTroubleshooting steps:")
        print("1. Check your .env file has the correct values")
        print("2. Verify the Supabase project is active")
        print("3. Check your internet connection")
        print("4. Try regenerating your anon/public key in Supabase")
        raise ValueError(f"Failed to initialize Supabase: {error_msg}")

# Check if user is authenticated and session is valid
def is_authenticated() -> bool:
    try:
        # Check if user is in session and has required attributes
        if not hasattr(st.session_state, 'is_authenticated') or not st.session_state.is_authenticated:
            return False
            
        if not hasattr(st.session_state, 'user') or not st.session_state.user:
            return False
            
        # Verify the user has required fields
        user = st.session_state.user
        if not isinstance(user, dict) or not user.get('id') or not user.get('email'):
            return False
            
        return True
        
    except Exception as e:
        print(f"Authentication check failed: {e}")
        return False

# Login function with enhanced session handling
def login(email: str, password: str) -> bool:
    try:
        print(f"[DEBUG] Login attempt for email: {email}")
        
        if not email or not password:
            error_msg = "Please enter both email and password"
            print(f"[DEBUG] {error_msg}")
            st.error(error_msg)
            return False
            
        print("[DEBUG] Initializing Supabase client...")
        supabase = init_supabase()
        
        print("[DEBUG] Attempting to sign in with password...")
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            print(f"[DEBUG] Sign in response: {response is not None}")
            
            if response and hasattr(response, 'user') and response.user:
                print("[DEBUG] Authentication successful")
                # Store user data in session
                user_data = {
                    'id': response.user.id,
                    'email': response.user.email,
                    'user_metadata': getattr(response.user, 'user_metadata', {}) or {}
                }
                st.session_state.user = user_data
                st.session_state.is_authenticated = True
                # Store token in both locations for compatibility
                st.session_state.token = response.session.access_token if hasattr(response, 'session') and hasattr(response.session, 'access_token') else None
                st.session_state.jwt_token = st.session_state.token  # Ensure compatibility with API service
                
                print(f"[DEBUG] Session state after login: {st.session_state}")
                print(f"[DEBUG] is_authenticated: {st.session_state.is_authenticated}")
                print(f"User {email} logged in successfully")
                
                # Force a rerun to update the UI
                st.rerun()
                return True
            else:
                st.error("Invalid email or password")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            print(f"[DEBUG] Login error: {error_msg}")
            if "invalid login credentials" in error_msg:
                st.error("Invalid email or password")
            elif "email not confirmed" in error_msg:
                st.error("Please verify your email before logging in")
            else:
                st.error(f"Login failed: {str(e)}")
            return False
            
    except Exception as e:
        print(f"[DEBUG] Unexpected error during login: {str(e)}")
        st.error("An unexpected error occurred during login. Please try again.")
        return False

def ensure_users_table_exists(supabase):
    """Ensure the users table exists with the correct schema."""
    try:
        # First, try to create the table (will succeed if it doesn't exist)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.users (
            id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(email)
        );
        """
        
        # Try to create the table
        try:
            supabase.rpc('execute_sql', {'query': create_table_sql}).execute()
            print("[DEBUG] Created or verified users table")
            
            # Now try to enable RLS and create policies
            try:
                policy_sql = """
                DO $$
                BEGIN
                    -- Enable RLS if not already enabled
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_tables 
                        WHERE schemaname = 'public' 
                        AND tablename = 'users' 
                        AND rowsecurity = true
                    ) THEN
                        ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
                    END IF;
                    
                    -- Create policies if they don't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies 
                        WHERE tablename = 'users' 
                        AND policyname = 'Users can view their own data'
                    ) THEN
                        CREATE POLICY "Users can view their own data" 
                        ON public.users FOR SELECT 
                        USING (auth.uid() = id);
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies 
                        WHERE tablename = 'users' 
                        AND policyname = 'Users can insert their own data'
                    ) THEN
                        CREATE POLICY "Users can insert their own data"
                        ON public.users FOR INSERT
                        WITH CHECK (auth.uid() = id);
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies 
                        WHERE tablename = 'users' 
                        AND policyname = 'Users can update their own data'
                    ) THEN
                        CREATE POLICY "Users can update their own data"
                        ON public.users FOR UPDATE
                        USING (auth.uid() = id);
                    END IF;
                END $$;
                """
                supabase.rpc('execute_sql', {'query': policy_sql}).execute()
                print("[DEBUG] Created or verified RLS policies")
            except Exception as policy_error:
                print(f"[WARNING] Could not create RLS policies: {policy_error}")
                
            return True
            
        except Exception as create_error:
            print(f"[DEBUG] Error creating users table: {create_error}")
            # If table creation fails, it might already exist, try to insert anyway
            return True
            
    except Exception as e:
        print(f"[ERROR] Error in ensure_users_table_exists: {e}")
        # Continue anyway, the insert will fail if there's really a problem
        return True

# Signup function
def signup(email: str, password: str, full_name: str) -> bool:
    try:
        # Basic validation
        if not email or not password or not full_name:
            st.error("Email, password, and full name are required")
            return False
            
        # Clean up the full name
        full_name = full_name.strip()
            
        print(f"\n=== Attempting to sign up user: {email} ===")
        
        # Initialize Supabase client with debug info
        print("Initializing Supabase client...")
        supabase = init_supabase()
        if not supabase:
            st.error("Failed to initialize Supabase client")
            return False
            
        # Print client info (without exposing full key)
        if hasattr(supabase, 'supabase_url'):
            print(f"Supabase URL: {supabase.supabase_url}")
            
        # Ensure the users table exists
        if not ensure_users_table_exists(supabase):
            st.error("Failed to verify database schema. Please check the logs.")
            return False
        
        print("Attempting to sign up...")
        # Attempt to sign up
        try:
            auth_response = supabase.auth.sign_up({
                "email": email, 
                "password": password,
                "options": {
                    "email_redirect_to": "http://localhost:8501/"  # Redirect after email confirmation
                }
            })
            
            if not hasattr(auth_response, 'user') or not auth_response.user:
                error_msg = getattr(auth_response, 'error', 'Unknown error during signup')
                print(f"[ERROR] Signup failed: {error_msg}")
                st.error(f"Sign up failed: {error_msg}")
                return False
                
            # Get the user ID from the auth response
            user_id = auth_response.user.id
            print(f"[DEBUG] User authenticated with ID: {user_id}")
            
            # Prepare user data for insertion
            user_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "hashed_password": password,  # In production, hash this password
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            print(f"[DEBUG] Prepared user data for insertion: {user_data}")
            
            # Try to insert the user data using service role key for higher permissions
            try:
                # First, ensure we have the service role key
                service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                if not service_role_key:
                    raise Exception("Service role key not found in environment variables")
                
                print("[DEBUG] Creating service role client...")
                service_supabase = create_client(
                    supabase_url=os.getenv('SUPABASE_URL'),
                    supabase_key=service_role_key
                )
                
                # First try with service role key
                print("[DEBUG] Attempting to insert user data into 'users' table...")
                result = service_supabase.table('users').insert(user_data).execute()
                print(f"[DEBUG] Insert result: {result}")
                
                if hasattr(result, 'data') and result.data:
                    print("[SUCCESS] User data inserted successfully into 'users' table")
                    # Also update the auth.users table with the full name
                    try:
                        update_result = service_supabase.auth.admin.update_user_by_id(
                            user_id,
                            attributes={"user_metadata": {"full_name": full_name}}
                        )
                        print("[DEBUG] User metadata updated in auth.users")
                    except Exception as update_error:
                        print(f"[WARNING] Could not update user metadata: {str(update_error)}")
                    
                    st.success("Sign up successful! Please check your email to confirm your account.")
                    return True
                else:
                    error_msg = "No data returned from insert operation"
                    if hasattr(result, 'error'):
                        error_msg = f"{error_msg}: {result.error}"
                    print(f"[ERROR] {error_msg}")
                    st.error("Failed to save user profile. Please try again.")
                    return False
                    
            except Exception as insert_error:
                error_msg = str(insert_error)
                print(f"[ERROR] Error inserting user data: {error_msg}")
                # Try to provide more specific error messages
                if "duplicate key" in error_msg.lower():
                    st.error("This user already exists in the database.")
                elif "permission denied" in error_msg.lower():
                    st.error("Permission denied. Please check your database permissions.")
                else:
                    st.error("Failed to save user profile. Please try again.")
                return False
                
        except Exception as auth_error:
            error_msg = str(auth_error)
            print(f"[ERROR] Authentication error: {error_msg}")
            if "email already registered" in error_msg.lower():
                st.error("This email is already registered. Please try logging in instead.")
            elif "password" in error_msg.lower() and "weak" in error_msg.lower():
                st.error("Please choose a stronger password (at least 6 characters)")
            else:
                st.error(f"Sign up failed: {error_msg}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"[CRITICAL] Unexpected error in signup: {error_msg}")
        st.error("An unexpected error occurred during signup. Please try again later.")
        return False
        traceback.print_exc()
            
        # Even if database save fails, we still return True because auth was successful
        # The user can update their profile later
        st.success("Account created! Please check your email to confirm your account.")
        return True
                
    except Exception as e:
        error_msg = str(e)
        print(f"Signup error: {error_msg}")
        
        # More user-friendly error messages
        if "email already registered" in error_msg.lower():
            st.error("This email is already registered. Please try logging in instead.")
        elif "password" in error_msg.lower() and "weak" in error_msg.lower():
            st.error("Please choose a stronger password (at least 6 characters)")
        else:
            st.error(f"Sign up failed: {error_msg}")
        return False

# Logout function with session cleanup
def logout():
    """Log out the current user and clear session data."""
    try:
        # Clear all session state variables
        for key in list(st.session_state.keys()):
            del st.session_state[key]
            
        # Clear any cached data
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
            
        # Ensure JWT token is cleared
        if 'jwt_token' in st.session_state:
            del st.session_state['jwt_token']
            
        print("User logged out successfully")
        st.rerun()
        
    except Exception as e:
        print(f"Error during logout: {e}")

# Password reset function with email verification
def reset_password(email: str) -> bool:
    try:
        if not email:
            st.error("Please enter your email address")
            return False
            
        supabase = init_supabase()
        
        # Get the base URL for the reset link
        site_url = os.getenv('SITE_URL', 'http://localhost:8501')
        reset_url = f"{site_url}?token=TOKEN"  # TOKEN will be replaced by Supabase
        
        # Check if email exists in the system
        try:
            # This will throw an error if email doesn't exist
            supabase.auth.reset_password_email(email, {
                'redirect_to': f"{site_url}",
                'data': {
                    'reset_url': reset_url,
                    'email': email
                }
            })
            st.success("If an account exists with this email, you'll receive a password reset link.")
            return True
        except Exception as e:
            # Don't reveal if email exists for security
            print(f"Password reset error: {e}")
            st.success("If an account exists with this email, you'll receive a password reset link.")
            return True
            
    except Exception as e:
        print(f"Password reset failed: {e}")
        st.error("An error occurred while processing your request. Please try again later.")
        return False

# Update password with token
def update_password_with_token(token: str, new_password: str) -> bool:
    try:
        if not token or not new_password:
            st.error("Token and new password are required")
            return False
            
        if len(new_password) < 6:
            st.error("Password must be at least 6 characters long")
            return False
            
        supabase = init_supabase()
        
        # Update the password using the token
        response = supabase.auth.update_user({
            "password": new_password
        }, token=token)
        
        if hasattr(response, 'user') and response.user:
            st.success("Password updated successfully! You can now log in with your new password.")
            return True
            
        st.error("Failed to update password. The token may be invalid or expired.")
        return False
        
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid token" in error_msg or "expired" in error_msg:
            st.error("The password reset link is invalid or has expired. Please request a new one.")
        else:
            st.error(f"Failed to update password: {str(e)}")
        return False

# Verify password reset token
def verify_reset_token(token: str) -> bool:
    try:
        if not token:
            return False
            
        supabase = init_supabase()
        # This will raise an exception if the token is invalid
        user = supabase.auth.get_user(token)
        return user is not None
        
    except Exception:
        return False
def update_password(new_password: str, token: str = None) -> bool:
    try:
        if not new_password:
            st.error("Please enter a new password")
            return False
            
        supabase = init_supabase()
        
        if token:
            # If token is provided, use it to update password
            supabase.auth.api.update_user(token, {'password': new_password})
        elif is_authenticated():
            # If user is logged in, update password directly
            supabase.auth.update_user({'password': new_password})
        else:
            st.error("No valid session or token found")
            return False
            
        st.success("Password updated successfully!")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if "token" in error_msg and "expired" in error_msg:
            st.error("The password reset link has expired. Please request a new one.")
        else:
            st.error(f"Failed to update password: {str(e)}")
        return False
