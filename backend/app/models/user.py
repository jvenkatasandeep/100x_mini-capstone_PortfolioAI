"""
User model for PortfolioAI.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class UserRole(str, Enum):
    """User roles for authorization."""
    USER = "user"
    ADMIN = "admin"

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    role: UserRole = Field(default=UserRole.USER, description="User's role for authorization")

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")

class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    password: Optional[str] = Field(None, min_length=8, description="New password (min 8 characters)")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")

class UserInDBBase(UserBase):
    """Base model for user stored in database."""
    id: str = Field(..., description="Unique identifier for the user")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the user was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the user was last updated")

    class Config:
        from_attributes = True

class User(UserInDBBase):
    """User model for API responses."""
    pass

class UserInDB(UserInDBBase):
    """User model for internal use with password hash."""
    hashed_password: str = Field(..., description="Hashed password")

class Token(BaseModel):
    """Authentication token model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")

class TokenData(BaseModel):
    """Data stored in the authentication token."""
    email: Optional[str] = Field(None, description="User's email from token")
    user_id: Optional[str] = Field(None, description="User ID from token")
