"""Centralized configuration management."""
import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file once at module import
try:
    from dotenv import load_dotenv
    
    # Determine project root (3 levels up from this file: app/config.py -> app/ -> project_root/)
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Also try loading from current directory (for flexibility)
        load_dotenv()
except ImportError:
    # python-dotenv not installed, rely on system env vars
    pass


class Config:
    """Centralized configuration class."""
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # LangSmith (for tracing and monitoring)
    LANGCHAIN_TRACING: str = os.getenv("LANGCHAIN_TRACING", "false")
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: Optional[str] = os.getenv("LANGCHAIN_PROJECT", "ai_data_analyst")
    LANGCHAIN_ENDPOINT: Optional[str] = os.getenv("LANGCHAIN_ENDPOINT")
    
    # Server
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        missing = []
        
        if not cls.DATABASE_URL:
            missing.append("DATABASE_URL")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please set them in your .env file or environment."
            )


# Global config instance
config = Config()

