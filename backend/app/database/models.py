"""Database models for PortfolioAI."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .local_config import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    api_key = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="owner")
    cvs = relationship("CV", back_populates="owner")
    cover_letters = relationship("CoverLetter", back_populates="owner")
    api_calls = relationship("APICall", back_populates="user")
    resume_optimizations = relationship("ResumeOptimization", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    template = Column(String, default="default")
    content = Column(JSON)
    is_public = Column(Boolean, default=False)
    subdomain = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="portfolios")

class CV(Base):
    __tablename__ = "cvs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    file_path = Column(String)
    file_type = Column(String)  # pdf, docx, etc.
    content = Column(JSON)  # Store structured CV data
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="cvs")

class APICall(Base):
    __tablename__ = "api_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Define relationship with User
    user = relationship("User", back_populates="api_calls")


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    file_path = Column(String)
    file_type = Column(String, default="txt")  # txt, docx, pdf
    content = Column(JSON)  # Store structured content
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="cover_letters")


class ResumeOptimization(Base):
    __tablename__ = "resume_optimizations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_text = Column(Text, nullable=False)
    optimized_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    score = Column(Float)  # 0.0-1.0 score of how well the resume matches the job
    suggestions = Column(JSON)  # List of suggested improvements
    keywords_matched = Column(JSON)  # List of keywords that were matched
    missing_keywords = Column(JSON)  # List of important keywords that are missing
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Define relationship with User
    user = relationship("User", back_populates="resume_optimizations")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), unique=True, nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    
    def __repr__(self) -> str:
        return f"<Resume(id='{self.id}', filename='{self.original_filename}')>"
