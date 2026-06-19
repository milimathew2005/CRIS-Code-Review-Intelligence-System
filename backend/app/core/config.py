from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
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
    CORS_ORIGINS: list[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    
    # FastAPI Host Configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # PostgreSQL Configuration
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "cris_db"
    
    DATABASE_URL: Optional[str] = None
    
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
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Instantiated single settings object for application-wide imports
settings = Settings()
