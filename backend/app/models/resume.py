"""
Resume Model for PortfolioAI

This module defines the SQLAlchemy model for storing resume information.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base

class Resume(Base):
    """
    SQLAlchemy model for storing resume information.
    
    Attributes:
        id: Unique identifier for the resume
        user_id: Foreign key to the user who uploaded the resume
        original_filename: Original name of the uploaded file
        stored_filename: Name of the file as stored on disk
        file_path: Full path to the stored file
        file_type: MIME type of the file
        file_size: Size of the file in bytes
        content: Extracted text content from the resume
        analysis: JSON field for storing AI analysis results
        uploaded_at: Timestamp when the resume was uploaded
        user: Relationship to the User model
    """
    __tablename__ = "resumes"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), unique=True, nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    analysis = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    
    def __repr__(self) -> str:
        return f"<Resume(id='{self.id}', filename='{self.original_filename}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the resume to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "content": self.content,
            "analysis": self.analysis,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
