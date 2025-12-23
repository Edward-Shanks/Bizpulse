"""
Application configuration
Loads environment variables and provides configuration settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from typing import List

ROOT_DIR = Path(__file__).parent.parent.parent

# Load environment variables
_dotenv_path = find_dotenv(str(ROOT_DIR / '.env')) or find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)

class Settings:
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    MONGO_URL: str = os.getenv('MONGO_URL', '')
    DB_NAME: str = os.getenv('DB_NAME', 'bizpulse')
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'thrive-brands-biz-pulse-secret-2024')
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Azure Blob Storage Configuration
    AZURE_CONNECTION_STRING: str = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
    AZURE_CONTAINER_NAME: str = os.getenv('AZURE_CONTAINER_NAME', '')
    AZURE_BLOB_PATH: str = os.getenv('AZURE_BLOB_PATH', '')
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    
    # LLM Configuration
    PERPLEXITY_API_KEY: str = os.getenv('PERPLEXITY_API_KEY', '')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    
    # Ollama Configuration (for local LLM)
    OLLAMA_BASE_URL: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11436')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'qwen2.5:32b-instruct')
    OLLAMA_FALLBACK_MODEL: str = os.getenv('OLLAMA_FALLBACK_MODEL', 'llama3:70b')
    OLLAMA_TIMEOUT: int = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'ollama')
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == 'development'
    
    def validate(self):
        """Validate required configuration"""
        if not self.MONGO_URL:
            raise ValueError("MONGO_URL environment variable is required")
        if not self.DB_NAME:
            raise ValueError("DB_NAME environment variable is required")

# Create global settings instance
settings = Settings()
settings.validate()

