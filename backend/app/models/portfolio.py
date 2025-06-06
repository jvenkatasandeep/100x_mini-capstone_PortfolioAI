"""
Pydantic models for the Portfolio API.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class ContentEnhancementRequest(BaseModel):
    """Request model for content enhancement."""
    section: str = Field(..., description="The section being enhanced (e.g., 'about', 'experience')")
    resume_data: Dict[str, Any] = Field(..., description="The parsed resume data")
    existing_content: str = Field(default="", description="Existing content to enhance")

class SectionSuggestionRequest(BaseModel):
    """Request model for section suggestions."""
    resume_data: Dict[str, Any] = Field(..., description="The parsed resume data")

class PortfolioRequest(BaseModel):
    """Request model for portfolio generation."""
    resume_id: Optional[str] = Field(None, description="ID of the resume to use")
    template: str = Field("default", description="Template to use for the portfolio")
    color_theme: str = Field("blue", description="Color theme for the portfolio")
    sections: List[str] = Field(default_factory=list, description="List of sections to include")
    use_ai_enhancement: bool = Field(True, description="Whether to use AI enhancement")
    personal_info: Dict[str, str] = Field(default_factory=dict, description="Personal information")

class PortfolioResponse(BaseModel):
    """Response model for portfolio generation."""
    status: str = Field(..., description="Status of the request (success/error)")
    html_content: Optional[str] = Field(None, description="Generated HTML content")
    message: Optional[str] = Field(None, description="Status message")

class EnhancedContentResponse(BaseModel):
    """Response model for enhanced content."""
    status: str = Field(..., description="Status of the request (success/error)")
    content: Optional[str] = Field(None, description="Enhanced content")
    section: Optional[str] = Field(None, description="Section that was enhanced")
    message: Optional[str] = Field(None, description="Status message")

class SectionSuggestionResponse(BaseModel):
    """Response model for section suggestions."""
    status: str = Field(..., description="Status of the request (success/error)")
    suggested_sections: List[str] = Field(default_factory=list, description="List of suggested sections")
    message: Optional[str] = Field(None, description="Status message")
