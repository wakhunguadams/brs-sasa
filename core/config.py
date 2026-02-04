import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application settings
    APP_NAME: str = Field(default="BRS-SASA", description="Name of the application")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")

    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], description="Allowed origins for CORS")

    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///./brs_sasa.db", description="Database connection string")

    # LLM settings
    DEFAULT_LLM_PROVIDER: str = Field(default="gemini", description="Default LLM provider to use")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Google Gemini model to use")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")

    # Vector database settings
    VECTOR_DB_TYPE: str = Field(default="chroma", description="Type of vector database to use")
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_data", description="Directory for ChromaDB persistence")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                           description="Log message format")

    # Knowledge base settings
    KNOWLEDGE_BASE_PATH: str = Field(default="./knowledge_base", description="Path to knowledge base documents")

    # Model configuration
    MAX_TOKENS: int = Field(default=1000, description="Maximum tokens for LLM responses")
    TEMPERATURE: float = Field(default=0.7, description="Temperature for LLM responses")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate that required settings are present"""
    if settings.DEFAULT_LLM_PROVIDER == "gemini" and not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required when using Gemini as the default LLM provider")
    elif settings.DEFAULT_LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required when using OpenAI as the default LLM provider")
    elif settings.DEFAULT_LLM_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic as the default LLM provider")

# Validate settings on import
validate_settings()