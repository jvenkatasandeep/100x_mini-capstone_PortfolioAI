"""
Frontend configuration settings for PortfolioAI.

This module provides a centralized configuration management system for the PortfolioAI frontend.
It uses environment variables with sensible defaults and includes validation through Pydantic.
"""
import os
from typing import List, Optional, Union, Dict, Any
from pydantic import AnyHttpUrl, validator, BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "PortfolioAI"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # API
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")
    API_V1_STR: str = "/api/v1"
    
    # Authentication
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "True").lower() in ("true", "1", "t")
    TOKEN_URL: str = f"{API_URL}/auth/token"
    REFRESH_TOKEN_URL: str = f"{API_URL}/auth/refresh"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Session
    SESSION_COOKIE_NAME: str = "portfolioai_session"
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "your-secret-key-here")
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 7  # 1 week
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Sentry
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # Feature Flags
    FEATURE_ANALYTICS: bool = os.getenv("FEATURE_ANALYTICS", "False").lower() in ("true", "1", "t")
    FEATURE_DARK_MODE: bool = os.getenv("FEATURE_DARK_MODE", "True").lower() in ("true", "1", "t")
    
    # UI/UX
    DEFAULT_THEME: str = os.getenv("DEFAULT_THEME", "light")
    ITEMS_PER_PAGE: int = int(os.getenv("ITEMS_PER_PAGE", "10"))
    
    # Performance
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))  # seconds
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            # This changes the order so env vars take precedence over .env file
            return env_settings, init_settings, file_secret_settings

# Create settings instance
settings = Settings()
