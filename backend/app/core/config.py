"""
Core configuration for NCERT AI Teacher Assistant backend.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "NCERT AI Teacher Assistant"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # LLM Configuration
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field(default="google", alias="DEFAULT_LLM_PROVIDER")
    default_model: str = Field(default="gemini-1.5-pro", alias="DEFAULT_MODEL")
    
    # Vector Database
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    indexing_api_key: str = Field(default="", alias="INDEXING_API_KEY")
    collection_name: str = Field(default="ncert_curriculum", alias="COLLECTION_NAME")
    
    # Document Processing
    max_chunk_size: int = Field(default=1000, alias="MAX_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    embedding_model: str = Field(default="models/embedding-001", alias="EMBEDDING_MODEL")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Security
    secret_key: str = Field(default="your_secret_key_here_change_in_production", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOWED_ORIGINS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()