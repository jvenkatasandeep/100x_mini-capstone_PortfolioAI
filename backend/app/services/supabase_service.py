"""Supabase service for PortfolioAI."""
from typing import Any, Dict, List, Optional, Union
from supabase import Client as SupabaseClient
from db.config import get_supabase

class SupabaseService:
    """Service class for Supabase operations."""
    
    def __init__(self, supabase: Optional[SupabaseClient] = None):
        """Initialize Supabase service.
        
        Args:
            supabase: Optional Supabase client. If not provided, a new one will be created.
        """
        self.supabase = supabase or get_supabase()
    
    # User Management
    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dict containing user data and session
        """
        return self.supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dict containing user data and session
        """
        return self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    
    def sign_out(self) -> None:
        """Sign out the current user."""
        return self.supabase.auth.sign_out()
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently authenticated user.
        
        Returns:
            User data if authenticated, None otherwise
        """
        try:
            return self.supabase.auth.get_user()
        except Exception:
            return None
    
    # Database Operations
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into a table.
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Inserted record
        """
        return self.supabase.table(table).insert(data).execute()
    
    def select(self, table: str, columns: str = "*", **filters) -> List[Dict[str, Any]]:
        """Select records from a table.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            **filters: Filter conditions
            
        Returns:
            List of matching records
        """
        query = self.supabase.table(table).select(columns)
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute().data
    
    def update(self, table: str, data: Dict[str, Any], **filters) -> List[Dict[str, Any]]:
        """Update records in a table.
        
        Args:
            table: Table name
            data: Data to update
            **filters: Filter conditions
            
        Returns:
            Updated records
        """
        query = self.supabase.table(table).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute().data
    
    def delete(self, table: str, **filters) -> List[Dict[str, Any]]:
        """Delete records from a table.
        
        Args:
            table: Table name
            **filters: Filter conditions
            
        Returns:
            Deleted records
        """
        query = self.supabase.table(table).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute().data
    
    # File Storage
    def upload_file(self, bucket: str, path: str, file: bytes, content_type: str = "text/plain") -> Dict[str, Any]:
        """Upload a file to Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            path: Path to store the file
            file: File content as bytes
            content_type: MIME type of the file
            
        Returns:
            Upload response
        """
        return self.supabase.storage.from_(bucket).upload(path, file, {"content-type": content_type})
    
    def download_file(self, bucket: str, path: str) -> bytes:
        """Download a file from Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            path: Path to the file
            
        Returns:
            File content as bytes
        """
        return self.supabase.storage.from_(bucket).download(path)
    
    def get_public_url(self, bucket: str, path: str) -> str:
        """Get a public URL for a file in Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            path: Path to the file
            
        Returns:
            Public URL of the file
        """
        return self.supabase.storage.from_(bucket).get_public_url(path)

# Create a singleton instance
supabase_service = SupabaseService()
