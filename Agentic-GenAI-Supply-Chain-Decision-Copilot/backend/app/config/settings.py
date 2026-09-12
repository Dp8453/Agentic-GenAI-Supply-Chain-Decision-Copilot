from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os


class Settings(BaseSettings):
    APP_NAME: str = "SupplyChain AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    REQUEST_TIMEOUT_SECONDS: int = 45

    # Database Settings
    POSTGRES_USER: str = "supplychain_user"
    POSTGRES_PASSWORD: str = "supplychain_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "supplychain_db"
    DATABASE_URL: Optional[str] = None

    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3:latest"
    LLM_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Embeddings Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Phase 10 Security Guardrails Configuration
    MAX_INPUT_LENGTH: int = 2000
    MAX_OUTPUT_LENGTH: int = 4000
    MAX_TOOL_CALLS: int = 5
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Phase 12 Production CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_cors_origins(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
