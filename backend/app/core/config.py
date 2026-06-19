from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Look for a .env file in the current working directory
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # General Environment
    APP_ENV: str = "development"
    SECRET_KEY: str = "temporary-secret-key-for-development"
    
    # FastAPI Host Configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # PostgreSQL Configuration
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "cris_db"
    
    # Gemini API Credentials
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # GitHub Webhook Configuration
    GITHUB_WEBHOOK_SECRET: str = "temporary-dev-webhook-secret"
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None

    @property
    def database_url(self) -> str:
        """
        Generates the SQLAlchemy-compatible database connection string.
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Instantiated single settings object for application-wide imports
settings = Settings()
